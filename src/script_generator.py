import json
import re


def generate_script(topic_data, client):
    prompt = f"""You are a scriptwriter for a popular educational YouTube channel.

Topic: {topic_data["topic"]}
Hook: {topic_data["angle"]}

Write a complete 8-10 minute documentary-style educational script.
Return ONLY valid JSON, no markdown fences:

{{
    "title": "YouTube title (under 70 chars, curiosity-driven, no ALL CAPS words)",
    "description": "3-paragraph YouTube description. First sentence is a powerful hook. Paragraphs 2-3 deliver value and keywords naturally. End with: Subscribe for a new fascinating video every single day!",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
    "sections": [
        {{
            "narration": "Exactly what the narrator says. 80-100 words. Conversational, vivid, engaging.",
            "visual": "Simple 1-3 word Pexels search term for stock photo (e.g. human brain, ancient ruins, deep ocean)"
        }}
    ]
}}

Script requirements:
- Exactly 20-22 sections
- Section 1: Start mid-story or with a jaw-dropping fact — no "today we're going to talk about"
- Sections 2-4: Establish context and stakes — make the viewer invested
- Sections 5-14: Core content with escalating reveals, each building on the last
- Sections 15-19: The big reveal, implications, what this means for the viewer personally
- Sections 20-22: Reflection, wider context, memorable closing thought
- Final section must end: "Subscribe and hit the bell — we post a new fascinating story every single day."
- Voice: Conversational but authoritative, like a brilliant friend explaining something over dinner
- Each visual keyword: concrete and searchable (avoid abstract terms like "concept" or "society")
- Vary the visual keywords — don't repeat the same word across sections"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    text = response.text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in script response: {text[:300]}")

    script = json.loads(match.group())
    if "sections" not in script or len(script["sections"]) < 10:
        raise ValueError(f"Script has too few sections: {len(script.get('sections', []))}")

    return script
