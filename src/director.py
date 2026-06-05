"""Cutaway director (rules-first).

Turns a script (sections with `beats`) plus per-sentence timings into a concrete,
deterministic cutaway plan shaped like remotion/src/cutaway/types.ts EpisodeProps.

Pattern: build -> validate -> repair per beat -> deterministic fallback (never drop a
section). An optional LLM director can be layered later that only SUGGESTS into this
validator; the rules here always own the render.
"""

from cutaway_vocab import (
    BEAT_TO_SCENE_FAMILY,
    CAMERA_INTENSITY,
    CAMERA_MOVE,
    LAYOUT,
    MOTION_KIND,
    SCENE_FAMILY,
    TRANSITION,
    coerce_beat_type,
)

STYLE_VERSION = "clean_flat_light_v1"

# default screen layout per scene family
DEFAULT_LAYOUT = {
    "title_stage": "center_subject",
    "object_stage": "center_subject",
    "diagram_stage": "radial",
    "map_stage": "map_focus",
    "comparison_stage": "left_right",
    "timeline_stage": "timeline_horizontal",
    "list_stage": "top_down_stack",
    "stat_stage": "center_subject",
    "paperwork_stage": "paper_stack",
    "miniature_world": "wide_scene",
    "caption_punch": "caption_only",
}

# default camera (move, intensity) per beat type
DEFAULT_CAMERA = {
    "establish": ("hold_then_push", "small"),
    "illustrate": ("static", "none"),
    "stat_pop": ("push_in", "small"),
    "compare": ("static", "none"),
    "diagram_build": ("hold_then_push", "small"),
    "map_focus": ("push_in", "medium"),
    "list_reveal": ("static", "none"),
    "cutaway_gag": ("snap_zoom", "medium"),
    "emphasize": ("push_in", "small"),
    "transition": ("static", "none"),
}

# default motion kinds per beat type (applied to the primary asset / overlay)
DEFAULT_MOTION = {
    "establish": ["pop_in"],
    "illustrate": ["pop_in"],
    "stat_pop": ["count_up"],
    "compare": ["slide_in"],
    "diagram_build": ["draw_on"],
    "map_focus": ["wipe_reveal"],
    "list_reveal": ["slide_in"],
    "cutaway_gag": ["pop_in", "stamp"],
    "emphasize": ["pop_in"],
    "transition": ["pop_in"],
}

# beat type -> default text overlay role / tone
# beat type -> default text overlay role / tone.
# Beats that carry ASSETS use the small "label" (bottom) so big headlines never
# overlap the artwork. Big "headline" is reserved for text-only caption_punch beats.
DEFAULT_TEXT_ROLE = {
    "establish": ("label", "ink"),
    "illustrate": ("label", "ink"),
    "stat_pop": ("stat", "coral_stamp"),
    "compare": ("label", "ink"),
    "diagram_build": ("label", "ink"),
    "map_focus": ("label", "ink"),
    "list_reveal": ("label", "ink"),
    "cutaway_gag": ("stamp", "coral_stamp"),
    "emphasize": ("headline", "coral_stamp"),
    "transition": ("headline", "ink"),
}

# spread anchors for N assets
ANCHOR_SPREAD = {
    1: ["center"],
    2: ["left", "right"],
    3: ["left", "center", "right"],
    4: ["upper_left", "upper_right", "lower_left", "lower_right"],
}

_SUBJECT_ALIASES = {
    "city": "building",
    "buildings": "building",
    "atomic clock": "clock",
    "atomic_clock": "clock",
    "map pin": "map_pin",
    "mappin": "map_pin",
    "pin": "map_pin",
    "blue_dot": "dot",
    "blue dot": "dot",
    "time signal": "signal",
    "signal beam": "signal_beam",
}


def _norm_subject(s):
    key = str(s).strip().lower()
    key = _SUBJECT_ALIASES.get(key, key)
    return key.replace(" ", "_")


def _clampi(v, lo, hi):
    return max(lo, min(hi, v))


def _assets_from_subjects(subjects):
    subjects = [s for s in (subjects or []) if str(s).strip()]
    if not subjects:
        subjects = ["generic_object"]
    subjects = subjects[:4]
    anchors = ANCHOR_SPREAD.get(len(subjects), ["center"] * len(subjects))
    assets = []
    for i, subj in enumerate(subjects):
        assets.append(
            {
                "id": "a%d" % i,
                "kind": "prop",
                "name": _norm_subject(subj),
                "anchor": anchors[i],
            }
        )
    return assets


def _safe(value, vocab, fallback):
    return value if value in vocab else fallback


def _direct_beat(beat, sentences_timing, fps, is_first):
    btype = coerce_beat_type(beat.get("type", "illustrate"))
    n = len(sentences_timing)
    s_start = _clampi(int(beat.get("sentence_start", 0)), 0, max(0, n - 1))
    s_end = _clampi(int(beat.get("sentence_end", s_start)), s_start, max(0, n - 1))

    if n > 0:
        start = float(sentences_timing[s_start]["start"])
        end = float(sentences_timing[s_end]["end"])
    else:
        start, end = 0.0, 1.0
    if end <= start:
        end = start + 0.6

    move, intensity = DEFAULT_CAMERA.get(btype, ("static", "none"))
    move = _safe(move, CAMERA_MOVE, "static")
    intensity = _safe(intensity, CAMERA_INTENSITY, "none")

    scene_family = _safe(BEAT_TO_SCENE_FAMILY.get(btype, "object_stage"), SCENE_FAMILY, "object_stage")
    layout = _safe(DEFAULT_LAYOUT.get(scene_family, "center_subject"), LAYOUT, "center_subject")

    trans_in = "smash_cut" if btype == "cutaway_gag" else ("dip_to_bg" if is_first else "hard_cut")
    trans_in = _safe(trans_in, TRANSITION, "hard_cut")

    background = "panel" if scene_family == "comparison_stage" else ("grid" if scene_family == "diagram_stage" else "plain")

    assets = _assets_from_subjects(beat.get("subjects"))

    overlays = []
    text = str(beat.get("text", "") or "").strip()
    if text:
        role, tone = DEFAULT_TEXT_ROLE.get(btype, ("label", "ink"))
        anchor = "headline" if role == "headline" else ("stat" if role == "stat" else "lower_center")
        overlays.append({"role": role, "text": text[:48], "anchor": anchor, "tone": tone})

    motions = []
    target = assets[0]["id"] if assets else "overlay"
    for i, kind in enumerate(DEFAULT_MOTION.get(btype, ["pop_in"])):
        kind = _safe(kind, MOTION_KIND, "pop_in")
        motions.append({"target": target, "kind": kind, "delay": 0.12 * i, "duration": 0.4})

    return {
        "id": str(beat.get("id", "beat")),
        "type": btype,
        "start": round(start, 3),
        "end": round(end, 3),
        "startFrame": int(round(start * fps)),
        "endFrame": int(round(end * fps)),
        "scene_family": scene_family,
        "layout": layout,
        "camera": {"move": move, "target": "center", "intensity": intensity},
        "transition_in": trans_in,
        "transition_out": "hard_cut",
        "background": background,
        "assets": assets,
        "text_overlays": overlays,
        "motion": motions,
    }


def _fallback_beat(section, sentences_timing, fps):
    start = 0.0
    end = float(sentences_timing[-1]["end"]) if sentences_timing else 2.0
    return {
        "id": "fallback",
        "type": "emphasize",
        "start": 0.0,
        "end": round(end, 3),
        "startFrame": 0,
        "endFrame": int(round(end * fps)),
        "scene_family": "caption_punch",
        "layout": "caption_only",
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut",
        "transition_out": "hard_cut",
        "background": "plain",
        "assets": [],
        "text_overlays": [
            {"role": "headline", "text": str(section.get("key_phrase", ""))[:48], "anchor": "center", "tone": "ink"}
        ],
        "motion": [{"target": "overlay", "kind": "pop_in", "delay": 0.0, "duration": 0.3}],
    }


def direct_section(section, sentences_timing, fps, index):
    """sentences_timing: list of {text,start,end,delivery} relative to the section start."""
    duration = float(sentences_timing[-1]["end"]) if sentences_timing else 2.0
    section_frames = int(round(duration * fps))
    directed = []
    beats = section.get("beats") or []
    for i, beat in enumerate(beats):
        try:
            directed.append(_direct_beat(beat, sentences_timing, fps, is_first=(i == 0)))
        except Exception:
            continue
    if not directed:
        directed.append(_fallback_beat(section, sentences_timing, fps))

    # Tile beats so they cover the WHOLE section with no gaps. A gap between two
    # beats' frame windows renders as a blank frame, so each beat is stretched to
    # hold until the next one starts; the last beat holds to the section end.
    directed.sort(key=lambda b: b["startFrame"])
    directed[0]["startFrame"] = 0
    for i in range(len(directed) - 1):
        directed[i]["endFrame"] = max(directed[i]["startFrame"] + 1, directed[i + 1]["startFrame"])
    directed[-1]["endFrame"] = max(directed[-1]["startFrame"] + 1, section_frames)
    for b in directed:
        b["start"] = round(b["startFrame"] / fps, 3)
        b["end"] = round(b["endFrame"] / fps, 3)

    return {
        "section_index": index,
        "durationInFrames": section_frames,
        "audioSrc": section.get("audioSrc", "") or "",
        "key_phrase": str(section.get("key_phrase", "")),
        "narration": section.get("narration", ""),
        "captions": sentences_timing,
        "beats": directed,
    }


def build_episode(script, per_section_timings, fps=30, width=1920, height=1080):
    """per_section_timings: list (one per section) of sentence-timing lists."""
    sections = []
    for i, section in enumerate(script.get("sections", [])):
        timings = per_section_timings[i] if i < len(per_section_timings) else []
        sections.append(direct_section(section, timings, fps, i))
    return {
        "schema_version": 1,
        "fps": fps,
        "width": width,
        "height": height,
        "style_version": STYLE_VERSION,
        "sections": sections,
    }
