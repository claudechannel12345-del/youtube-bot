"""Focused scene/environment contract tests.

Run directly:
  py tests/test_scene_contracts.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from artdirector_validator import validate_blueprint  # noqa: E402
import artdirector_validator  # noqa: E402
from blueprint_presets import build_blueprint, build_scene_stage  # noqa: E402
import blueprint_presets  # noqa: E402
from cutaway_vocab import ENVIRONMENTS, ENVIRONMENT_SLOTS  # noqa: E402
import environments  # noqa: E402
from environments import ENVIRONMENT_BUILDERS, get_environment  # noqa: E402
import env_resolver  # noqa: E402
import generate_environment  # noqa: E402
from scene_script_validator import has_errors, validate_scene_script  # noqa: E402
import src.llm as src_llm  # noqa: E402


def test_environment_contracts_and_slots():
    assert len(ENVIRONMENT_BUILDERS) == 31
    for env_id in ENVIRONMENT_BUILDERS:
        env = get_environment(env_id)
        assert env["id"] == env_id
        assert env.get("backdrop")
        assert env.get("midground")
        assert env.get("foreground")
        assert env.get("text_zone")
        assert env.get("slots")
        for slot_id, slot in env["slots"].items():
            assert slot_id in ENVIRONMENT_SLOTS
            assert 0 <= slot["x"] <= 1920
            assert 0 <= slot["y"] <= 1080
            assert slot.get("scale", 0) > 0


def test_scene_stage_safe_area_clamps():
    safe_top = 64
    safe_bottom = 48
    env_ids = list(ENVIRONMENT_BUILDERS) + list(environments.load_generated_environments())
    for env_id in env_ids:
        env = get_environment(env_id)
        zone = env["text_zone"]
        assert zone["y"] >= safe_top, (env_id, zone)
        assert zone["y"] + zone["h"] <= 1080 - safe_bottom, (env_id, zone)
        for slot_name, slot in env["slots"].items():
            assert safe_top <= slot["y"] <= 1080 - safe_bottom, (env_id, slot_name, slot)
            scene_bp = build_scene_stage(
                {
                    "id": "safe_%s_%s" % (env_id, slot_name),
                    "environment": env_id,
                    "actors": [{"id": "actor1", "asset": "person", "slot": slot_name}],
                    "text_overlays": [{"role": "headline", "text": "SAFE TEXT"}],
                },
                [],
                {},
            )
            actor = next(element for element in scene_bp["elements"] if element.get("id") == "actor1")
            actor_w, actor_h = blueprint_presets._scene_asset_base_size(actor.get("asset"))
            actor_scale = actor.get("size", {}).get("scale", 1.0)
            assert actor["position"]["y"] + actor_h * actor_scale / 2 <= 1080 - safe_bottom + 0.001, (env_id, slot_name, actor)
            assert actor["position"]["y"] - actor_h * actor_scale / 2 >= safe_top - 0.001, (env_id, slot_name, actor)
        for prop in env.get("set_props") or []:
            assert safe_top <= prop["y"] <= 1080 - safe_bottom, (env_id, prop)
        scene_bp = build_scene_stage(
            {
                "id": "safe_%s_props" % env_id,
                "environment": env_id,
                "text_overlays": [{"role": "headline", "text": "SAFE TEXT"}],
            },
            [],
            {},
        )
        text = next(element for element in scene_bp["elements"] if element.get("id") == "scene_text")
        assert text["position"]["y"] - text["size"]["h"] / 2 >= safe_top, (env_id, text)
        for element in scene_bp["elements"]:
            if not element.get("setProp"):
                continue
            asset_name = element.get("generatedAssetName") or element.get("asset")
            prop_w, prop_h = blueprint_presets._scene_asset_base_size(asset_name)
            scale = element.get("size", {}).get("scale", 1.0)
            assert element["position"]["y"] + prop_h * scale / 2 <= 1080 - safe_bottom + 0.001, (env_id, element)
            assert element["position"]["y"] - prop_h * scale / 2 >= safe_top - 0.001, (env_id, element)


def test_scene_script_validator_legal_and_illegal_slots():
    legal = {
        "sections": [
            {
                "environment": "arena",
                "beats": [
                    {
                        "id": "b1",
                        "actors": [
                            {"id": "red", "asset": "person", "slot": "red_corner", "colorRole": "accent"},
                            {"id": "blue", "asset": "person", "slot": "blue_corner", "colorRole": "blue"},
                        ],
                        "text_overlays": [{"role": "headline", "text": "RED WINS"}],
                    }
                ],
            }
        ]
    }
    assert not has_errors(validate_scene_script(legal))

    illegal = {
        "sections": [
            {
                "environment": "arena",
                "beats": [
                    {
                        "id": "b1",
                        "actors": [{"id": "bad", "asset": "person", "slot": "judge_bench"}],
                    }
                ],
            }
        ]
    }
    issues = validate_scene_script(illegal)
    assert has_errors(issues)
    assert any(issue["code"] == "unknown_actor_slot" for issue in issues)


def test_generated_environment_loaded_from_data_and_scene_stage():
    generated_env = _generated_env_fixture("generated_room")
    with _temporary_generated_env_store({"generated_room": generated_env}):
        assert environments.has_environment("generated_room")
        env = get_environment("generated_room")
        assert env["id"] == "generated_room"
        assert env["backdrop"][0]["x"] == 0
        assert env["midground"] == []
        assert env["foreground"] == []
        assert set(env["slots"]) == {"host", "guest"}
        assert env["slot_docs"]["host"]["role"] == "foreground"

        scene_bp = build_scene_stage(
            {
                "id": "generated_scene",
                "environment": "generated_room",
                "actors": [{"id": "h", "asset": "person", "slot": "host"}],
                "text_overlays": [{"role": "headline", "text": "CLEAR"}],
            },
            [],
            {},
        )
        assert scene_bp["preset"] == "scene_stage"
        assert scene_bp["environment"] == "generated_room"
        assert any(element.get("setProp") and element.get("asset") == "plant" for element in scene_bp["elements"])


def test_generated_environment_validation_text_zone_and_fake_prop():
    generated_env = _generated_env_fixture("fake_prop_room")
    generated_env["set_props"] = [
        {"asset": "fake_countertop", "x": 1420, "y": 735, "scale": 0.5, "z": 130},
        {"asset": "plant", "x": 1510, "y": 760, "scale": 0.42, "z": 132},
    ]
    with _temporary_generated_assets({"fake_countertop": {"description": "fake prop", "shapes": [{"type": "circle", "cx": 0, "cy": 0, "r": 20, "fill": "accent"}]}}):
        valid = generate_environment.validate_environment(generated_env)
        assert valid["set_props"][0]["asset"] == "fake_countertop"
        with _temporary_generated_env_store({"fake_prop_room": valid}):
            script = {
                "sections": [
                    {
                        "environment": "fake_prop_room",
                        "beats": [{"id": "b1", "actors": [{"id": "actor1", "asset": "person", "slot": "host"}]}],
                    }
                ]
            }
            assert not has_errors(validate_scene_script(script))
            repaired, repairs = validate_blueprint(
                {
                    "version": 1,
                    "intent": "generated set prop",
                    "background": {"treatment": "plain"},
                    "camera": {"move": "static", "target": "center", "intensity": "none"},
                    "environment": "fake_prop_room",
                    "elements": [
                        {
                            "id": "counter",
                            "kind": "prop",
                            "asset": "fake_countertop",
                            "setProp": True,
                            "position": {"mode": "point", "x": 1420, "y": 735},
                            "size": {"mode": "scale", "scale": 0.5},
                            "z": 500,
                        }
                    ],
                    "connections": [],
                },
                "scene_stage",
            )
            assert repaired["elements"][0]["generatedAssetName"] == "fake_countertop"
            assert repaired["elements"][0]["z"] == 160
            assert any(repair["code"] == "scene_set_prop_z_repaired" for repair in repairs)

    bad = _generated_env_fixture("bad_text_room")
    bad["text_zone"] = {"x": 850, "y": 700, "w": 220, "h": 100}
    try:
        generate_environment.validate_environment(bad)
    except ValueError as exc:
        assert "overlaps text_zone" in str(exc)
    else:
        raise AssertionError("expected text_zone overlap validation to fail")


def test_unknown_environment_falls_back_safely():
    script = {
        "sections": [
            {
                "environment": "not_a_real_env",
                "beats": [{"id": "b1", "actors": [{"id": "actor1", "asset": "person", "slot": "person_behind_desk"}]}],
            }
        ]
    }
    issues = validate_scene_script(script)
    assert not has_errors(issues)
    assert any(issue["code"] == "unknown_environment" and issue["severity"] == "warning" for issue in issues)

    repaired, repairs = validate_blueprint(
        {
            "version": 1,
            "intent": "bad env",
            "background": {"treatment": "plain"},
            "camera": {"move": "static", "target": "center", "intensity": "none"},
            "environment": "not_a_real_env",
            "elements": [{"id": "actor", "kind": "prop", "asset": "person", "slot": "missing", "position": {"mode": "point", "x": 960, "y": 720}, "size": {"mode": "scale", "scale": 1.0}}],
            "connections": [],
        },
        "scene_stage",
    )
    assert repaired["environment"] == artdirector_validator.SAFE_FALLBACK_ENVIRONMENT
    assert any(repair["code"] == "unknown_environment" for repair in repairs)


def test_blueprint_validator_repairs_illegal_blueprint():
    repaired, repairs = validate_blueprint(
        {
            "version": 99,
            "intent": None,
            "background": {"treatment": "sparkles"},
            "camera": {"move": "teleport", "target": "void", "intensity": "huge"},
            "elements": [
                {
                    "id": "1bad",
                    "kind": "prop",
                    "asset": "missing_asset",
                    "position": {"mode": "point", "x": -100, "y": 2000},
                    "size": {"mode": "scale", "scale": 9},
                    "colorRole": "neon",
                }
            ],
            "connections": [],
        },
        "object_stage",
    )
    assert repaired["version"] == 1
    assert repaired["background"]["treatment"] == "plain"
    assert repaired["camera"]["move"] == "static"
    assert repaired["elements"][0]["asset"] == "generic_object"
    assert repairs


def test_scene_stage_and_non_environment_back_compat():
    section = {"key_phrase": "TEST", "environment": "arena"}
    beat = {
        "id": "scene",
        "type": "emphasize",
        "environment": "arena",
        "actors": [{"id": "red", "asset": "person", "slot": "red_corner", "colorRole": "accent"}],
        "text_overlays": [{"role": "headline", "text": "CLEAR TEXT"}],
    }
    scene_bp = build_scene_stage(beat, [], section)
    assert scene_bp["preset"] == "scene_stage"
    assert scene_bp["environment"] == "arena"
    assert any(element.get("slot") == "red_corner" for element in scene_bp["elements"])
    assert any(element.get("text", {}).get("text") == "CLEAR TEXT" and element.get("asset") == "none" for element in scene_bp["elements"])

    plain_bp = build_blueprint(
        {
            "id": "plain",
            "type": "emphasize",
            "scene_family": "caption_punch",
            "text_overlays": [{"role": "headline", "text": "OLD WAY"}],
            "assets": [],
        },
        [],
        {"key_phrase": "OLD WAY"},
    )
    assert plain_bp["preset"] == "caption_punch"
    assert "environment" not in plain_bp


def test_llm_generate_callable_with_fake_openai():
    original = src_llm._generate_openai
    try:
        src_llm._generate_openai = lambda prompt, *, tier, json_mode: '{"ok": true}'
        assert src_llm.llm_generate("offline smoke", provider="openai", json_mode=True) == '{"ok": true}'
    finally:
        src_llm._generate_openai = original


def test_env_resolver_match_and_fallback_offline():
    assert env_resolver.resolve_environment("classroom", allow_create=False) == "classroom"
    fallback = env_resolver.resolve_environment("missing_env_for_offline_test", allow_create=False)
    assert fallback in ENVIRONMENT_BUILDERS
    assert environments.has_environment(fallback)
    assert env_resolver.resolve_environment(None, allow_create=False) is None


def test_env_resolver_ensure_de_dupes():
    original = env_resolver.resolve_environment_info
    calls = []

    def fake_resolve(env_id, **kwargs):
        calls.append(env_id)
        return {"requested": env_id, "resolved": "classroom", "status": "fallback", "created": False}

    try:
        env_resolver.resolve_environment_info = fake_resolve
        result = env_resolver.ensure_environments(
            [
                {"id": "duplicate_room", "description": "first"},
                {"id": "duplicate_room", "description": "second"},
                {"id": "other_room", "description": "third"},
            ],
            allow_create=False,
        )
        assert calls == ["duplicate_room", "other_room"]
        assert result == {"duplicate_room": "classroom", "other_room": "classroom"}
    finally:
        env_resolver.resolve_environment_info = original


def test_env_resolver_fake_create_persists_and_resets_cache():
    original_has_key = generate_environment.has_configured_llm_key
    original_generate = generate_environment.generate_and_persist_environment
    new_id = "resolver_created_room"

    def fake_generate(name, description, force=False):
        generated = _generated_env_fixture(name)
        generated["description"] = description
        data = {}
        try:
            import json

            with open(environments.GENERATED_ENVIRONMENTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data[name] = generated
        os.makedirs(os.path.dirname(environments.GENERATED_ENVIRONMENTS_PATH), exist_ok=True)
        with open(environments.GENERATED_ENVIRONMENTS_PATH, "w", encoding="utf-8") as f:
            import json

            json.dump(data, f, indent=2, sort_keys=True)
        return generated

    with _temporary_generated_env_store({}):
        assert not environments.has_environment(new_id)
        generate_environment.has_configured_llm_key = lambda: True
        generate_environment.generate_and_persist_environment = fake_generate
        try:
            resolved = env_resolver.resolve_environment(new_id, description="resolver create test room", allow_create=True)
            assert resolved == new_id
            assert environments.has_environment(new_id)
            assert get_environment(new_id)["description"] == "resolver create test room"
        finally:
            generate_environment.has_configured_llm_key = original_has_key
            generate_environment.generate_and_persist_environment = original_generate


def _generated_env_fixture(env_id):
    return {
        "id": env_id,
        "description": "generated test room",
        "backdrop": [
            {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "paper"},
            {"type": "rect", "x": 0, "y": 660, "w": 1920, "h": 420, "fill": "paper_deep"},
        ],
        "set_props": [
            {"asset": "plant", "x": 1450, "y": 735, "scale": 0.5, "z": 130},
            {"asset": "house", "x": 1540, "y": 760, "scale": 0.38, "z": 132},
        ],
        "slots": {
            "host": {"x": 900, "y": 735, "scale": 1.25, "z": 260, "role": "foreground"},
            "guest": {"x": 1120, "y": 735, "scale": 1.2, "z": 270, "role": "foreground"},
        },
        "text_zone": {"x": 100, "y": 80, "w": 700, "h": 145},
    }


class _temporary_generated_env_store:
    def __init__(self, data):
        self.data = data
        self.path = environments.GENERATED_ENVIRONMENTS_PATH
        self.original = None

    def __enter__(self):
        self.original = _read_file(self.path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            import json

            json.dump(self.data, f, indent=2, sort_keys=True)
        environments._GENERATED_ENVIRONMENTS_CACHE = None
        return self

    def __exit__(self, exc_type, exc, tb):
        _restore_file(self.path, self.original)
        environments._GENERATED_ENVIRONMENTS_CACHE = None


class _temporary_generated_assets:
    def __init__(self, extra):
        self.extra = extra
        self.path = os.path.join(ROOT, "data", "generated_assets.json")
        self.original = None

    def __enter__(self):
        import json

        self.original = _read_file(self.path)
        try:
            existing = json.loads(self.original) if self.original else {}
        except Exception:
            existing = {}
        existing.update(self.extra)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, sort_keys=True)
        blueprint_presets._GENERATED_ASSETS_CACHE = None
        return self

    def __exit__(self, exc_type, exc, tb):
        _restore_file(self.path, self.original)
        blueprint_presets._GENERATED_ASSETS_CACHE = None


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _restore_file(path, content):
    if content is None:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    tests = [
        test_environment_contracts_and_slots,
        test_scene_stage_safe_area_clamps,
        test_scene_script_validator_legal_and_illegal_slots,
        test_generated_environment_loaded_from_data_and_scene_stage,
        test_generated_environment_validation_text_zone_and_fake_prop,
        test_unknown_environment_falls_back_safely,
        test_blueprint_validator_repairs_illegal_blueprint,
        test_scene_stage_and_non_environment_back_compat,
        test_llm_generate_callable_with_fake_openai,
        test_env_resolver_match_and_fallback_offline,
        test_env_resolver_ensure_de_dupes,
        test_env_resolver_fake_create_persists_and_resets_cache,
    ]
    for test in tests:
        test()
    print("OK scene contract tests (%d)" % len(tests))


if __name__ == "__main__":
    main()
