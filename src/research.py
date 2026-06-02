import json
import re
import requests


def get_trending_topics(api_key, max_results=15):
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "US",
            "maxResults": max_results,
            "key": api_key,
        },
        timeout=30,
    )
    resp.raise_for_status()

    topics = []
    for item in resp.json().get("items", []):
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        topics.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "view_count": int(stats.get("viewCount", 0)),
        })
    return topics


def pick_topic(topics, client):
    topics_text = "\n".join(
        f'- "{t["title"]}" by {t["channel"]} ({t["view_count"]:,} views)'
        for t in topics[:12]
    )

    prompt = f"""You are a YouTube content strategist for a faceless educational channel.

Today's trending YouTube videos:
{topics_text}

Choose ONE topic to make an educational video about. Requirements:
- Educational (facts, science, history, technology, psychology, money, nature, space)
- Evergreen (NOT breaking news, sports scores, or celebrity gossip)
- Easy to illustrate with stock photography
- Broad audience appeal

Return ONLY valid JSON, no markdown fences:
{{
    "topic": "specific topic to cover",
    "angle": "the interesting hook or unique angle for our video",
    "visual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
}}"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    match = re.search(r"\{.*\}", response.text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in research response: {response.text[:300]}")
    return json.loads(match.group())
