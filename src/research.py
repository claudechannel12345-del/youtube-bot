import json
import os
import re

from llm import llm_generate

CHANNEL_NICHE = (
    "fascinating science, psychology, history, and human behavior - "
    "surprising facts and stories that make people say 'I had no idea'"
)

TOPIC_HISTORY_PATH = os.path.join("data", "topic_history.json")


def _load_recent_topics():
    if not os.path.exists(TOPIC_HISTORY_PATH):
        return []
    try:
        with open(TOPIC_HISTORY_PATH, "r", encoding="utf-8") as f:
            history = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(history, list):
        return []
    return [topic for topic in history if isinstance(topic, str)]


def pick_topic(client):
    recent_topics = _load_recent_topics()
    recent_topics_json = json.dumps(recent_topics[-50:], ensure_ascii=True)

    prompt = f"""You are the content strategist for a popular educational YouTube channel.
The channel covers: {CHANNEL_NICHE}

Recent topics to avoid repeating or closely resembling:
{recent_topics_json}

Brainstorm 6 candidate topics, then select ONE specific, fascinating topic for today's 8-10 minute video.

Requirements:
- Genuinely surprising or counterintuitive to most people
- Evergreen (not breaking news, sports, or celebrity gossip)
- Visually illustratable with motion graphics, data, diagrams, maps, or timelines.
- Broad adult audience appeal - the kind of thing people share with friends
- Materially different from the recent topics above
- Not a generic, well-worn faceless-channel topic
- Built around a non-obvious angle: the thing most videos on this topic get wrong or never mention

Great topic examples:
- "The Soviet experiment to hybridize humans and apes"
- "Why your brain is constantly hallucinating your reality"
- "The real reason humans are the only animals that cry"
- "How ancient Romans used urine as toothpaste - and it worked"
- "The psychology trick casinos use to make you lose track of time"
- "Why some people can taste words and see sounds"
- "The island where people naturally live to 100"
- "How the CIA secretly dosed thousands of people with LSD"

Selection process:
1. Privately brainstorm 6 candidates.
2. Compare them against the recent topics and reject anything similar.
3. Select the single most original, specific candidate.
4. Make the angle concrete and non-obvious.

Return ONLY valid JSON, no markdown fences:
{{
    "topic": "specific topic",
    "angle": "the non-obvious thing most videos get wrong or never mention",
    "why_original": "why this is materially different from common videos and recent topics",
    "visual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
    "key_facts": ["concrete checkable fact 1", "concrete checkable fact 2", "concrete checkable fact 3"]
}}"""

    text = llm_generate(prompt, tier="cheap", json_mode=True)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in research response: {text[:300]}")
    return json.loads(match.group())
