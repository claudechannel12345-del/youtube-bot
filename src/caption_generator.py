def _ts(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours = millis // 3_600_000
    millis %= 3_600_000
    minutes = millis // 60_000
    millis %= 60_000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(cues, output_path):
    index = 1
    with open(output_path, "w", encoding="utf-8") as f:
        for cue in cues:
            if cue["end"] <= cue["start"]:
                continue

            f.write(f"{index}\n")
            f.write(f"{_ts(cue['start'])} --> {_ts(cue['end'])}\n")
            f.write(f"{cue['text']}\n\n")
            index += 1
