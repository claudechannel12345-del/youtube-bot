"""Create 2-3 vertical Short scripts from a full script JSON.

This is offline authoring tooling: it does not call TTS, render Remotion, or
touch the audio cache. It chooses hook moments from the source beats, keeps the
source narration sentence text unchanged, and writes compact vertical scene
scripts that can later be voiced/rendered by the normal Short pipeline.

Usage:
  py scripts/make_shorts_batch.py data/color_script_scenes.json --main-url https://youtu.be/...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from environments import has_environment  # noqa: E402

DEFAULT_OUT_DIR = os.path.join(ROOT, "data", "shorts_batch")
MAX_SHORTS = 3
MAX_SENTENCES = 5

HOOK_TERMS = {
    "change",
    "wins",
    "winner",
    "red",
    "swap",
    "swapped",
    "judge",
    "referee",
    "bias",
    "cheating",
    "score",
    "scored",
    "gone",
    "fair",
    "coin",
    "years",
}

ENV_BY_TEXT = [
    ("courtroom", ["court", "jury", "juries", "defendant", "lawyer", "sentence", "years"]),
    ("arena", ["athlete", "fighter", "fight", "mat", "olympic", "sport", "referee", "kick", "score"]),
    ("lab", ["research", "researcher", "study", "scientist", "repeat", "tested"]),
    ("news_studio", ["story", "channel", "subscribe", "second glance"]),
]

DEFAULT_ACTORS = {
    "arena": [
        {"id": "red_fighter", "asset": "person", "slot": "red_corner", "colorRole": "accent", "pose": "walking", "motion": "micro_bob"},
        {"id": "blue_fighter", "asset": "person", "slot": "blue_corner", "colorRole": "blue", "pose": "walking", "motion": "micro_bob"},
        {"id": "referee", "asset": "person", "slot": "referee_center", "colorRole": "ink", "pose": "pointing", "motion": "point"},
    ],
    "courtroom": [
        {"id": "judge", "asset": "judge", "slot": "judge_bench", "colorRole": "ink", "pose": "idle", "motion": "none"},
        {"id": "defendant", "asset": "person", "slot": "defendant_left", "colorRole": "muted", "pose": "sitting", "motion": "micro_bob"},
        {"id": "lawyer", "asset": "suit", "slot": "lawyer_right", "colorRole": "blue", "pose": "pointing", "motion": "point"},
    ],
    "lab": [
        {"id": "scientist", "asset": "scientist", "slot": "presenter", "colorRole": "blue", "pose": "pointing", "motion": "point"},
        {"id": "sample_a", "asset": "person", "slot": "sample_left", "colorRole": "accent", "pose": "idle", "motion": "micro_bob"},
        {"id": "sample_b", "asset": "person", "slot": "sample_right", "colorRole": "muted", "pose": "idle", "motion": "micro_bob"},
    ],
    "news_studio": [
        {"id": "host", "asset": "suit", "slot": "host_center", "colorRole": "accent", "pose": "pointing", "motion": "point"},
        {"id": "guest", "asset": "person", "slot": "guest_left", "colorRole": "blue", "pose": "idle", "motion": "micro_bob"},
        {"id": "screen", "asset": "eye", "slot": "screen", "colorRole": "accent", "pose": "idle", "motion": "none"},
    ],
}


def load_script(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
        raise ValueError("script must contain a sections list")
    return data


def choose_moments(script: Dict[str, Any], limit: int) -> List[Tuple[int, Dict[str, Any], int]]:
    candidates: List[Tuple[int, int, int, Dict[str, Any]]] = []
    for section_index, section in enumerate(script.get("sections", [])):
        for beat_index, beat in enumerate(section.get("beats", []) or []):
            score = _score_beat(section, beat)
            if score <= 0:
                continue
            start = int(beat.get("sentence_start", 0) or 0)
            candidates.append((score, section_index, start, beat))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))

    chosen = []
    used_sections = set()
    for _score, section_index, _start, beat in candidates:
        if section_index in used_sections and len(chosen) < min(limit, 3):
            continue
        chosen.append((section_index, beat, _score))
        used_sections.add(section_index)
        if len(chosen) >= limit:
            break
    return chosen


def build_short_script(script: Dict[str, Any], moment: Tuple[int, Dict[str, Any], int], ordinal: int, main_url: str) -> Dict[str, Any]:
    section_index, hook_beat, score = moment
    source_section = script["sections"][section_index]
    sentences = source_section.get("sentences", []) or []
    if not sentences:
        sentences = [{"text": source_section.get("narration", ""), "delivery": "neutral"}]

    window_start, window_end = _sentence_window(hook_beat, len(sentences))
    short_sentences = [dict(s) for s in sentences[window_start : window_end + 1]]
    narration = " ".join(str(s.get("text", "")).strip() for s in short_sentences if str(s.get("text", "")).strip())
    env_id = _choose_environment(source_section, hook_beat, short_sentences)
    title = _title_for_short(source_section, hook_beat, ordinal)

    beats = []
    for index, beat in enumerate(source_section.get("beats", []) or []):
        beat_start = int(beat.get("sentence_start", 0) or 0)
        beat_end = int(beat.get("sentence_end", beat_start) or beat_start)
        if beat_end < window_start or beat_start > window_end:
            continue
        copied = _short_beat(beat, index, window_start, env_id)
        beats.append(copied)
    if not beats:
        beats.append(_fallback_beat(hook_beat, env_id))

    section = {
        "section_index": 0,
        "key_phrase": source_section.get("key_phrase", title),
        "narration": narration,
        "sentences": short_sentences,
        "beats": beats,
        "environment": env_id,
        "orientation": "vertical",
        "vertical": True,
        "source_section_index": section_index,
        "source_sentence_start": window_start,
        "source_sentence_end": window_end,
    }
    return {
        "title": title,
        "description": "Short cut from the main video. Full story: %s" % main_url,
        "main_video_url": main_url,
        "source_title": script.get("title", ""),
        "source_section_index": section_index,
        "source_beat_id": hook_beat.get("id"),
        "hook_score": score,
        "sections": [section],
    }


def _score_beat(section: Dict[str, Any], beat: Dict[str, Any]) -> int:
    text = " ".join(
        [
            str(beat.get("text", "")),
            str(beat.get("visual_intent", "")),
            str(section.get("key_phrase", "")),
        ]
    ).lower()
    score = 0
    if beat.get("importance") == "high":
        score += 5
    elif beat.get("importance") == "must_hit":
        score += 6
    if beat.get("type") in ("stat_pop", "compare", "emphasize"):
        score += 3
    if section.get("environment") or beat.get("environment"):
        score += 2
    words = set(re.findall(r"[a-z0-9]+", text))
    score += min(6, len(words & HOOK_TERMS))
    return score


def _sentence_window(beat: Dict[str, Any], sentence_count: int) -> Tuple[int, int]:
    start = max(0, int(beat.get("sentence_start", 0) or 0))
    end = max(start, int(beat.get("sentence_end", start) or start))
    while (end - start + 1) < 3 and (start > 0 or end + 1 < sentence_count):
        if start > 0:
            start -= 1
        if (end - start + 1) >= 3:
            break
        if end + 1 < sentence_count:
            end += 1
    while (end - start + 1) > MAX_SENTENCES:
        if end - int(beat.get("sentence_end", end) or end) > int(beat.get("sentence_start", start) or start) - start:
            end -= 1
        else:
            start += 1
    return start, min(end, sentence_count - 1)


def _choose_environment(section: Dict[str, Any], beat: Dict[str, Any], sentences: List[Dict[str, Any]]) -> str:
    for value in (beat.get("environment"), section.get("environment")):
        env_id = str(value or "").split(":", 1)[0].strip()
        if has_environment(env_id):
            return env_id
    text = " ".join([str(beat.get("text", "")), str(beat.get("visual_intent", ""))] + [str(s.get("text", "")) for s in sentences]).lower()
    for env_id, terms in ENV_BY_TEXT:
        if any(term in text for term in terms) and has_environment(env_id):
            return env_id
    return "news_studio"


def _title_for_short(section: Dict[str, Any], beat: Dict[str, Any], ordinal: int) -> str:
    text = str(beat.get("text") or beat.get("visual_intent") or section.get("key_phrase") or "Short %d" % ordinal)
    clean = " ".join(text.replace("\n", " ").split())
    return clean[:60]


def _short_beat(beat: Dict[str, Any], index: int, window_start: int, env_id: str) -> Dict[str, Any]:
    beat_start = max(0, int(beat.get("sentence_start", 0) or 0) - window_start)
    beat_end = max(beat_start, int(beat.get("sentence_end", beat_start) or beat_start) - window_start)
    text = str(beat.get("text") or beat.get("visual_intent") or "").strip()
    copied = {
        "id": "short_%02d" % (index + 1),
        "type": beat.get("type", "emphasize"),
        "sentence_start": beat_start,
        "sentence_end": beat_end,
        "visual_intent": beat.get("visual_intent", text),
        "text": text,
        "subjects": beat.get("subjects", []),
        "importance": beat.get("importance", "high"),
        "environment": env_id,
        "vertical": True,
        "actors": _actors_for_beat(beat, env_id),
        "text_overlays": [{"role": _overlay_role(beat), "text": text, "tone": "coral_stamp" if beat.get("type") == "stat_pop" else "ink"}] if text else [],
    }
    if beat.get("colors"):
        copied["colors"] = beat.get("colors")
    return copied


def _fallback_beat(beat: Dict[str, Any], env_id: str) -> Dict[str, Any]:
    text = str(beat.get("text") or beat.get("visual_intent") or "FULL STORY").strip()
    return {
        "id": "short_01",
        "type": "emphasize",
        "sentence_start": 0,
        "sentence_end": 0,
        "visual_intent": text,
        "text": text,
        "subjects": [],
        "importance": "high",
        "environment": env_id,
        "vertical": True,
        "actors": DEFAULT_ACTORS.get(env_id, DEFAULT_ACTORS["news_studio"]),
        "text_overlays": [{"role": "headline", "text": text, "tone": "ink"}],
    }


def _actors_for_beat(beat: Dict[str, Any], env_id: str) -> List[Dict[str, Any]]:
    actors = beat.get("actors")
    if isinstance(actors, list) and actors:
        return [dict(actor) for actor in actors[:4] if isinstance(actor, dict)]
    return [dict(actor) for actor in DEFAULT_ACTORS.get(env_id, DEFAULT_ACTORS["news_studio"])]


def _overlay_role(beat: Dict[str, Any]) -> str:
    if beat.get("type") == "stat_pop":
        return "stat"
    if beat.get("type") in ("emphasize", "transition"):
        return "headline"
    return "label"


def write_batch(script: Dict[str, Any], out_dir: str, main_url: str, count: int) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for ordinal, moment in enumerate(choose_moments(script, count), start=1):
        short_script = build_short_script(script, moment, ordinal, main_url)
        path = os.path.join(out_dir, "short_%02d.json" % ordinal)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(short_script, f, indent=2)
        paths.append(path)
    return paths


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Build vertical Short scripts from a full script JSON.")
    parser.add_argument("script", nargs="?", default=os.path.join(ROOT, "data", "color_script_scenes.json"))
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--main-url", default="MAIN_VIDEO_URL")
    parser.add_argument("--count", type=int, default=MAX_SHORTS)
    args = parser.parse_args(argv[1:])

    script_path = args.script if os.path.isabs(args.script) else os.path.join(ROOT, args.script)
    out_dir = args.out_dir if os.path.isabs(args.out_dir) else os.path.join(ROOT, args.out_dir)
    count = max(2, min(MAX_SHORTS, int(args.count or MAX_SHORTS)))
    paths = write_batch(load_script(script_path), out_dir, args.main_url, count)
    print("wrote %d short scripts to %s" % (len(paths), out_dir))
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
