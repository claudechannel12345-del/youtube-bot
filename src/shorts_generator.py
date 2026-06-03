import json
import os
import shutil
import subprocess

from remotion_renderer import FPS, REMOTION_DIR, _npx_command


def select_short_segments(script_sections, sections_data):
    viable = [
        i for i, section in enumerate(sections_data)
        if float(section.get("duration") or 0) <= 60
    ]
    if not viable:
        return []

    groups = []
    used = set()
    if 0 in viable:
        cold_open = _best_group_from(0, sections_data)
        if cold_open:
            groups.append(cold_open)
            used.update(cold_open)

    candidates = []
    for i in viable:
        if i in used:
            continue
        section = script_sections[i] if i < len(script_sections) else {}
        template = str(section.get("template") or sections_data[i].get("template") or "")
        duration = float(sections_data[i].get("duration") or 0)
        priority = 0
        if template in {"stat_reveal", "quote"}:
            priority = 2
        elif "stat" in template or "quote" in template:
            priority = 1
        candidates.append((priority, duration, i))

    candidates.sort(reverse=True)
    for _, _, i in candidates:
        if len(groups) >= 3:
            break
        if i in used:
            continue
        group = _best_group_from(i, sections_data, used)
        if not group:
            continue
        groups.append(group)
        used.update(group)

    return groups


def render_shorts(sections_data, groups, temp_dir):
    if not groups:
        return []

    public_dir = os.path.join(REMOTION_DIR, "public")
    os.makedirs(public_dir, exist_ok=True)
    copied_audio = []
    props_files = []
    shorts = []

    try:
        for short_index, group in enumerate(groups, start=1):
            props_sections = []
            for position, section_index in enumerate(group):
                section = sections_data[section_index]
                audio_src = f"short_{short_index:02d}_{position:02d}.mp3"
                audio_dest = os.path.join(public_dir, audio_src)
                shutil.copyfile(section["audio_path"], audio_dest)
                copied_audio.append(audio_dest)
                props_sections.append({
                    "durationInFrames": max(1, round(float(section.get("duration") or 0) * FPS)),
                    "audioSrc": audio_src,
                    "key_phrase": section.get("key_phrase") or "",
                    "captions": _clean_captions(section.get("captions") or []),
                })

            props = {
                "fps": FPS,
                "sections": props_sections,
            }
            props_path = os.path.join(REMOTION_DIR, f"short_props_{short_index:02d}.json")
            with open(props_path, "w", encoding="utf-8") as f:
                json.dump(props, f, indent=2, ensure_ascii=True)
            props_files.append(props_path)

            output_path = os.path.abspath(os.path.join(temp_dir, f"short_{short_index:02d}.mp4"))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            _render_short(props_path, output_path)
            shorts.append({
                "path": output_path,
                "section_indices": list(group),
            })
    finally:
        for path in copied_audio:
            try:
                os.remove(path)
            except OSError:
                pass
        for path in props_files:
            try:
                os.remove(path)
            except OSError:
                pass

    return shorts


def _best_group_from(index, sections_data, used=None):
    used = used or set()
    duration = float(sections_data[index].get("duration") or 0)
    if duration <= 0 or duration > 60:
        return None
    if index in used:
        return None

    group = [index]
    next_index = index + 1
    if duration < 20 and next_index < len(sections_data) and next_index not in used:
        next_duration = float(sections_data[next_index].get("duration") or 0)
        combined = duration + next_duration
        if 0 < next_duration <= 60 and combined <= 50:
            group.append(next_index)
            duration = combined

    if duration > 50 and len(group) == 1:
        return group
    return group


def _clean_captions(captions):
    cleaned = []
    for caption in captions:
        if not isinstance(caption, dict):
            continue
        text = str(caption.get("text") or "").strip()
        if not text:
            continue
        start = _as_float(caption.get("start"), 0.0)
        end = _as_float(caption.get("end"), start + 0.5)
        cleaned.append({
            "text": text,
            "start": max(0.0, start),
            "end": max(start + 0.1, end),
        })
    return cleaned


def _render_short(props_path, output_path):
    env = {**os.environ}
    node_opts = env.get("NODE_OPTIONS", "")
    if os.environ.get("REMOTION_USE_SYSTEM_CA") and "--use-system-ca" not in node_opts:
        env["NODE_OPTIONS"] = (node_opts + " --use-system-ca").strip()
    result = subprocess.run(
        [
            _npx_command(),
            "remotion",
            "render",
            "src/index.ts",
            "Short",
            output_path,
            f"--props={os.path.basename(props_path)}",
        ],
        cwd=REMOTION_DIR,
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-1000:]
        raise RuntimeError(f"Remotion short render failed:\n{tail}")


def _as_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
