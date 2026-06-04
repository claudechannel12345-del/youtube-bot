import json
import re

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
            "broll_keywords": ["keyword"]
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

    if normalized:
        return normalized

    narration = str(section.get("narration") or "").strip()
    fallback = [s.strip() for s in re.split(SENTENCE_SPLIT_RE, narration) if s.strip()]
    if not fallback and narration:
        fallback = [narration]
    return [{"text": text, "delivery": "neutral"} for text in fallback]
