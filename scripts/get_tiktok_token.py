"""One-shot helper to grab a TikTok user access token for posting.

TikTok's dashboard requires the Redirect URI to be https://, and a local server can't speak
https without cert hassle - so this uses the simple PASTE flow:

  1. It opens the TikTok approval page in your browser.
  2. You log in as your channel and click Allow.
  3. TikTok sends your browser to  https://localhost:8080/callback?code=...  -> the page will show a
     "can't reach this site" / privacy error. THAT IS EXPECTED (nothing is running there).
  4. You copy the WHOLE URL out of the browser's address bar and paste it back here.
  5. The script pulls the ?code= out, exchanges it for a token, and writes:
        C:\\Users\\Caden\\.youtube_bot_tiktok_token.txt     (access token  - used by publish_social.py)
        C:\\Users\\Caden\\.youtube_bot_tiktok_refresh.txt   (refresh token - for later auto-renewal)

ONE-TIME SETUP in the TikTok app dashboard (developers.tiktok.com -> your app):
  - Add product "Content Posting API", enable Direct Post, scope: video.publish
  - Login Kit -> Redirect URI, add EXACTLY:   https://localhost:8080/callback

RUN:
  py scripts/get_tiktok_token.py --client-key YOUR_KEY --client-secret YOUR_SECRET
  (or save them to the *_client_key.txt / *_client_secret.txt files and run with no args)
"""
import argparse
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
import webbrowser

HOME = r"C:\Users\Caden"
TOKEN_FILE = os.path.join(HOME, ".youtube_bot_tiktok_token.txt")
REFRESH_FILE = os.path.join(HOME, ".youtube_bot_tiktok_refresh.txt")
KEY_FILE = os.path.join(HOME, ".youtube_bot_tiktok_client_key.txt")
SECRET_FILE = os.path.join(HOME, ".youtube_bot_tiktok_client_secret.txt")
REDIRECT_URI = "https://localhost:8080/callback"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
SCOPE = "video.publish,video.upload"


def _ssl_ctx():
    ctx = ssl.create_default_context()
    if os.environ.get("SOCIAL_INSECURE_SSL") or os.environ.get("ELEVENLABS_INSECURE_SSL"):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _read(path):
    return open(path, encoding="utf-8").read().strip() if os.path.exists(path) else None


def _extract_code(pasted):
    """Accept either the full redirected URL or a bare code string."""
    pasted = pasted.strip()
    if "code=" in pasted:
        q = urllib.parse.urlparse(pasted).query or pasted.split("?", 1)[-1]
        params = urllib.parse.parse_qs(q)
        if params.get("code"):
            return params["code"][0]
    return pasted  # assume they pasted just the code


def _exchange_code(code, client_key, client_secret):
    body = urllib.parse.urlencode({
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    with urllib.request.urlopen(req, context=_ssl_ctx()) as resp:
        return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-key", default=_read(KEY_FILE))
    ap.add_argument("--client-secret", default=_read(SECRET_FILE))
    args = ap.parse_args()

    if not args.client_key or not args.client_secret:
        sys.exit("Need --client-key and --client-secret (or save them to the *_client_*.txt files).")

    state = os.urandom(8).hex()
    authorize = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_key": args.client_key,
        "scope": SCOPE,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
    })

    print("\nMake sure this EXACT redirect URI is registered in your TikTok app (Login Kit):")
    print("    " + REDIRECT_URI)
    print("\nOpening the TikTok approval page. Log in as your CHANNEL account and click Allow.")
    print("(If it doesn't open, paste this URL into your browser:)\n    " + authorize + "\n")
    try:
        webbrowser.open(authorize)
    except Exception:
        pass

    print("After you click Allow, your browser will jump to a page like:")
    print("    https://localhost:8080/callback?code=XXXXXXXX&state=...")
    print("It will show a 'can't reach this site' / 'not secure' error -- THAT IS NORMAL.")
    print("Copy the WHOLE address from the browser's address bar and paste it below.\n")
    pasted = input("Paste the redirected URL (or just the code) here: ").strip()
    code = _extract_code(pasted)
    if not code:
        sys.exit("Couldn't find a code in what you pasted.")

    print("\nExchanging the code for a token...")
    data = _exchange_code(code, args.client_key, args.client_secret)
    if "access_token" not in data:
        sys.exit("Token exchange failed: %s" % json.dumps(data))

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(data["access_token"].strip())
    if data.get("refresh_token"):
        with open(REFRESH_FILE, "w", encoding="utf-8") as f:
            f.write(data["refresh_token"].strip())

    print("\nDONE.")
    print("  access token  -> %s" % TOKEN_FILE)
    if data.get("refresh_token"):
        print("  refresh token -> %s" % REFRESH_FILE)
    print("  expires in ~%s seconds" % data.get("expires_in", "?"))
    print("\nNow post:  py scripts/publish_social.py --video out/short.mp4 --caption \"...\" --to tiktok")


if __name__ == "__main__":
    main()
