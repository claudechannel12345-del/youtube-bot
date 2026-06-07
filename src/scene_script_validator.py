"""Scene script schema checks for authored environment sections.

This validator is intentionally stricter than the renderer fallback path. It
reports authoring mistakes early while leaving non-environment sections alone.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Set

from cutaway_vocab import COLOR_ROLE, MOTION_KIND_V2, REGISTRY_ASSETS
from environments import ENVIRONMENT_VARIANTS, get_environment, has_environment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_ASSETS_PATH = os.path.join(ROOT, "data", "generated_assets.json")

MAX_SCENE_ACTORS = 4
MAX_SCENE_TEXT_OVERLAYS = 1
SAFE_FALLBACK_ENVIRONMENT = "office"
ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{1,40}$")
POSES = frozenset(["idle", "arms_up", "pointing", "sitting", "walking", "left", "right", "lean"])
MOTION_ALIASES = frozenset(["idle", "idle_bob", "bob", "point", "pointing", "emphasize", "walk", "walking", "lean", "leaning", "none"])


def validate_scene_script(script: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate scene-script environment and actor declarations.

    Returns a flat issue list. Each issue has ``severity``, ``code``, ``path``,
    and ``message``. The input script is not modified.
    """
    issues: List[Dict[str, Any]] = []
    generated_assets = _generated_asset_names()
    checked_set_props: Set[str] = set()

    sections = script.get("sections") if isinstance(script, dict) else None
    if not isinstance(sections, list):
        return [_issue("error", "missing_sections", "sections", "script must contain a sections list")]

    for section_index, section in enumerate(sections):
        section_path = "sections[%d]" % section_index
        if not isinstance(section, dict):
            issues.append(_issue("error", "bad_section", section_path, "section must be an object"))
            continue

        section_env = _environment_id(section.get("environment"))
        section_variant = _variant_id(section.get("environment_variant"))
        _validate_environment_ref(section.get("environment"), section_path + ".environment", issues)
        _validate_variant_ref(section.get("environment_variant"), section_path + ".environment_variant", issues)

        beats = section.get("beats")
        if not isinstance(beats, list):
            issues.append(_issue("error", "missing_beats", section_path + ".beats", "section must contain a beats list"))
            continue

        for beat_index, beat in enumerate(beats):
            beat_path = "%s.beats[%d]" % (section_path, beat_index)
            if not isinstance(beat, dict):
                issues.append(_issue("error", "bad_beat", beat_path, "beat must be an object"))
                continue
            beat_env = _environment_id(beat.get("environment")) or section_env
            beat_variant = _variant_id(beat.get("environment_variant")) or section_variant
            _validate_environment_ref(beat.get("environment"), beat_path + ".environment", issues)
            _validate_variant_ref(beat.get("environment_variant"), beat_path + ".environment_variant", issues)

            actors = beat.get("actors")
            if actors is not None:
                _validate_actors(actors, beat_env, beat_variant, beat_path + ".actors", generated_assets, issues)
            elif beat_env:
                issues.append(
                    _issue(
                        "warning",
                        "scene_actors_missing",
                        beat_path + ".actors",
                        "environment beat has no actors; renderer will synthesize a fallback person or assets",
                    )
                )

            if beat_env:
                env_key = "%s:%s" % (beat_env, beat_variant or "")
                if env_key not in checked_set_props:
                    checked_set_props.add(env_key)
                    _validate_environment_set_props(beat_env, beat_variant, "environment[%s].set_props" % env_key, generated_assets, issues)
                _validate_scene_text_limits(beat, beat_path, issues)

    return issues


def has_errors(issues: Iterable[Dict[str, Any]]) -> bool:
    return any(issue.get("severity") == "error" for issue in issues)


def format_issues(issues: Iterable[Dict[str, Any]]) -> str:
    lines = []
    for issue in issues:
        lines.append(
            "%s %s %s: %s"
            % (
                str(issue.get("severity", "")).upper(),
                issue.get("code", "issue"),
                issue.get("path", ""),
                issue.get("message", ""),
            )
        )
    return "\n".join(lines)


def _validate_environment_ref(value: Any, path: str, issues: List[Dict[str, Any]]) -> None:
    if value is None:
        return
    env_id = str(value or "").split(":", 1)[0].strip()
    if not env_id:
        issues.append(_issue("error", "empty_environment", path, "environment must be a non-empty id or omitted"))
    elif not has_environment(env_id):
        issues.append(_issue("warning", "unknown_environment", path, "unknown environment '%s'; validator will use '%s' for slot checks" % (env_id, _safe_environment())))


def _validate_variant_ref(value: Any, path: str, issues: List[Dict[str, Any]]) -> None:
    if value is None:
        return
    variant = str(value or "").strip().lower()
    if not variant:
        issues.append(_issue("error", "empty_environment_variant", path, "environment_variant must be non-empty or omitted"))
    elif variant not in ENVIRONMENT_VARIANTS:
        issues.append(_issue("error", "unknown_environment_variant", path, "unknown environment variant '%s'" % variant))


def _validate_actors(
    actors: Any,
    env_id: Optional[str],
    variant: Optional[str],
    path: str,
    generated_assets: Set[str],
    issues: List[Dict[str, Any]],
) -> None:
    if not env_id:
        issues.append(_issue("error", "actors_without_environment", path, "actors require a section or beat environment"))
        return
    if not isinstance(actors, list):
        issues.append(_issue("error", "actors_not_list", path, "actors must be a list"))
        return
    if len(actors) > MAX_SCENE_ACTORS:
        issues.append(_issue("error", "too_many_actors", path, "scene_stage supports at most %d actors" % MAX_SCENE_ACTORS))

    slots = get_environment(env_id, variant=variant or "").get("slots") or {}
    seen_ids: Set[str] = set()
    for index, actor in enumerate(actors):
        actor_path = "%s[%d]" % (path, index)
        if not isinstance(actor, dict):
            issues.append(_issue("error", "bad_actor", actor_path, "actor must be an object"))
            continue
        actor_id = actor.get("id")
        if actor_id is not None:
            clean_id = str(actor_id)
            if not ID_RE.match(clean_id):
                issues.append(_issue("error", "bad_actor_id", actor_path + ".id", "actor id must match %s" % ID_RE.pattern))
            elif clean_id in seen_ids:
                issues.append(_issue("error", "duplicate_actor_id", actor_path + ".id", "actor id '%s' is duplicated" % clean_id))
            seen_ids.add(clean_id)
        asset = str(actor.get("asset") or actor.get("name") or "person").strip().lower().replace(" ", "_")
        if asset not in REGISTRY_ASSETS and asset not in generated_assets:
            issues.append(_issue("error", "unknown_actor_asset", actor_path + ".asset", "unknown actor asset '%s'" % asset))
        slot = str(actor.get("slot") or "").strip()
        if slot not in slots:
            issues.append(_issue("error", "unknown_actor_slot", actor_path + ".slot", "slot '%s' is not in environment '%s'" % (slot, env_id)))
        color = actor.get("colorRole")
        if color is not None and color not in COLOR_ROLE:
            issues.append(_issue("error", "unknown_actor_color", actor_path + ".colorRole", "unknown color role '%s'" % color))
        pose = str(actor.get("pose") or "").strip().lower().replace(" ", "_")
        if pose and pose not in POSES:
            issues.append(_issue("error", "unknown_actor_pose", actor_path + ".pose", "unknown actor pose '%s'" % pose))
        motion = actor.get("motion")
        if isinstance(motion, str):
            motion_id = motion.strip().lower().replace(" ", "_")
            if motion_id and motion_id not in MOTION_KIND_V2 and motion_id not in MOTION_ALIASES:
                issues.append(_issue("error", "unknown_actor_motion", actor_path + ".motion", "unknown actor motion '%s'" % motion_id))
        elif motion is not None and not isinstance(motion, list):
            issues.append(_issue("error", "bad_actor_motion", actor_path + ".motion", "motion must be a string, list, or omitted"))


def _validate_scene_text_limits(beat: Dict[str, Any], beat_path: str, issues: List[Dict[str, Any]]) -> None:
    overlays = [item for item in beat.get("text_overlays", []) or [] if isinstance(item, dict) and str(item.get("text") or "").strip()]
    if len(overlays) > MAX_SCENE_TEXT_OVERLAYS:
        issues.append(_issue("warning", "too_many_scene_text_overlays", beat_path + ".text_overlays", "scene_stage uses only one text overlay in the environment text_zone"))
    for index, overlay in enumerate(overlays):
        role = overlay.get("role")
        if role not in ("stat", "caption", "stamp", "headline", "label", "tiny_note"):
            issues.append(_issue("warning", "scene_text_role_unusual", "%s.text_overlays[%d].role" % (beat_path, index), "scene text role '%s' may be dropped or repaired" % role))


def _validate_environment_set_props(
    env_id: str,
    variant: Optional[str],
    path: str,
    generated_assets: Set[str],
    issues: List[Dict[str, Any]],
) -> None:
    props = get_environment(env_id, variant=variant or "").get("set_props") or []
    if not isinstance(props, list):
        issues.append(_issue("error", "bad_environment_set_props", path, "set_props must be a list when present"))
        return
    for index, prop in enumerate(props):
        prop_path = "%s[%d]" % (path, index)
        if not isinstance(prop, dict):
            issues.append(_issue("error", "bad_environment_set_prop", prop_path, "set_prop must be an object"))
            continue
        asset = str(prop.get("asset") or prop.get("name") or "").strip().lower().replace(" ", "_")
        if asset not in REGISTRY_ASSETS and asset not in generated_assets:
            issues.append(_issue("error", "unknown_environment_set_prop_asset", prop_path + ".asset", "unknown set_prop asset '%s'" % asset))


def _environment_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    env_id = str(value or "").split(":", 1)[0].strip()
    if env_id and has_environment(env_id):
        return env_id
    return _safe_environment() if env_id else None


def _safe_environment() -> str:
    return SAFE_FALLBACK_ENVIRONMENT if has_environment(SAFE_FALLBACK_ENVIRONMENT) else "arena"


def _variant_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    variant = str(value or "").strip().lower()
    return variant if variant in ENVIRONMENT_VARIANTS else None


def _generated_asset_names() -> Set[str]:
    try:
        with open(GENERATED_ASSETS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return set()
    if not isinstance(data, dict):
        return set()
    return {str(name).strip() for name, asset in data.items() if isinstance(asset, dict) and isinstance(asset.get("shapes"), list)}


def _issue(severity: str, code: str, path: str, message: str) -> Dict[str, str]:
    return {"severity": severity, "code": code, "path": path, "message": message}


def _main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("usage: py -m scene_script_validator path/to/script.json", file=sys.stderr)
        return 2
    with open(argv[1], "r", encoding="utf-8") as f:
        script = json.load(f)
    issues = validate_scene_script(script)
    if issues:
        print(format_issues(issues))
    else:
        print("OK scene script schema")
    return 1 if has_errors(issues) else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
