# krillion leaderboard

A live leaderboard for the `#krillion` Slack channel. It works the same way as the
maptap board: a GitHub Action reads the channel every 15 minutes, rewrites
`data.json`, and GitHub Pages serves `index.html`.

## What's in here
- `index.html`: the site (reads `data.json`)
- `data.json`: the scores (already filled in through Krillion #132)
- `sync.py`: reads #krillion and rebuilds `data.json`
- `.github/workflows/sync.yml`: runs `sync.py` every 15 minutes

## Setup (about 10 minutes)

### 1. Let the existing Slack bot see #krillion
#krillion is in the same workspace as #maptap, so reuse the maptap bot.
1. In Slack, open `#krillion` and type `/invite @your-maptap-bot-name`.
2. Go to https://api.slack.com/apps, open the maptap app, then
   "OAuth & Permissions", and copy the "Bot User OAuth Token" (starts with `xoxb-`).

The bot still only has `channels:history`. It can read #maptap and #krillion
(the two channels it's invited to) and nothing else.

### 2. Make the repo
1. On GitHub, click "New repository". Name it something like `krillion`, make it
   **Public**, and create it.
2. Click "uploading an existing file" and drag in everything from this folder,
   **including the `.github` folder**. (If your browser skips the hidden folder,
   create the file by hand: "Add file" > "Create new file", type the name
   `.github/workflows/sync.yml`, and paste in the contents.)
3. Commit.

### 3. Add the Slack token as a secret
Repo "Settings" > "Secrets and variables" > "Actions" > "New repository secret".
- Name: `SLACK_BOT_TOKEN`
- Value: the `xoxb-` token from step 1

### 4. Turn on Pages
Repo "Settings" > "Pages". Under "Build and deployment", set Source to
"Deploy from a branch", branch `main`, folder `/ (root)`, and save.
After a minute your link appears at the top of that page
(`https://<your-username>.github.io/krillion/`).

### 5. Run the first sync
"Actions" tab > "Sync Krillion scores" > "Run workflow". After that it runs on
its own every 15 minutes, and only commits when new scores show up.

## Adjusting things
- **New player shows up as an ID like `U0ABC123`:** add them to `MEMBERS` in
  `sync.py` (in Slack: click their name > "Copy member ID").
- **Minimum dives to rank:** `MIN_DIVES` near the top of the script in `index.html`
  (currently 3). People with fewer dives are listed under "Still in the shallows".
- **Timing:** the `cron` line in `.github/workflows/sync.yml` (UTC).

## How scoring works on the board
Score is shown as depth in meters. Each of the 7 tiles is worth:
⬛ 0 · 🫧 10 · 🐟 30 · 🦑 60 · 🏮 85 · 🌟 100. Ranking defaults to average
depth; click any column header to sort by deepest dive, wins, dives, or 🏮
(midnight-zone answers). A daily win goes to the top score that day, and ties
all get the win. Only the first score someone posts for a puzzle counts, and
scores posted in threads are ignored (thread your answers, as Johnny says).
