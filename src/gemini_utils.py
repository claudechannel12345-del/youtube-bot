import time

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]


def generate(client, prompt, retries=4, delay=20):
    """Call Gemini with retries across models on 503/overload errors."""
    last_err = None
    for attempt in range(retries):
        model = MODELS[min(attempt, len(MODELS) - 1)]
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                wait = delay * (attempt + 1)
                print(f"  Gemini 503 (attempt {attempt + 1}/{retries}), "
                      f"retrying with {model} in {wait}s...")
                time.sleep(wait)
                last_err = e
            else:
                raise
    raise last_err
