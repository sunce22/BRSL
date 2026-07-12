# Stream Prep — design spec

_Date: 2026-07-12_

## Problem

After creating the YouTube live stream, several minutes of manual steps follow before
chat commands actually work and the stream is announced everywhere:

1. Update Twitch title (and occasionally category).
2. Post a chat announcement on Twitch.
3. Switch Restream.io's dashboard to the new YouTube source, confirm chat relay works.
4. Run the Discord/Telegram announce script and paste the Telegram text manually.
5. Point `history-facts-bot` at the new YouTube live ID and restart it so `!факт` /
   `!тема` / etc. commands work in chat.

Step 5 is new and easy to forget. The goal: one command that runs all of this, reports
pass/fail per step, and highlights anything that needs manual follow-up.

## CLI

```
node tools/stream-prep/index.js --youtube <url|id> --title "Заголовок" [--announce "Текст"] [--category "Гра"]
```

- `--youtube`: required. YouTube video ID or full `youtube.com/live/<id>` /
  `studio.youtube.com/video/<id>/livestreaming` URL — same value the streamer already
  copies for `history-facts-bot`. Script extracts the ID if a URL is passed.
- `--title`: required. New Twitch title.
- `--announce`: optional. Twitch chat announcement text. If omitted, step is skipped.
- `--category`: optional. Defaults to `Raid: Shadow Legends`. Resolved to a Twitch
  category ID at runtime via Helix "Search Categories" (not hardcoded), so a typo'd or
  changed game name fails loudly instead of silently applying the wrong category.

## Steps (run sequentially, one failing step does not block the rest)

Each step is `{ name, run() }`, wrapped in try/catch. Final output is a numbered
report: ✅ / ❌ / ⚠️ per step with error detail under any non-✅ line. Process exits
non-zero if any step is ❌.

### 1. Twitch — update title/category

Uses Helix API (`PATCH /helix/channels`). Requires a user access token with
`channel:manage:broadcast` scope + the app's Client ID.

Auth: generate via twitchtokengenerator.com (same tool already used for the chat bot
token) requesting scopes `channel:manage:broadcast` + `moderator:manage:announcements`.
This is a **separate token** from the existing chat-only bot token in
`history-facts-bot/index.js` — that one is untouched. Client ID, access token, refresh
token stored in `tools/stream-prep/.secrets.json` (gitignored). Script auto-refreshes
the access token via the stored refresh token when Helix returns 401.

Broadcaster's Twitch user ID resolved once via `GET /helix/users?login=<channel>` and
cached in the same secrets file.

### 2. Twitch — chat announcement

`POST /helix/chat/announcements`, same token (broadcaster is implicitly a moderator of
their own channel, so no extra scope holder needed). Skipped entirely if `--announce`
not passed.

### 3. Restream.io — switch YouTube source

Playwright automation using a locally saved `storageState` (one-time manual login,
no re-login needed afterward). Navigates to the Restream dashboard, selects the new
YouTube stream from its source picker, and verifies both Twitch and YouTube chat-relay
indicators show connected.

Exact selectors are **not specified here** — the Restream dashboard structure will be
inspected interactively (headed browser / codegen) during implementation, since no
public API exists for this. If the dashboard layout changes later, this step is the
most likely to need selector maintenance.

### 4. Share — Discord + Telegram

Invokes `D:\projects\personal_youtube\stream_announce.py` unmodified via
`child_process.execFile`. Captures stdout:
- If it reports a successful Discord post → ✅.
- The printed "Скопіюй це для Telegram" block is extracted and echoed prominently in
  the final report — Telegram posting stays manual (multiple channels/threads, no
  single bot token available).
- **Known caveat:** YouTube's RSS feed the script polls can lag several minutes behind
  stream creation. If the script reports no new video, this step is marked ⚠️ with a
  note to rerun `stream_announce.py` manually once RSS catches up. No automatic
  retry/poll loop is added for this (keep it simple; can be revisited if it's a
  frequent annoyance in practice).

### 5. history-facts-bot — repoint + restart

- Regex-replace `const YOUTUBE_LIVE_ID = '...'` in `d:\history-facts-bot\index.js`
  with the new ID.
- Kill any previously running `node index.js` process for this bot (tracked via a PID
  file written on spawn), then spawn a new detached `node index.js`, stdout/stderr
  redirected to a log file.
- Tail that log for up to 15s looking for both connection markers (Streamlabs/Twitch
  connect success line, YouTube chat `start` event). Report ✅ per marker seen, ❌ with
  the last log lines if a marker doesn't show up in time.

## Config / secrets layout

```
tools/stream-prep/
  index.js
  steps/
    twitch.js
    restream.js
    share.js
    historyBot.js
  .secrets.json        (gitignored: twitch client id/secret/tokens, broadcaster id)
  restream-state.json  (gitignored: Playwright storageState)
  historyBot.pid        (runtime, written on spawn)
```

`.gitignore` gets entries for `tools/stream-prep/.secrets.json` and
`tools/stream-prep/restream-state.json`.

## Out of scope

- Auto-detecting the new YouTube live ID (user already has it in hand from creating
  the stream — passing it as a CLI arg is simpler and more reliable than scraping
  YouTube Studio).
- Retrying the RSS-lag case in step 4 automatically.
- A full Twitch Developer Console app registration — twitchtokengenerator.com's
  existing flow covers the needed scopes without that overhead.
