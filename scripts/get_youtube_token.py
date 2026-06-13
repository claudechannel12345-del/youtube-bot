"""Mint a fresh YouTube OAuth refresh token (run locally, interactively).

Opens a browser, you log in as the CHANNEL Google account (claudechannel12345@gmail.com)
and grant access. Writes the new refresh token to C:\\Users\\Caden\\.youtube_bot_yt_refresh.txt
(OUTSIDE the repo). It is never printed in full or committed.

Usage:  py scripts/get_youtube_token.py
"""
import os

# This machine runs Avast, which intercepts HTTPS and re-signs it with its own root CA.
# That root lives in the Windows cert store but NOT in certifi's bundle, so the Google
# token-exchange call fails verification. truststore routes SSL through the Windows store.
import truststore

truststore.inject_into_ssl()

from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
OUT = os.path.join(os.path.expanduser("~"), ".youtube_bot_yt_refresh.txt")


def main():
    secrets = os.path.join(ROOT, "client_secrets.json")
    if not os.path.exists(secrets):
        raise SystemExit("client_secrets.json not found in repo root")
    flow = InstalledAppFlow.from_client_secrets_file(secrets, SCOPES)
    # access_type=offline + prompt=consent forces Google to return a refresh_token
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not creds.refresh_token:
        raise SystemExit("No refresh_token returned — re-run and make sure to grant access.")
    with open(OUT, "w", encoding="ascii") as f:
        f.write(creds.refresh_token)
    rt = creds.refresh_token
    print("OK. New refresh token saved to:", OUT)
    print("Preview (first/last 6 chars):", rt[:6] + "..." + rt[-6:])
    print("Channel authorized for scope:", SCOPES[0])


if __name__ == "__main__":
    main()
