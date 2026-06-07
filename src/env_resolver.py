"""Resolve requested scene environments, optionally creating missing ones.

Imports are intentionally local and lightweight so test/import paths never touch
the network. Generation only happens when allow_create is true and an LLM key is
configured.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Iterable, Optional

from environments import get_environment, has_environment, reset_generated_cache


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

SAFE_FALLBACK_ENVIRONMENT = "classroom"
_LAST_RESOLUTION_EVENTS: Dict[str, Dict[str, Any]] = {}


def _clean_env_id(env_id: Any) -> Optional[str]:
    text = str(env_id or "").strip()
    return text or None


def _description_from_id(env_id: str) -> str:
    return str(env_id or "scene").replace("_", " ")


def _fallback_for_slots(slot_names: Iterable[str] | None = None) -> str:
    requested = {str(slot or "").strip() for slot in (slot_names or []) if str(slot or "").strip()}
    if requested:
        for candidate in ("classroom", "office", "courtroom", "newsroom"):
            try:
                slots = set((get_environment(candidate).get("slots") or {}).keys())
            except Exception:
                continue
            if requested & slots:
                return candidate
    return SAFE_FALLBACK_ENVIRONMENT


def _can_create() -> bool:
    try:
        import generate_environment

        return bool(generate_environment.has_configured_llm_key())
    except Exception:
        return False


def _generate(env_id: str, description: str) -> bool:
    try:
        import generate_environment

        generate_environment.generate_and_persist_environment(env_id, description)
        reset_generated_cache()
        return has_environment(env_id)
    except Exception as exc:
        print("ENV_RESOLVE FALLBACK requested=%s reason=%s" % (env_id, exc))
        reset_generated_cache()
        return False


def resolve_environment(env_id: Any, *, description: str | None = None, allow_create: bool = True, slots: Iterable[str] | None = None) -> Optional[str]:
    info = resolve_environment_info(env_id, description=description, allow_create=allow_create, slots=slots)
    return info["resolved"]


def resolve_environment_info(env_id: Any, *, description: str | None = None, allow_create: bool = True, slots: Iterable[str] | None = None) -> Dict[str, Any]:
    requested = _clean_env_id(env_id)
    if not requested:
        return {"requested": None, "resolved": None, "status": "none", "created": False}
    if has_environment(requested):
        return {"requested": requested, "resolved": requested, "status": "match", "created": False}

    clean_description = " ".join(str(description or "").split()) or _description_from_id(requested)
    if allow_create and _can_create() and _generate(requested, clean_description):
        return {"requested": requested, "resolved": requested, "status": "create", "created": True}

    fallback = _fallback_for_slots(slots)
    return {"requested": requested, "resolved": fallback, "status": "fallback", "created": False}


def ensure_environments(specs: Iterable[Dict[str, Any]] | None, *, allow_create: bool = True) -> Dict[str, Optional[str]]:
    global _LAST_RESOLUTION_EVENTS
    resolved: Dict[str, Optional[str]] = {}
    events: Dict[str, Dict[str, Any]] = {}
    seen = set()
    for spec in specs or []:
        if not isinstance(spec, dict):
            continue
        requested = _clean_env_id(spec.get("id"))
        if not requested or requested in seen:
            continue
        seen.add(requested)
        info = resolve_environment_info(
            requested,
            description=spec.get("description"),
            allow_create=allow_create,
            slots=spec.get("slots"),
        )
        resolved[requested] = info["resolved"]
        events[requested] = info
    _LAST_RESOLUTION_EVENTS = events
    return resolved


def last_resolution_events() -> Dict[str, Dict[str, Any]]:
    return dict(_LAST_RESOLUTION_EVENTS)
