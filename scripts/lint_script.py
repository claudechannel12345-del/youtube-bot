"""Lint an authored script JSON before rendering.

This is an offline authoring report. It checks the scene-script schema, keeps
non-environment sections legal, verifies narration/sentence consistency, and
prints environment/slot/asset usage so mistakes are easy to spot before a
Remotion render.

Usage:
  py scripts/lint_script.py data/color_script_scenes.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from cutaway_vocab import REGISTRY_ASSETS  # noqa: E402
from environments import ENVIRONMENT_VARIANTS, ENVIRONMENTS, get_environment, has_environment  # noqa: E402
from scene_script_validator import format_issues, has_errors, validate_scene_script  # noqa: E402


def _load_script(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("script root must be an object")
    return data


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _environment_id(value: Any) -> str:
    return str(value or "").split(":", 1)[0].strip()


def _inline_variant(value: Any) -> str:
    raw = str(value or "").strip()
    if ":" not in raw:
        return ""
    return raw.split(":", 1)[1].strip().lower()


def _effective_env(section: Dict[str, Any], beat: Dict[str, Any]) -> Tuple[str, str]:
    env = _environment_id(beat.get("environment")) or _environment_id(section.get("environment"))
    variant = (
        str(beat.get("environment_variant") or "").strip().lower()
        or _inline_variant(beat.get("environment"))
        or str(section.get("environment_variant") or "").strip().lower()
        or _inline_variant(section.get("environment"))
    )
    return env, variant if variant in ENVIRONMENT_VARIANTS else ""


def _sentence_concat_issues(script: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for sidx, section in enumerate(script.get("sections") or []):
        if not isinstance(section, dict):
            continue
        sentences = section.get("sentences")
        narration = section.get("narration")
        if not isinstance(sentences, list) or narration is None:
            continue
        joined = _norm_text(" ".join(str(item.get("text", "")) for item in sentences if isinstance(item, dict)))
        expected = _norm_text(narration)
        if joined and expected and joined != expected:
            issues.append(
                {
                    "severity": "error",
                    "code": "narration_sentence_mismatch",
                    "path": "sections[%d].sentences" % sidx,
                    "message": "joined sentence text does not match section narration",
                }
            )
    return issues


def _beat_span_issues(script: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for sidx, section in enumerate(script.get("sections") or []):
        if not isinstance(section, dict):
            continue
        sentence_count = len(section.get("sentences") or [])
        for bidx, beat in enumerate(section.get("beats") or []):
            if not isinstance(beat, dict):
                continue
            start = beat.get("sentence_start")
            end = beat.get("sentence_end")
            if start is None and end is None:
                continue
            path = "sections[%d].beats[%d]" % (sidx, bidx)
            try:
                istart = int(start if start is not None else 0)
                iend = int(end if end is not None else istart)
            except Exception:
                issues.append({"severity": "error", "code": "bad_sentence_span", "path": path, "message": "sentence_start/end must be integers"})
                continue
            if iend < istart:
                issues.append({"severity": "error", "code": "bad_sentence_span", "path": path, "message": "sentence_end is before sentence_start"})
            if sentence_count and (istart < 0 or iend >= sentence_count):
                issues.append({"severity": "error", "code": "sentence_span_out_of_range", "path": path, "message": "sentence span is outside section sentences"})
    return issues


def _collect_usage(script: Dict[str, Any]) -> Dict[str, Any]:
    env_counts: Counter[str] = Counter()
    variant_counts: Counter[str] = Counter()
    slot_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    asset_counts: Counter[str] = Counter()
    non_env_sections = 0
    scene_text_counts: Counter[str] = Counter()

    for section in script.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section_has_env = bool(_environment_id(section.get("environment")))
        if not section_has_env:
            non_env_sections += 1
        for beat in section.get("beats") or []:
            if not isinstance(beat, dict):
                continue
            env_id, variant = _effective_env(section, beat)
            if env_id:
                env_counts[env_id] += 1
                if variant:
                    variant_counts[variant] += 1
                overlays = [item for item in beat.get("text_overlays", []) or [] if isinstance(item, dict) and str(item.get("text") or "").strip()]
                scene_text_counts[env_id] += len(overlays)
            for actor in beat.get("actors") or []:
                if not isinstance(actor, dict):
                    continue
                asset = str(actor.get("asset") or actor.get("name") or "person").strip().lower().replace(" ", "_")
                slot = str(actor.get("slot") or "").strip()
                if asset:
                    asset_counts[asset] += 1
                if env_id and slot:
                    slot_counts[env_id][slot] += 1
    return {
        "env_counts": env_counts,
        "variant_counts": variant_counts,
        "slot_counts": slot_counts,
        "asset_counts": asset_counts,
        "non_env_sections": non_env_sections,
        "scene_text_counts": scene_text_counts,
    }


def _inventory_lines() -> List[str]:
    lines = ["Available environments: %d" % len(ENVIRONMENTS)]
    for env_id in sorted(ENVIRONMENTS):
        env = get_environment(env_id)
        slots = ", ".join(sorted((env.get("slots") or {}).keys()))
        zone = env.get("text_zone") or {}
        lines.append(
            "  - %s: slots [%s], text_zone x=%s y=%s w=%s h=%s"
            % (env_id, slots, zone.get("x"), zone.get("y"), zone.get("w"), zone.get("h"))
        )
    return lines


def _usage_lines(usage: Dict[str, Any]) -> List[str]:
    lines = []
    env_counts: Counter[str] = usage["env_counts"]
    lines.append("Environment beats: %d" % sum(env_counts.values()))
    if env_counts:
        for env_id, count in sorted(env_counts.items()):
            status = "known" if has_environment(env_id) else "unknown"
            lines.append("  - %s: %d beats (%s)" % (env_id, count, status))
            slots = usage["slot_counts"].get(env_id) or {}
            if slots:
                lines.append("    slots: " + ", ".join("%s=%d" % (slot, n) for slot, n in sorted(slots.items())))
    lines.append("Non-environment sections: %d" % usage["non_env_sections"])
    if usage["variant_counts"]:
        lines.append("Variants: " + ", ".join("%s=%d" % item for item in sorted(usage["variant_counts"].items())))
    if usage["asset_counts"]:
        known = sum(count for asset, count in usage["asset_counts"].items() if asset in REGISTRY_ASSETS)
        total = sum(usage["asset_counts"].values())
        lines.append("Actor assets: %d references, %d known registry references" % (total, known))
    return lines


def _print_section(title: str, lines: Iterable[str]) -> None:
    print(title)
    for line in lines:
        print(line)


def lint_script(script: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    issues.extend(validate_scene_script(script))
    issues.extend(_sentence_concat_issues(script))
    issues.extend(_beat_span_issues(script))
    return issues


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate a script JSON and print an environment report.")
    parser.add_argument("script", help="path to script JSON")
    parser.add_argument("--inventory", action="store_true", help="also print all known environments and slots")
    args = parser.parse_args(argv[1:])

    script_path = args.script if os.path.isabs(args.script) else os.path.join(ROOT, args.script)
    script = _load_script(script_path)
    sections = script.get("sections") if isinstance(script.get("sections"), list) else []
    beats = sum(len(section.get("beats") or []) for section in sections if isinstance(section, dict))
    issues = lint_script(script)
    usage = _collect_usage(script)

    print("SCRIPT LINT REPORT")
    print("path: %s" % script_path)
    print("sections: %d" % len(sections))
    print("beats: %d" % beats)
    print("")
    _print_section("USAGE", _usage_lines(usage))
    print("")
    if args.inventory:
        _print_section("ENVIRONMENT INVENTORY", _inventory_lines())
        print("")
    if issues:
        _print_section("ISSUES", [format_issues(issues)])
    else:
        print("ISSUES")
        print("OK")
    return 1 if has_errors(issues) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
