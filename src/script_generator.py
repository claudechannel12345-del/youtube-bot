import json
import re


def generate_script(topic_data, client):
    prompt = f"""You are a scriptwriter for a popular faceless YouTube educational channel.

Topic: {topic_data["topic"]}
Angle: {topic_data["angle"]}

Write a complete 3-4 minute video script. Return ONLY valid JSON, no markdown fences:

{{
    "title": "YouTube title (under 60 chars, compelling and specific, no ALL CAPS words)",
    "description": "3-paragraph YouTube description. First line is a strong hook sentence. Include relevant keywords naturally in paragraphs 2-3. End with: Subscribe for a new video every day!",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
    "sections": [
        {{
            "narration": "Exactly what the narrator says. 50-70 words. Conversational and engaging.",
            "visual": "Simple 1-3 word Pexels search term for a stock photo (e.g. ocean waves, city night, scientist lab)"
        }}
    ]
}}

Script requirements:
- Exactly 10-12 sections
- Section 1: Powerful hook — start with a surprising fact, question, or statement
- Sections 2-10: Deliver interesting content with great pacing and flow
- Final section: "If you enjoyed that, hit like and subscribe — we post a brand new video every single day."
- Voice: Conversational, curious, engaging — like telling a friend something amazing
- Visual keyword: simple, concrete, searchable (avoid abstract words like "concept" or "idea")"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    text = response.text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in script response: {text[:300]}")

    script = json.loads(match.group())
    if "sections" not in script or len(script["sections"]) < 5:
        raise ValueError(f"Script has too few sections: {len(script.get('sections', []))}")

    return script
