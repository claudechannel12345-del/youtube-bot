from environments import ENVIRONMENTS, ENVIRONMENT_VARIANTS, all_environment_slot_ids

BEAT_TYPES = frozenset(
    [
        "establish",
        "illustrate",
        "stat_pop",
        "compare",
        "diagram_build",
        "process",
        "map_focus",
        "list_reveal",
        "quote",
        "cutaway_gag",
        "emphasize",
        "transition",
    ]
)

IMPORTANCE = frozenset(["low", "medium", "high", "must_hit"])

COMEDY_ROLES = frozenset(
    [
        "deadpan_literalization",
        "scale_absurdity",
        "bureaucracy_metaphor",
        "wrong_tool",
        "overly_literal_label",
        "quiet_contradiction",
    ]
)

SCENE_FAMILY = frozenset(
    [
        "title_stage",
        "object_stage",
        "diagram_stage",
        "map_stage",
        "comparison_stage",
        "timeline_stage",
        "list_stage",
        "stat_stage",
        "paperwork_stage",
        "miniature_world",
        "quote_stage",
        "caption_punch",
    ]
)

LAYOUT = frozenset(
    [
        "center_subject",
        "left_right",
        "top_down_stack",
        "radial",
        "map_focus",
        "timeline_horizontal",
        "three_panel",
        "paper_stack",
        "wide_scene",
        "quote_card",
        "caption_only",
    ]
)

CAMERA_MOVE = frozenset(
    [
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
)

CAMERA_INTENSITY = frozenset(["none", "small", "medium", "large"])

TRANSITION = frozenset(
    [
        "hard_cut",
        "pop_cut",
        "wipe_left",
        "wipe_right",
        "match_cut",
        "smash_cut",
        "dip_to_bg",
    ]
)

ASSET_KIND = frozenset(
    [
        "prop",
        "icon",
        "icon_cluster",
        "figure",
        "label",
        "connector",
        "map_shape",
        "chart",
        "panel",
        "stamp",
        "texture",
    ]
)

MOTION_KIND = frozenset(
    [
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
    ]
)

BLUEPRINT_ELEMENT_KIND = frozenset(
    [
        "prop",
        "label",
        "headline",
        "caption",
        "stat",
        "quote",
        "title",
        "tiny_note",
        "stamp",
        "panel",
        "connector",
        "map_shape",
        "chart",
        "texture",
        "generated_image",
    ]
)

GENERATED_IMAGE_ENABLED = False

MOTION_KIND_V2 = MOTION_KIND | frozenset(
    [
        "enter",
        "hold",
        "exit",
        "connect_to",
        "count",
        "draw_path",
        "highlight",
    ]
)

POSITION_MODE = frozenset(["point", "anchor"])

SIZE_MODE = frozenset(["scale", "box"])

CONNECTION_KIND = frozenset(["line", "arrow", "range_ring", "pulse", "brace"])

BACKGROUND_TREATMENT = frozenset(
    [
        "plain",
        "panel",
        "grid",
        "map",
        "comparison_panels",
        "paper_stack",
    ]
)

ENVIRONMENT_SLOTS = all_environment_slot_ids()

EASING = frozenset(["linear", "spring", "ease_out", "ease_in_out"])

COLOR_ROLE = frozenset(
    [
        "ink",
        "accent",
        "blue",
        "green",
        "yellow",
        "lavender",
        "muted",
        "white",
        "paper",
        "paper_deep",
    ]
)

REGISTRY_ASSETS = frozenset(
    [
        "person",
        "phone",
        "city",
        "building",
        "clock",
        "atomic_clock",
        "satellite",
        "signal",
        "signal_beam",
        "earth",
        "map_pin",
        "dot",
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
        "gavel", "document", "eye",
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
)

TEXT_ROLE = frozenset(
    [
        "headline",
        "label",
        "caption",
        "quote",
        "stat",
        "stamp",
        "callout",
        "title",
        "tiny_note",
    ]
)

BEAT_TO_SCENE_FAMILY = {
    "establish": "object_stage",
    "illustrate": "object_stage",
    "stat_pop": "stat_stage",
    "compare": "comparison_stage",
    "diagram_build": "diagram_stage",
    "process": "list_stage",
    "map_focus": "map_stage",
    "list_reveal": "list_stage",
    "quote": "quote_stage",
    "cutaway_gag": "miniature_world",
    "emphasize": "caption_punch",
    "transition": "caption_punch",
}


def coerce_beat_type(x):
    if x in BEAT_TYPES:
        return x
    return "illustrate"


def is_valid(vocab_set, x):
    return x in vocab_set
