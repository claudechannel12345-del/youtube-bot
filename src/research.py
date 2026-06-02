import json
import re

CHANNEL_NICHE = (
    "fascinating science, psychology, history, and human behavior — "
    "surprising facts and stories that make people say 'I had no idea'"
)


def pick_topic(client):
    prompt = f"""You are the content strategist for a popular educational YouTube channel.
The channel covers: {CHANNEL_NICHE}

Choose ONE specific, fascinating topic for today's 8-10 minute video.

Requirements:
- Genuinely surprising or counterintuitive to most people
- Evergreen (not breaking news, sports, or celebrity gossip)
- Visually illustratable with stock photography
- Broad adult audience appeal — the kind of thing people share with friends

Great topic examples:
- "The Soviet experiment to hybridize humans and apes"
- "Why your brain is constantly hallucinating your reality"
- "The real reason humans are the only animals that cry"
- "How ancient Romans used urine as toothpaste — and it worked"
- "The psychology trick casinos use to make you lose track of time"
- "Why some people can taste words and see sounds"
- "The island where people naturally live to 100"
- "How the CIA secretly dosed thousands of people with LSD"

Return ONLY valid JSON, no markdown fences:
{{
    "topic": "specific topic",
    "angle": "the surprising hook that makes this video unmissable",
    "visual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
}}"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    match = re.search(r"\{.*\}", response.text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in research response: {response.text[:300]}")
    return json.loads(match.group())
