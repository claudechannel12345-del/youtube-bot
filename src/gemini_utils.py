import os
import re
import time

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

# The free tier allows ~15 requests/min. Space every call out through one chokepoint so we
# never trip the per-minute limit, no matter how many callers there are. Tune via env; set to
# 0 if you move to a paid tier with higher limits.
MIN_INTERVAL = float(os.environ.get("GEMINI_MIN_INTERVAL", "4.5"))
_last_call = [0.0]


def _throttle():
    gap = MIN_INTERVAL - (time.monotonic() - _last_call[0])
    if gap > 0:
        time.sleep(gap)
    _last_call[0] = time.monotonic()


def generate(client, prompt, retries=5, delay=20):
    """Call Gemini through one throttled, self-healing chokepoint.

    - Proactively SPACES requests (MIN_INTERVAL) so we stay under the per-minute rate limit.
    - Retries on 429 rate-limit, honoring the server's retryDelay.
    - Retries on 503 overload, falling back across models.
    """
    last_err = None
    for attempt in range(retries):
        model = MODELS[min(attempt, len(MODELS) - 1)]
        _throttle()
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                m = re.search(r"retryDelay'?:?\s*'?(\d+)s", msg)
                wait = (int(m.group(1)) + 2) if m else 35
                print(f"  Gemini rate-limited (attempt {attempt + 1}/{retries}); waiting {wait}s...")
                time.sleep(wait)
                last_err = e
            elif "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                wait = delay * (attempt + 1)
                print(f"  Gemini 503 (attempt {attempt + 1}/{retries}); retrying with {model} in {wait}s...")
                time.sleep(wait)
                last_err = e
            else:
                raise
    raise last_err
