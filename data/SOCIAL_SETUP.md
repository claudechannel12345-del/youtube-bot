# Auto-posting shorts to TikTok + Instagram Reels

The pipeline already renders a vertical short (`make_short.py` → `out/short.mp4`).
`scripts/publish_social.py` distributes that file to TikTok and Instagram. Each platform needs a
one-time developer-app + token setup **you** do with your own accounts. Tokens go in
`C:\Users\Caden\.youtube_bot_*.txt` (outside the repo, never committed — same as the other keys).

---

## TikTok (Content Posting API)

1. Create a developer app at https://developers.tiktok.com → "Manage apps".
2. Add the **Content Posting API** product, scopes: `video.publish` (direct post) — `video.upload`
   only sends to drafts.
3. Do the OAuth login flow for **your channel's TikTok account** to get a **user access token**.
   Save it to `C:\Users\Caden\.youtube_bot_tiktok_token.txt`.
4. **Audit gate:** until TikTok approves your app, posts are forced to `SELF_ONLY` (private). The
   code defaults to that so it won't error. After audit, set `TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE`.
5. Access tokens expire (~24h) and need refresh-token renewal — note the expiry when you set it up.

Token file: `.youtube_bot_tiktok_token.txt`

---

## Instagram Reels (Graph API)

1. Convert the channel's IG account to **Business or Creator**, and link it to a **Facebook Page**.
2. Create a Meta app at https://developers.facebook.com → add **Instagram** + permission
   `instagram_content_publish` (also `instagram_basic`, `pages_show_list`).
3. Generate a **long-lived access token** (~60 days) for the IG user. Save to
   `.youtube_bot_ig_token.txt`.
4. Get the **IG user id** (`GET /me/accounts` → page → `instagram_business_account`). Save the numeric
   id to `.youtube_bot_ig_user_id.txt`.
5. IG **pulls** the video from a public URL — `publish_social.py` auto-hosts via catbox.moe. To use
   your own host instead, pass `--video-url https://...`.

Token files: `.youtube_bot_ig_token.txt`, `.youtube_bot_ig_user_id.txt`

---

## Running it

```
# render the vertical short first
py scripts/make_short.py

# then distribute (caption from --caption, or out/short.caption.txt sidecar)
py scripts/publish_social.py --video out/short.mp4 --caption "..." --to tiktok,instagram
```

`--to` accepts any of: `tiktok`, `instagram`. YouTube Shorts already has its own path
(`publish_short.py` / `uploader.upload_short`).

## Status / blockers
- Code is complete and ready; it CANNOT be tested until the tokens above exist.
- TikTok public posting is blocked until app audit (days). Private posting works immediately for testing.
- Instagram needs the Business-account + FB-Page link before any token will have publish permission.
