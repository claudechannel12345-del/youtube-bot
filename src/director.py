"""Cutaway director (rules-first).

Turns a script (sections with `beats`) plus per-sentence timings into a concrete,
deterministic cutaway plan shaped like remotion/src/cutaway/types.ts EpisodeProps.

Pattern: build -> validate -> repair per beat -> deterministic fallback (never drop a
section). An optional LLM director can be layered later that only SUGGESTS into this
validator; the rules here always own the render.
"""

import copy
import json
import os
import sys

from cutaway_vocab import (
    BEAT_TO_SCENE_FAMILY,
    BACKGROUND_TREATMENT,
    CAMERA_INTENSITY,
    CAMERA_MOVE,
    COLOR_ROLE,
    CONNECTION_KIND,
    LAYOUT,
    MOTION_KIND,
    MOTION_KIND_V2,
    REGISTRY_ASSETS,
    SCENE_FAMILY,
    TRANSITION,
    coerce_beat_type,
)
from blueprint_presets import build_blueprint
from environments import ENVIRONMENT_VARIANTS, ENVIRONMENTS, get_environment, has_environment
from env_resolver import resolve_environment

STYLE_VERSION = "clean_flat_light_v1"
DIRECTOR_MODE = os.environ.get("DIRECTOR_MODE", "rules").strip().lower()
# allowed: rules | llm

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
    "quote_stage": "quote_card",
    "caption_punch": "caption_only",
}

# default camera (move, intensity) per beat type
DEFAULT_CAMERA = {
    "establish": ("hold_then_push", "small"),
    "illustrate": ("static", "none"),
    "stat_pop": ("push_in", "small"),
    "compare": ("static", "none"),
    "diagram_build": ("hold_then_push", "small"),
    "process": ("pan_right", "small"),
    "map_focus": ("push_in", "medium"),
    "list_reveal": ("static", "none"),
    "quote": ("hold_then_push", "small"),
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
    "process": ["slide_in"],
    "map_focus": ["wipe_reveal"],
    "list_reveal": ["slide_in"],
    "quote": ["pop_in"],
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
    "process": ("label", "ink"),
    "map_focus": ("label", "ink"),
    "list_reveal": ("label", "ink"),
    "quote": ("caption", "ink"),
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
    "paperwork": "document",
    "paper": "document",
    "test": "document",
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

BUILD_RUN_TYPES = frozenset(["diagram_build", "process", "compare", "list_reveal"])
EFFECT_ASSETS = frozenset(["signal", "signal_beam"])
CONTEXT_ASSETS = frozenset(["phone", "satellite", "earth"])
# Beat types that render their `text` as an on-screen label. Includes compare/establish/illustrate so
# comparison panels ("RED vs BLUE") and object scenes ("A STATUS REPORT") actually caption themselves
# (a bottom "label", which won't overlap the centered art).
TEXT_OVERLAY_BEAT_TYPES = frozenset(
    ["stat_pop", "quote", "cutaway_gag", "emphasize", "transition", "compare", "establish", "illustrate"]
)
GENERIC_OVERLAY_TEXT = frozenset(
    [
        "label",
        "stamp",
        "clock",
        "distance",
        "earth",
        "satellite",
        "phone",
        "signal",
        "map",
        "point",
        "dot",
        "generic_object",
    ]
)

CAMERA_VARIANTS = [
    ("hold_then_push", "small"),
    ("push_in", "small"),
    ("pull_back", "small"),
    ("pan_left", "small"),
    ("pan_right", "small"),
    ("parallax_drift", "small"),
]

_CATALOG_ASSET_ORDER = [
    "person",
    "phone",
    "city",
    "building",
    "satellite",
    "signal",
    "signal_beam",
    "earth",
    "map_pin",
    "dot",
    "clock",
    "atomic_clock",
    "watch",
    "grid",
    "sphere",
    "ring",
    "point",
    "ruler",
    "arrow",
    "light",
    "einstein",
    "mandrill",
    "finch",
    "person_female",
    "person_arms_up",
    "person_pointing",
    "person_sitting",
    "person_walking",
    "person_left",
    "person_right",
    "doctor",
    "scientist",
    "judge",
    "athlete",
    "suit",
    "heart",
    "gavel",
    "document",
    "eye",
    "car",
    "tree",
    "house",
    "coin",
    "money",
    "trophy",
    "book",
    "bag",
    "bottle",
    "cup",
    "box",
    "key",
    "lightbulb",
    "lock",
    "shield",
    "flag",
    "ball",
    "camera",
    "microphone",
    "laptop",
    "chart_bar",
    "chart_line",
    "pie_chart",
    "arrow_up",
    "arrow_down",
    "checkmark",
    "cross",
    "question_mark",
    "warning",
    "gear",
    "magnet",
    "brain",
    "dna",
    "pill",
    "syringe",
    "scale_justice",
    "ballot",
    "crown",
    "target",
    "sun",
    "cloud",
    "rain",
    "star",
    "moon",
    "mountain_shape",
    "wave",
    "fire",
    "plant",
    "map",
    "coffee",
    "counter",
    "number",
    "subscribe",
    "label",
    "stamp",
    "generic_object",
]

_CATALOG_ASSET_META = {
    "person": {"typical_scale": 0.8, "notes": "human figure"},
    "phone": {"typical_scale": 0.55},
    "city": {"typical_scale": 0.82, "notes": "small skyline cluster"},
    "building": {"typical_scale": 0.78, "notes": "single flat building"},
    "satellite": {"typical_scale": 0.55},
    "signal": {"typical_scale": 1.0},
    "signal_beam": {"typical_scale": 1.0},
    "earth": {"typical_scale": 1.2},
    "map_pin": {"typical_scale": 0.5},
    "dot": {"typical_scale": 0.45},
    "clock": {"typical_scale": 0.7},
    "atomic_clock": {"typical_scale": 0.7},
    "watch": {"typical_scale": 0.65},
    "grid": {"typical_scale": 1.0},
    "sphere": {"typical_scale": 1.0},
    "ring": {"typical_scale": 1.0},
    "point": {"typical_scale": 0.45},
    "ruler": {"typical_scale": 0.7},
    "arrow": {"typical_scale": 0.75},
    "light": {"typical_scale": 0.8},
    "einstein": {"typical_scale": 0.75},
    "mandrill": {"typical_scale": 0.9, "notes": "colorful mandrill face"},
    "finch": {"typical_scale": 0.5, "notes": "small profile bird"},
    "person_female": {"typical_scale": 0.8, "notes": "female human figure"},
    "person_arms_up": {"typical_scale": 0.78, "notes": "human figure with raised arms"},
    "person_pointing": {"typical_scale": 0.78, "notes": "human figure pointing right"},
    "person_sitting": {"typical_scale": 0.78, "notes": "seated human figure"},
    "person_walking": {"typical_scale": 0.78, "notes": "walking human figure"},
    "person_left": {"typical_scale": 0.8, "notes": "human figure facing left"},
    "person_right": {"typical_scale": 0.8, "notes": "human figure facing right"},
    "doctor": {"typical_scale": 0.8, "notes": "doctor role figure"},
    "scientist": {"typical_scale": 0.8, "notes": "scientist role figure"},
    "judge": {"typical_scale": 0.8, "notes": "judge role figure"},
    "athlete": {"typical_scale": 0.8, "notes": "athlete role figure"},
    "suit": {"typical_scale": 0.8, "notes": "business suit role figure"},
    "heart": {"typical_scale": 0.5, "notes": "coral attraction heart"},
    "gavel": {"typical_scale": 0.7, "notes": "judge gavel and sound block"},
    "document": {"typical_scale": 0.8, "notes": "sheet of paper with text lines"},
    "eye": {"typical_scale": 0.8, "notes": "flat eye brand mark"},
    "car": {"typical_scale": 0.75, "notes": "side-view car"},
    "tree": {"typical_scale": 0.75, "notes": "simple leafy tree"},
    "house": {"typical_scale": 0.8, "notes": "small house"},
    "coin": {"typical_scale": 0.62, "notes": "single gold coin"},
    "money": {"typical_scale": 0.75, "notes": "paper money bill"},
    "trophy": {"typical_scale": 0.7, "notes": "award trophy"},
    "book": {"typical_scale": 0.72, "notes": "open book"},
    "bag": {"typical_scale": 0.7, "notes": "handled bag"},
    "bottle": {"typical_scale": 0.65, "notes": "bottle with label"},
    "cup": {"typical_scale": 0.65, "notes": "handled cup"},
    "box": {"typical_scale": 0.7, "notes": "open-top shipping box"},
    "key": {"typical_scale": 0.68, "notes": "large key"},
    "lightbulb": {"typical_scale": 0.68, "notes": "idea lightbulb"},
    "lock": {"typical_scale": 0.68, "notes": "padlock"},
    "shield": {"typical_scale": 0.7, "notes": "protection shield"},
    "flag": {"typical_scale": 0.7, "notes": "pole flag"},
    "ball": {"typical_scale": 0.65, "notes": "generic sports ball"},
    "camera": {"typical_scale": 0.72, "notes": "photo camera"},
    "microphone": {"typical_scale": 0.68, "notes": "podcast microphone"},
    "laptop": {"typical_scale": 0.78, "notes": "open laptop"},
    "chart_bar": {"typical_scale": 0.72, "notes": "bar chart"},
    "chart_line": {"typical_scale": 0.72, "notes": "line chart"},
    "pie_chart": {"typical_scale": 0.7, "notes": "pie chart"},
    "arrow_up": {"typical_scale": 0.72, "notes": "upward arrow"},
    "arrow_down": {"typical_scale": 0.72, "notes": "downward arrow"},
    "checkmark": {"typical_scale": 0.72, "notes": "approval check mark"},
    "cross": {"typical_scale": 0.72, "notes": "rejection cross mark"},
    "question_mark": {"typical_scale": 0.75, "notes": "question mark"},
    "warning": {"typical_scale": 0.7, "notes": "warning triangle"},
    "gear": {"typical_scale": 0.68, "notes": "settings gear"},
    "magnet": {"typical_scale": 0.72, "notes": "horseshoe magnet"},
    "brain": {"typical_scale": 0.72, "notes": "brain icon"},
    "dna": {"typical_scale": 0.72, "notes": "DNA helix"},
    "pill": {"typical_scale": 0.68, "notes": "capsule pill"},
    "syringe": {"typical_scale": 0.68, "notes": "medical syringe"},
    "scale_justice": {"typical_scale": 0.72, "notes": "justice scales"},
    "ballot": {"typical_scale": 0.72, "notes": "checked ballot"},
    "crown": {"typical_scale": 0.68, "notes": "gold crown"},
    "target": {"typical_scale": 0.7, "notes": "bullseye target"},
    "sun": {"typical_scale": 0.62, "notes": "weather sun"},
    "cloud": {"typical_scale": 0.68, "notes": "weather cloud"},
    "rain": {"typical_scale": 0.68, "notes": "rain cloud"},
    "star": {"typical_scale": 0.62, "notes": "five-point star"},
    "moon": {"typical_scale": 0.62, "notes": "crescent moon"},
    "mountain_shape": {"typical_scale": 0.78, "notes": "mountain silhouette"},
    "wave": {"typical_scale": 0.72, "notes": "ocean wave"},
    "fire": {"typical_scale": 0.68, "notes": "flame"},
    "plant": {"typical_scale": 0.68, "notes": "potted plant"},
    "map": {"typical_scale": 1.1},
    "coffee": {"typical_scale": 0.75},
    "counter": {"typical_scale": 1.0},
    "number": {"typical_scale": 1.0},
    "subscribe": {"typical_scale": 0.9},
    "label": {"typical_scale": 1.0},
    "stamp": {"typical_scale": 1.0},
    "generic_object": {"typical_scale": 0.8},
}

_CATALOG_ANCHORS = {
    "center": [960, 540],
    "left": [560, 560],
    "right": [1360, 560],
    "upper_left": [370, 190],
    "upper_right": [1550, 190],
    "lower_left": [390, 850],
    "lower_right": [1530, 850],
    "upper_center": [960, 170],
    "lower_center": [960, 858],
    "headline": [960, 210],
    "stat": [960, 470],
    "diagram_core": [960, 540],
}

_MOTION_KIND_ORDER = [
    "none",
    "pop_in",
    "pop_out",
    "slide_in",
    "slide_out",
    "draw_on",
    "count_up",
    "stamp",
    "shake_once",
    "micro_bob",
    "orbit",
    "pulse",
    "trace_line",
    "wipe_reveal",
    "enter",
    "hold",
    "exit",
    "connect_to",
    "count",
    "draw_path",
    "highlight",
]

_CAMERA_MOVE_ORDER = [
    "static",
    "hold_then_push",
    "push_in",
    "pull_back",
    "pan_left",
    "pan_right",
    "snap_zoom",
    "tilt_down",
    "parallax_drift",
]

_BACKGROUND_ORDER = ["plain", "panel", "grid", "map", "comparison_panels", "paper_stack"]
_CONNECTION_KIND_ORDER = ["line", "arrow", "range_ring", "pulse", "brace"]

_ART_DIRECTOR_PROMPT = """You are the art director for a clean flat vector explainer video.

Return ONLY valid JSON. No markdown. No comments.

You must produce one storyboard blueprint per beat. You may only use the supplied closed vocabulary:
- registry_assets exactly as named
- environments exactly as named, or null when no staged place helps
- environment_variants exactly as named
- slots only from the chosen environment
- anchors exactly as named, or explicit x/y coordinates inside 1920x1080
- motion_kinds exactly as named
- camera_moves exactly as named
- backgrounds exactly as named
- connection_kinds exactly as named

Do not invent assets. Do not request generated images. Do not use photorealism. Do not describe visuals the engine cannot draw.

Style:
- clean flat vector, light paper background
- few large readable elements
- no crowded diagrams
- text must be short and uppercase unless it is a quote
- prefer concrete spatial staging over generic centered icons
- every important narration beat must have a visual action

Input:
%s

Output schema:
{
  "section_index": number,
  "environment": EnvironmentId or null,
  "environment_variant": "day" | "night" | "crowded" | "empty" | null,
  "beats": [
    {
      "id": string,
      "actors": [
        {"id": string, "asset": RegistryAsset, "pose": "idle" | "arms_up" | "pointing" | "sitting" | "walking" | "left" | "right" | "lean", "slot": SlotId, "colorRole": ColorRole, "motion": "idle" | "point" | "lean" | MotionKind}
      ],
      "blueprint": {
        "version": 1,
        "preset": SceneFamily,
        "intent": string,
        "background": {"treatment": BackgroundTreatment},
        "camera": {"move": CameraMove, "target": ElementRef or AnchorId, "intensity": CameraIntensity},
        "elements": [...],
        "connections": [...]
      }
    }
  ]
}

Rules:
- Preserve every input beat id exactly.
- Do not change timing fields; timing is owned by the rules director.
- If you choose an environment, stage 1 to 4 actors per beat into valid slots for that environment.
- Use actor pose/motion only when it clarifies the action; prefer idle, pointing, sitting, walking, arms_up, or lean.
- Use environment staging for concrete places, people, institutions, competitions, labs, studios, travel, weather, and public scenes.
- Leave environment null for abstract diagrams, pure stats, maps, lists, timelines, and text-only beats.
- Use 1 to 7 elements per beat, excluding connections.
- Use at most 2 text elements per beat.
- Text caps: label 28 chars, headline 34, stamp 30, stat 22, caption 160, tiny_note 42.
- All element ids must be unique within a beat.
- Every connection must reference existing element ids or legal anchors.
- Motion start and duration are seconds relative to the beat, not frames.
- Motion must stay within the beat duration implied by sentence timings.
- Use coordinates inside safe area unless intentionally entering/exiting.
- Prefer explicit point coordinates for important elements.
"""


def _ordered_from_vocab(order, vocab):
    return [name for name in order if name in vocab]


def build_capabilities_catalog():
    registry_assets = []
    for name in _ordered_from_vocab(_CATALOG_ASSET_ORDER, REGISTRY_ASSETS):
        item = {"name": name}
        item.update(_CATALOG_ASSET_META[name])
        registry_assets.append(item)
    environments = []
    for env_id in sorted(ENVIRONMENTS):
        try:
            env = get_environment(env_id)
        except Exception:
            continue
        environments.append(
            {
                "id": env_id,
                "slots": [
                    {
                        "name": name,
                        "role": doc.get("role"),
                        "depth": doc.get("depth"),
                        "scale": doc.get("scale"),
                    }
                    for name, doc in sorted((env.get("slot_docs") or {}).items())
                ],
                "text_zone": env.get("text_zone"),
            }
        )
    return {
        "world": {"width": 1920, "height": 1080, "safe_margin": 96},
        "style": {
            "version": "clean_flat_light_v1",
            "rules": [
                "flat vector only",
                "no raster images",
                "no photorealism",
                "use few large readable elements",
                "uppercase short text",
            ],
        },
        "registry_assets": registry_assets,
        "environments": environments,
        "environment_variants": sorted(ENVIRONMENT_VARIANTS),
        "anchors": dict(_CATALOG_ANCHORS),
        "motion_kinds": _ordered_from_vocab(_MOTION_KIND_ORDER, MOTION_KIND_V2),
        "camera_moves": _ordered_from_vocab(_CAMERA_MOVE_ORDER, CAMERA_MOVE),
        "backgrounds": _ordered_from_vocab(_BACKGROUND_ORDER, BACKGROUND_TREATMENT),
        "connection_kinds": _ordered_from_vocab(_CONNECTION_KIND_ORDER, CONNECTION_KIND),
    }


def _norm_subject(s):
    key = str(s).strip().lower()
    key = _SUBJECT_ALIASES.get(key, key)
    return key.replace(" ", "_")


def _clampi(v, lo, hi):
    return max(lo, min(hi, v))


def _anchor_sequence(count):
    if count in ANCHOR_SPREAD:
        return ANCHOR_SPREAD[count]
    return ["upper_left", "upper_right", "center", "lower_left", "lower_right", "left"][:count]


def _assets_from_subjects(subjects, beat_id="beat"):
    subjects = [s for s in (subjects or []) if str(s).strip()]
    if not subjects:
        subjects = ["generic_object"]
    subjects = subjects[:4]
    anchors = ANCHOR_SPREAD.get(len(subjects), ["center"] * len(subjects))
    assets = []
    for i, subj in enumerate(subjects):
        assets.append(
            {
                "id": "%s_a%d" % (beat_id, i),
                "kind": "prop",
                "name": _norm_subject(subj),
                "anchor": anchors[i],
                "is_new": True,
            }
        )
    return _ensure_effect_context(assets, beat_id)


def _ensure_effect_context(assets, beat_id):
    names = [a["name"] for a in assets]
    has_effect = any(name in EFFECT_ASSETS for name in names)
    has_context = any(name in CONTEXT_ASSETS for name in names)
    if not has_effect or has_context:
        return assets
    context = {
        "id": "%s_context_phone" % beat_id,
        "kind": "prop",
        "name": "phone",
        "anchor": "left",
        "is_new": True,
    }
    adjusted = [context]
    for i, asset in enumerate(assets):
        adjusted_asset = dict(asset)
        adjusted_asset["anchor"] = "right" if i == 0 else adjusted_asset.get("anchor", "center")
        adjusted.append(adjusted_asset)
    return adjusted[:4]


def _camera_for_beat(btype, beat_index):
    move, intensity = DEFAULT_CAMERA.get(btype, ("static", "none"))
    if move == "static" or intensity == "none":
        move, intensity = CAMERA_VARIANTS[beat_index % len(CAMERA_VARIANTS)]
    elif beat_index % 3 == 2:
        move, intensity = CAMERA_VARIANTS[beat_index % len(CAMERA_VARIANTS)]
    return _safe(move, CAMERA_MOVE, "static"), _safe(intensity, CAMERA_INTENSITY, "none")


def _safe(value, vocab, fallback):
    return value if value in vocab else fallback


def _clean_meaningful_text(text, subjects=None):
    cleaned = " ".join(str(text or "").strip().split())
    if not cleaned:
        return ""
    normalized = cleaned.lower().replace("_", " ")
    if normalized in GENERIC_OVERLAY_TEXT:
        return ""
    subject_names = {
        _norm_subject(subject).replace("_", " ")
        for subject in (subjects or [])
        if str(subject).strip()
    }
    if normalized in subject_names:
        return ""
    return cleaned


def _direct_beat(beat, sentences_timing, fps, is_first, beat_index, environment_id=None):
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

    move, intensity = _camera_for_beat(btype, beat_index)

    scene_family = _safe(BEAT_TO_SCENE_FAMILY.get(btype, "object_stage"), SCENE_FAMILY, "object_stage")
    layout = _safe(DEFAULT_LAYOUT.get(scene_family, "center_subject"), LAYOUT, "center_subject")

    trans_in = "smash_cut" if btype == "cutaway_gag" else ("dip_to_bg" if is_first else "hard_cut")
    trans_in = _safe(trans_in, TRANSITION, "hard_cut")

    background = "panel" if scene_family == "comparison_stage" else ("grid" if scene_family == "diagram_stage" else "plain")

    beat_id = str(beat.get("id", "beat%d" % beat_index)).replace(" ", "_")
    if btype == "quote":
        assets = []
    elif btype == "process" and beat.get("steps"):
        assets = [
            {
                "id": "%s_step%d" % (beat_id, i),
                "kind": "label",
                "name": "label",
                "anchor": "center",
                "variant": _clean_meaningful_text(step) or str(step).strip(),
                "is_new": True,
            }
            for i, step in enumerate(beat.get("steps", [])[:5])
            if str(step).strip()
        ]
    else:
        assets = _assets_from_subjects(beat.get("subjects"), beat_id)

    overlays = []
    text = _clean_meaningful_text(beat.get("text", ""), beat.get("subjects"))
    if btype == "quote":
        quote = _clean_meaningful_text(beat.get("quote", "") or text, beat.get("subjects"))
        attribution = _clean_meaningful_text(beat.get("attribution", ""), beat.get("subjects"))
        if quote:
            overlays.append({"role": "caption", "text": quote, "anchor": "center", "tone": "ink"})
        if attribution:
            overlays.append({"role": "tiny_note", "text": attribution, "anchor": "lower_center", "tone": "muted"})
    if text and btype in TEXT_OVERLAY_BEAT_TYPES:
        role, tone = DEFAULT_TEXT_ROLE.get(btype, ("label", "ink"))
        anchor = "headline" if role == "headline" else ("stat" if role == "stat" else "lower_center")
        if btype != "quote":
            overlays.append({"role": role, "text": text, "anchor": anchor, "tone": tone})

    if environment_id:
        keep_text = btype in ("stat_pop", "quote") or btype == "emphasize" or bool(beat.get("emphasis"))
        if keep_text:
            overlays = overlays[:1]
        else:
            overlays = []

    motions = []
    motion_kinds = DEFAULT_MOTION.get(btype, ["pop_in"])
    for asset_index, asset in enumerate(assets):
        kind = _safe(motion_kinds[min(asset_index, len(motion_kinds) - 1)], MOTION_KIND, "pop_in")
        motions.append({"target": asset["id"], "kind": kind, "delay": 0.08 * asset_index, "duration": 0.38})
    if not assets:
        motions.append({"target": "overlay", "kind": "pop_in", "delay": 0.0, "duration": 0.3})

    directed = {
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
        "compare_colors": beat.get("colors"),
    }
    if environment_id:
        directed["environment"] = environment_id
        directed["scene_family"] = "scene_stage"
        directed["layout"] = "wide_scene"
        directed["background"] = "plain"
        if isinstance(beat.get("actors"), list):
            directed["actors"] = copy.deepcopy(beat.get("actors"))
    return directed


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
            {"role": "headline", "text": _clean_meaningful_text(section.get("key_phrase", "")) or "CUTAWAY", "anchor": "center", "tone": "ink"}
        ],
        "motion": [{"target": "overlay", "kind": "pop_in", "delay": 0.0, "duration": 0.3}],
    }


def _settled_asset(asset):
    settled = dict(asset)
    settled["is_new"] = False
    return settled


def _new_asset(asset):
    fresh = dict(asset)
    fresh["is_new"] = True
    return fresh


def _rebuild_motion_for_new_assets(beat):
    motion_kinds = DEFAULT_MOTION.get(beat["type"], ["pop_in"])
    motions = []
    new_index = 0
    for asset in beat["assets"]:
        if not asset.get("is_new"):
            continue
        kind = _safe(motion_kinds[min(new_index, len(motion_kinds) - 1)], MOTION_KIND, "pop_in")
        motions.append({"target": asset["id"], "kind": kind, "delay": 0.08 * new_index, "duration": 0.38})
        new_index += 1
    beat["motion"] = motions or [{"target": "overlay", "kind": "none", "delay": 0.0, "duration": 0.1}]


def _apply_progressive_builds(directed):
    i = 0
    while i < len(directed):
        if directed[i]["type"] not in BUILD_RUN_TYPES:
            i += 1
            continue
        j = i + 1
        while j < len(directed) and directed[j]["type"] == directed[i]["type"]:
            j += 1
        run = directed[i:j]
        if len(run) <= 1:
            i = j
            continue

        all_assets = []
        for beat in run:
            for asset in beat["assets"]:
                all_assets.append(dict(asset))
        anchors = _anchor_sequence(len(all_assets))
        for asset_index, asset in enumerate(all_assets):
            asset["anchor"] = anchors[min(asset_index, len(anchors) - 1)]

        cursor = 0
        cumulative = []
        for beat in run:
            new_count = len(beat["assets"])
            new_assets = [_new_asset(asset) for asset in all_assets[cursor : cursor + new_count]]
            beat["assets"] = [_settled_asset(asset) for asset in cumulative] + new_assets
            beat["new_count"] = new_count
            _rebuild_motion_for_new_assets(beat)
            cumulative.extend(new_assets)
            cursor += new_count
        i = j


def _attach_validated_blueprints(directed, sentences_timing, section):
    from artdirector_validator import validate_blueprint

    for beat in directed:
        blueprint = build_blueprint(beat, sentences_timing, section)
        repaired, repairs = validate_blueprint(blueprint, beat.get("scene_family", "object_stage"))
        beat["blueprint"] = repaired
        beat["validation"] = {
            "source": "rules",
            "warnings": [],
            "repairs": repairs,
        }


def _response_text(response):
    text = getattr(response, "text", None)
    if text:
        return text
    try:
        parts = response.candidates[0].content.parts
        return "".join(str(getattr(part, "text", "") or "") for part in parts)
    except Exception:
        return str(response)


def _extract_first_json_object(text):
    decoder = json.JSONDecoder()
    start = str(text or "").find("{")
    while start >= 0:
        try:
            obj, _ = decoder.raw_decode(str(text)[start:])
            if isinstance(obj, dict):
                return obj
        except ValueError:
            start = str(text).find("{", start + 1)
            continue
        break
    raise ValueError("No JSON object found in LLM response")


def _parse_llm_json(text):
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = _extract_first_json_object(text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON root must be an object")
    return parsed


def _sentence_payload(sentences_timing):
    sentences = []
    for i, sentence in enumerate(sentences_timing or []):
        sentences.append(
            {
                "index": i,
                "text": str(sentence.get("text", "")),
                "start": float(sentence.get("start", 0.0)),
                "end": float(sentence.get("end", 0.0)),
                "delivery": str(sentence.get("delivery", "neutral") or "neutral"),
            }
        )
    return sentences


def _input_beat_payload(beat, source_beat=None):
    source = source_beat if isinstance(source_beat, dict) else beat
    return {
        "id": str(beat.get("id", "")),
        "type": str(beat.get("type", "")),
        "sentence_start": int(source.get("sentence_start", 0) or 0),
        "sentence_end": int(source.get("sentence_end", source.get("sentence_start", 0)) or 0),
        "visual_intent": str(source.get("visual_intent", "") or ""),
        "text": str(source.get("text", beat.get("text", "")) or ""),
        "subjects": [str(s) for s in (source.get("subjects") or beat.get("subjects") or [])],
        "importance": str(source.get("importance", "medium") or "medium"),
        "comedy_role": str(source.get("comedy_role", "") or ""),
    }


def _valid_environment_id(value):
    env_id = str(value or "").strip()
    return env_id if env_id and has_environment(env_id) else None


def _llm_environment_description(section, beat=None):
    parts = []
    if isinstance(beat, dict):
        for overlay in beat.get("text_overlays") or []:
            if isinstance(overlay, dict) and str(overlay.get("text") or "").strip():
                parts.append(str(overlay.get("text")).strip())
        if str(beat.get("id") or "").strip():
            parts.append(str(beat.get("id")).strip())
    if isinstance(section, dict):
        parts.append(str(section.get("key_phrase") or "").strip())
        parts.append(str(section.get("narration") or "").strip()[:240])
    text = " ".join(part for part in parts if part)
    return text or None


def _resolve_llm_environment_id(value, description=None):
    env_id = str(value or "").strip()
    if not env_id:
        return None
    allow_create = os.environ.get("ENV_AUTOCREATE", "1").strip() != "0"
    return resolve_environment(env_id, description=description, allow_create=allow_create)


def _valid_environment_variant(value):
    variant = str(value or "").strip().lower()
    return variant if variant in ENVIRONMENT_VARIANTS else None


def _sanitize_actor_suggestions(actors, env_id, env_variant=""):
    if not isinstance(actors, list) or not env_id:
        return []
    try:
        slots = get_environment(env_id, variant=env_variant).get("slots") or {}
    except Exception:
        return []
    clean = []
    used_ids = set()
    for index, actor in enumerate(actors[:4]):
        if not isinstance(actor, dict):
            continue
        slot = str(actor.get("slot") or "").strip()
        if slot not in slots:
            continue
        asset = _norm_subject(actor.get("asset") or actor.get("name") or "person")
        if asset not in REGISTRY_ASSETS:
            asset = "person"
        item = {
            "id": _unique_actor_id(actor.get("id") or "%s_%d" % (asset, index + 1), used_ids),
            "asset": asset,
            "slot": slot,
        }
        pose = str(actor.get("pose") or "").strip().lower().replace(" ", "_")
        if pose:
            item["pose"] = pose
        color = actor.get("colorRole")
        if color in COLOR_ROLE:
            item["colorRole"] = color
        motion = actor.get("motion")
        if motion in MOTION_KIND_V2:
            item["motion"] = motion
        clean.append(item)
    return clean


def _unique_actor_id(raw, used_ids):
    base = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(raw or "actor"))
    while base and not base[0].isalpha():
        base = base[1:]
    base = (base or "actor")[:36]
    candidate = base
    suffix = 2
    while candidate in used_ids:
        candidate = ("%s_%d" % (base[:34], suffix))[:40]
        suffix += 1
    used_ids.add(candidate)
    return candidate


def _copy_rules_with_llm_blueprints(rules_section, llm_plan, sentences_timing):
    if not isinstance(llm_plan.get("beats"), list):
        raise ValueError("LLM response missing beats list")
    llm_by_id = {}
    for item in llm_plan.get("beats", []):
        if isinstance(item, dict):
            llm_by_id[str(item.get("id"))] = item
    rules_beats = rules_section.get("beats", []) or []
    actionable = [
        item
        for item in llm_by_id.values()
        if isinstance(item.get("blueprint"), dict)
        or isinstance(item.get("actors"), list)
        or bool(str(item.get("environment") or "").strip())
    ]
    if rules_beats and len(actionable) < max(1, (len(rules_beats) + 1) // 2):
        raise ValueError("LLM response missing most beats")
    merged = copy.deepcopy(rules_section)

    section_env = _resolve_llm_environment_id(llm_plan.get("environment"), _llm_environment_description(merged)) or _valid_environment_id(merged.get("environment"))
    section_variant = _valid_environment_variant(llm_plan.get("environment_variant")) or _valid_environment_variant(merged.get("environment_variant"))
    if section_env:
        merged["environment"] = section_env
        if section_variant:
            merged["environment_variant"] = section_variant
        else:
            merged.pop("environment_variant", None)

    for beat in merged.get("beats", []) or []:
        beat_id = str(beat.get("id"))
        suggestion = llm_by_id.get(beat_id)
        if suggestion:
            beat_env = _resolve_llm_environment_id(suggestion.get("environment"), _llm_environment_description(merged, beat)) or section_env
            beat_variant = _valid_environment_variant(suggestion.get("environment_variant")) or section_variant
            actors = _sanitize_actor_suggestions(suggestion.get("actors"), beat_env, beat_variant or "")
            if beat_env:
                beat["environment"] = beat_env
                beat["scene_family"] = "scene_stage"
                beat["layout"] = "wide_scene"
                beat["background"] = "plain"
                if beat_variant:
                    beat["environment_variant"] = beat_variant
                else:
                    beat.pop("environment_variant", None)
                if actors:
                    beat["actors"] = actors
                elif isinstance(beat.get("actors"), list):
                    beat.pop("actors", None)
                beat["blueprint"] = build_blueprint(beat, sentences_timing, merged)
            elif isinstance(suggestion.get("blueprint"), dict):
                beat["blueprint"] = suggestion["blueprint"]
            beat["validation"] = {"source": "llm", "warnings": [], "repairs": []}
            beat["_llm_blueprint_present"] = True
        else:
            beat["validation"] = {"source": "repaired_llm", "warnings": ["missing_llm_beat"], "repairs": []}
            beat["_llm_blueprint_present"] = False
    return merged


def direct_section_llm(section, sentences_timing, fps, index, catalog, client):
    from llm import llm_generate

    rules_section = direct_section_rules(section, sentences_timing, fps, index)
    source_by_id = {str(beat.get("id", "beat%d" % i)): beat for i, beat in enumerate(section.get("beats") or [])}
    duration = float(sentences_timing[-1]["end"]) if sentences_timing else 2.0
    payload = {
        "section_index": index,
        "fps": fps,
        "section_duration_frames": int(round(duration * fps)),
        "sentences": _sentence_payload(sentences_timing),
        "beats": [_input_beat_payload(beat, source_by_id.get(str(beat.get("id")))) for beat in (rules_section.get("beats") or [])],
        "capabilities": catalog,
    }
    prompt = _ART_DIRECTOR_PROMPT % json.dumps(payload, sort_keys=True, separators=(",", ":"))
    llm_plan = _parse_llm_json(llm_generate(prompt, tier="cheap", json_mode=True))
    return _copy_rules_with_llm_blueprints(rules_section, llm_plan, sentences_timing)


def log_artdirector_fallback(index, reason):
    print(
        json.dumps(
            {
                "event": "artdirector_fallback",
                "section_index": index,
                "reason": str(reason),
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        file=sys.stderr,
    )


def _stamp_validation_source(section_plan, source):
    stamped = copy.deepcopy(section_plan)
    for beat in stamped.get("beats", []) or []:
        validation = dict(beat.get("validation") or {})
        validation["source"] = source
        validation.setdefault("warnings", [])
        validation.setdefault("repairs", [])
        beat["validation"] = validation
    stamped["validation"] = {"source": source, "repairs": []}
    return stamped


def _validate_llm_with_rules_fallback(llm_section, rules_section):
    from artdirector_validator import validate_and_repair_section

    repaired = validate_and_repair_section(llm_section, source="llm")
    rules_by_id = {str(beat.get("id")): beat for beat in (rules_section.get("beats", []) or [])}
    for beat in repaired.get("beats", []) or []:
        beat_id = str(beat.get("id"))
        llm_present = beat.pop("_llm_blueprint_present", True)
        if not isinstance(beat.get("blueprint"), dict) and beat_id in rules_by_id:
            beat["blueprint"] = copy.deepcopy(rules_by_id[beat_id].get("blueprint"))
            beat["validation"] = {"source": "repaired_llm", "warnings": ["invalid_llm_blueprint"], "repairs": []}
        elif not llm_present and beat_id in rules_by_id:
            beat["blueprint"] = copy.deepcopy(rules_by_id[beat_id].get("blueprint"))
            validation = dict(beat.get("validation") or {})
            validation["source"] = "repaired_llm"
            warnings = list(validation.get("warnings") or [])
            if "missing_llm_beat" not in warnings:
                warnings.append("missing_llm_beat")
            validation["warnings"] = warnings
            validation.setdefault("repairs", [])
            beat["validation"] = validation
    return repaired


def direct_section_rules(section, sentences_timing, fps, index):
    """sentences_timing: list of {text,start,end,delivery} relative to the section start."""
    duration = float(sentences_timing[-1]["end"]) if sentences_timing else 2.0
    section_frames = int(round(duration * fps))
    environment_id = str(section.get("environment") or "").strip()
    if environment_id and not has_environment(environment_id):
        environment_id = None
    directed = []
    beats = section.get("beats") or []
    for i, beat in enumerate(beats):
        try:
            directed.append(_direct_beat(beat, sentences_timing, fps, is_first=(i == 0), beat_index=i, environment_id=environment_id))
        except Exception:
            continue
    if not directed:
        directed.append(_fallback_beat(section, sentences_timing, fps))

    # Tile beats so they cover the WHOLE section with no gaps. A gap between two
    # beats' frame windows renders as a blank frame, so each beat is stretched to
    # hold until the next one starts; the last beat holds to the section end.
    directed.sort(key=lambda b: b["startFrame"])
    if not environment_id:
        _apply_progressive_builds(directed)
    directed[0]["startFrame"] = 0
    for i in range(len(directed) - 1):
        directed[i]["endFrame"] = max(directed[i]["startFrame"] + 1, directed[i + 1]["startFrame"])
    directed[-1]["endFrame"] = max(directed[-1]["startFrame"] + 1, section_frames)
    for b in directed:
        b["start"] = round(b["startFrame"] / fps, 3)
        b["end"] = round(b["endFrame"] / fps, 3)
    _attach_validated_blueprints(directed, sentences_timing, section)

    section_plan = {
        "section_index": index,
        "durationInFrames": section_frames,
        "audioSrc": section.get("audioSrc", "") or "",
        "key_phrase": str(section.get("key_phrase", "")),
        "narration": section.get("narration", ""),
        "captions": sentences_timing,
        "beats": directed,
    }
    if environment_id:
        section_plan["environment"] = environment_id
    return section_plan


def direct_section(section, sentences_timing, fps, index, client=None):
    rules_section = direct_section_rules(section, sentences_timing, fps, index)
    if DIRECTOR_MODE != "llm":
        return rules_section
    try:
        catalog = build_capabilities_catalog()
        llm_section = direct_section_llm(section, sentences_timing, fps, index, catalog, client)
        return _validate_llm_with_rules_fallback(llm_section, rules_section)
    except Exception as e:
        log_artdirector_fallback(index, reason=str(e))
        return _stamp_validation_source(rules_section, "fallback_rules")


def build_episode(script, per_section_timings, fps=30, width=1920, height=1080, client=None):
    """per_section_timings: list (one per section) of sentence-timing lists."""
    sections = []
    for i, section in enumerate(script.get("sections", [])):
        timings = per_section_timings[i] if i < len(per_section_timings) else []
        sections.append(direct_section(section, timings, fps, i, client=client))
    return {
        "schema_version": 2,
        "fps": fps,
        "width": width,
        "height": height,
        "style_version": STYLE_VERSION,
        "sections": sections,
    }
