import json
import re

from cutaway_vocab import coerce_beat_type
from gemini_utils import generate

VALID_TEMPLATES = {
    "title_card",
    "stat_reveal",
    "comparison",
    "timeline",
    "process",
    "quote",
    "list",
    "map",
    "diagram",
    "image_focus",
}

VALID_DELIVERY = {
    "neutral", "curious", "question", "brisk",
    "weighty", "surprised", "skeptical", "ominous", "warm_cta",
}

SENTENCE_SPLIT_RE = r"(?<=[.!?])\s+"


def generate_script(topic_data, client):
    prompt = f"""You are a retention-focused scriptwriter for a popular educational YouTube channel.

Topic: {topic_data["topic"]}
Angle: {topic_data["angle"]}
Why original: {topic_data.get("why_original", "")}
Visual keywords: {json.dumps(topic_data.get("visual_keywords", []), ensure_ascii=True)}
Key facts to use/check: {json.dumps(topic_data.get("key_facts", []), ensure_ascii=True)}

Write a complete 8-10 minute documentary-style educational script structured like a real YouTube video.
The narration must be written for speech: contractions, short sentences, vivid phrasing, and ellipses for breath.

Return ONLY valid JSON, no markdown fences:

{{
    "title": "primary title (<=70 chars, curiosity gap, specific, no all-caps words)",
    "title_options": ["alt title 1", "alt title 2"],
    "hook_options": ["spoken hook v1", "spoken hook v2"],
    "thumbnail_text_options": ["3-5 WORD TEXT A", "3-5 WORD TEXT B", "3-5 WORD TEXT C"],
    "description": "3 paragraphs; first sentence = strong hook; ends with a subscribe line",
    "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"],
    "sections": [
        {{
            "narration": "What the narrator says. Written for the ear. 50-90 words.",
            "sentences": [
                {{"text": "What the narrator says.", "delivery": "curious"}}
            ],
            "key_phrase": "ON-SCREEN HEADLINE",
            "template": "title_card",
            "on_screen": {{"subtitle": "short subtitle"}},
            "broll_keywords": ["keyword"],
            "beats": [
                {{
                    "id": "s0_visual_id",
                    "type": "establish",
                    "sentence_start": 0,
                    "sentence_end": 0,
                    "visual_intent": "Concrete visual direction tied to the sentence.",
                    "text": "SHORT LABEL",
                    "subjects": ["subject"],
                    "importance": "high"
                }}
            ]
        }}
    ]
}}

Template vocabulary and required on_screen fields:
- title_card: {{"subtitle": "..."}}
- stat_reveal: {{"stat": "70%", "label": "short label"}}
- comparison: {{"left": "...", "right": "...", "left_label": "...", "right_label": "..."}}
- timeline: {{"events": ["1969: ...", "1972: ..."]}}
- process: {{"steps": ["...", "..."]}}
- quote: {{"quote": "...", "attribution": "..."}}
- list: {{"items": ["...", "..."]}}
- map: {{"place": "Region/Country"}}
- diagram: {{"parts": ["label1", "label2"]}}
- image_focus: {{"overlay_text": "short phrase"}}

Script structure requirements:
- Use 10-16 sections, driven by the story rather than a fixed count.
- The FIRST section is the cold-open hook. Open on the single most surprising moment or fact, with no slow build. Its narration must exactly match one of hook_options.
- Then move through: stakes/context -> escalating reveals -> climax/big reveal -> payoff/meaning -> CTA close.
- Do not repeat the same template back-to-back. Pick the template that actually fits each beat.
- Every section must include narration, key_phrase, template, on_screen, and broll_keywords.
- Split each section's narration into sentences. For each sentence add a `delivery` tag from this exact set: neutral, curious, question, brisk, weighty, surprised, skeptical, ominous, warm_cta.
- The concatenation of sentences[].text, joined with a single space, MUST equal narration exactly.
- Delivery guidance: rhetorical/real questions -> question; the key reveal / most important line -> weighty; fast connective transitions -> brisk; a genuine twist -> surprised; testing an assumption -> skeptical; tense foreboding setup -> ominous; the closing CTA line -> warm_cta; default neutral. Use weighty/ominous sparingly (1-2 per section max) so they keep impact.
- Every section must include a `beats` array tied to sentence indexes. Beat timing is not in seconds yet.
- Beat `type` is closed vocabulary from this exact set: establish, illustrate, stat_pop, compare, diagram_build, map_focus, list_reveal, cutaway_gag, emphasize, transition.
- Each beat must include id, type, sentence_start, and sentence_end. sentence_start and sentence_end are zero-based indexes into sentences[] and may cover a sentence range.
- Optional beat fields: visual_intent, text, subjects, importance, comedy_role.
- Beat importance, when present, must be one of: low, medium, high, must_hit.
- Beat comedy_role, when present on cutaway_gag, must be one of: deadpan_literalization, scale_absurdity, bureaucracy_metaphor, wrong_tool, overly_literal_label, quiet_contradiction.
- Do not make cutaway_gag mandatory. Use it only when the line earns it, and never more than one cutaway_gag in a section.
- key_phrase must be 2-5 words, punchy, and suitable as an on-screen headline.
- Narration must not be list-like fragments.
- The final section must end with a natural subscribe CTA using wording like "new deep-dives every week"; do not mention daily posting.
- The description must have 3 paragraphs. Its first sentence must be a strong hook. It must end with a subscribe line.
- tags must contain exactly 10 tags.
- title_options must contain exactly 2 alternates.
- hook_options must contain exactly 2 spoken hooks.
- thumbnail_text_options must contain exactly 3 options, each 3-5 words."""

    response = generate(client, prompt)
    text = response.text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in script response: {text[:300]}")

    script = json.loads(match.group())
    if not script.get("title"):
        raise ValueError("Script has empty title")
    if "sections" not in script or len(script["sections"]) < 8:
        raise ValueError(f"Script has too few sections: {len(script.get('sections', []))}")

    for section in script["sections"]:
        if not section.get("narration"):
            raise ValueError("Script section missing narration")
        if not section.get("key_phrase"):
            raise ValueError("Script section missing key_phrase")
        if section.get("template") not in VALID_TEMPLATES:
            section["template"] = "title_card"
        section["sentences"] = _normalize_sentences(section)
        section["beats"] = _normalize_beats(section)

    return script


def _normalize_sentences(section):
    sentences = section.get("sentences")
    normalized = []
    if isinstance(sentences, list):
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            text = str(sentence.get("text") or "").strip()
            if not text:
                continue
            delivery = sentence.get("delivery")
            if delivery not in VALID_DELIVERY:
                delivery = "neutral"
            normalized.append({"text": text, "delivery": delivery})

    narration = str(section.get("narration") or "").strip()
    if normalized and _sentence_join(normalized) == narration:
        return normalized

    fallback = [s.strip() for s in re.split(SENTENCE_SPLIT_RE, narration) if s.strip()]
    if not fallback and narration:
        fallback = [narration]
    return [{"text": text, "delivery": "neutral"} for text in fallback]


def _normalize_beats(section):
    sentences = section.get("sentences") or []
    sentence_count = len(sentences)
    beats = section.get("beats")
    if not isinstance(beats, list):
        beats = []

    normalized = []
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue
        normalized_beat = dict(beat)
        beat_type = coerce_beat_type(normalized_beat.get("type"))
        start = _coerce_sentence_index(normalized_beat.get("sentence_start"), sentence_count)
        end = _coerce_sentence_index(normalized_beat.get("sentence_end"), sentence_count)
        if start > end:
            start, end = end, start

        normalized_beat["id"] = str(normalized_beat.get("id") or f"s{start}_{beat_type}_{index}")
        normalized_beat["type"] = beat_type
        normalized_beat["sentence_start"] = start
        normalized_beat["sentence_end"] = end
        if beat_type == "cutaway_gag" and not normalized_beat.get("comedy_role"):
            normalized_beat["comedy_role"] = "deadpan_literalization"
        normalized.append(normalized_beat)

    if normalized:
        return normalized

    return _fallback_beats(sentences)


def _fallback_beats(sentences):
    beats = []
    last_index = len(sentences) - 1
    for index, sentence in enumerate(sentences):
        text = str(sentence.get("text") or "")
        beat_type = _fallback_beat_type(text, index, last_index)
        beats.append(
            {
                "id": f"s{index}_{beat_type}",
                "type": beat_type,
                "sentence_start": index,
                "sentence_end": index,
            }
        )
    return beats


def _fallback_beat_type(text, index, last_index):
    if index == 0:
        return "establish"
    if _looks_stat_like(text):
        return "stat_pop"
    if re.search(r"\b(but|instead|versus)\b", text, re.IGNORECASE):
        return "compare"
    if index == last_index:
        return "emphasize"
    return "illustrate"


def _looks_stat_like(text):
    return bool(
        re.search(
            r"\d|%|\b(percent|million|billion|trillion|thousand|half|third|quarter|times|x)\b",
            text,
            re.IGNORECASE,
        )
    )


def _coerce_sentence_index(value, sentence_count):
    if sentence_count <= 0:
        return 0
    try:
        index = int(value)
    except (TypeError, ValueError):
        index = 0
    return max(0, min(index, sentence_count - 1))


def _sentence_join(sentences):
    return " ".join(sentence["text"] for sentence in sentences)
