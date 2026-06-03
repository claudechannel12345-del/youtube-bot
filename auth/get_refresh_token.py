"""
Run this ONCE locally to authorize the bot to upload to your YouTube channel.
It will open a browser, ask you to log in, then print the secrets you need
to add to GitHub.

Usage:
    pip install google-auth-oauthlib google-api-python-client
    python auth/get_refresh_token.py
"""
import json
import os
import ssl
import sys

# Fix SSL certificate verification on Windows
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    try:
        import certifi
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: Run:  pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
SECRETS_FILE = os.path.join(os.path.dirname(__file__), "..", "client_secrets.json")


def main():
    if not os.path.exists(SECRETS_FILE):
        print("ERROR: client_secrets.json not found in the youtube-bot folder.")
        print("Download it from:")
        print("  Google Cloud Console > APIs & Services > Credentials")
        print("  > your OAuth 2.0 Client ID > Download JSON")
        sys.exit(1)

    print("Opening browser for YouTube authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, scopes=SCOPES)
    credentials = flow.run_local_server(port=8080)

    with open(SECRETS_FILE) as f:
        raw = json.load(f)
    installed = raw.get("installed") or raw.get("web", {})

    print("\n" + "=" * 60)
    print("SUCCESS! Add these 3 secrets to GitHub:")
    print("=" * 60)
    print(f"\nYOUTUBE_REFRESH_TOKEN\n  {credentials.refresh_token}")
    print(f"\nYOUTUBE_CLIENT_ID\n  {installed.get('client_id', 'NOT FOUND - check your JSON')}")
    print(f"\nYOUTUBE_CLIENT_SECRET\n  {installed.get('client_secret', 'NOT FOUND - check your JSON')}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
