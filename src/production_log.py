import datetime
import json
import os
import re


def write_log(entry: dict, logs_dir="production_logs") -> str:
    os.makedirs(logs_dir, exist_ok=True)

    now = datetime.datetime.now(datetime.timezone.utc)
    title = str(entry.get("title") or "untitled")
    slug = _slug(title)
    path = os.path.join(logs_dir, f"{now.date().isoformat()}-{slug}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=True)

    return path


def _slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = slug.strip("-")[:60].strip("-")
    return slug or "untitled"
