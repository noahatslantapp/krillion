#!/usr/bin/env python3
"""
Reads the #krillion Slack channel and writes data.json for the leaderboard site.

Minimal-access design (same as the maptap board): this script ONLY reads the one
channel you point it at. It does not read the workspace user directory or any other
channel. Player names come from the built-in MEMBERS map below.

Environment variables (set in the GitHub Actions workflow / secrets):
  SLACK_BOT_TOKEN       Bot User OAuth Token (starts with xoxb-)
  KRILLION_CHANNEL_ID   The channel ID (default: #krillion)

Required Slack bot scope: channels:history   (that's the only one)
The bot must be invited to the channel:  /invite @your-bot-name  in #krillion
Uses the Python standard library only. No packages to install.
"""
import os, re, json, time, datetime, urllib.request, urllib.parse

TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("KRILLION_CHANNEL_ID", "C0CD7M5361L")

# user_id -> display name. Add a line when someone new starts posting
# (Slack: click their name -> "Copy member ID"). Unknown IDs show as the raw ID.
MEMBERS = {
    "U0B4K0M14KC": "Johnny Richards",
    "U0B9ZSVDMUZ": "Haley Brown",
    "U0CCM0A1VH6": "Carly Brecht",
    "U0B1X34UCRJ": "Noah Hankin",
    "U0ATZ5ZQN4D": "Jonathan Farnsworth",
    "U0AU0G9QMQE": "Jeff",
    "U0B433R2F61": "Mitch",
    "U0AC040ALQ7": "MURP",
    "U0ADP5H1VD4": "Chris Arnold",
    "U0AGJN69AQN": "Emma Walton",
    "U0AN4E26WSX": "Jake Hope",
    "U0777UVE75Z": "Mckade Adams",
    "U09U4Q8DU9M": "Trevan Reese",
    "U04QX0HSSLC": "Thomas Clawson",
    "U0CG7C7UUCR": "John Sandberg",
    "U0799JAE2Q3": "Hunter Romano",
}

# Krillion's per-prompt tiles. Code letters are what data.json stores.
TILES = {
    "black_large_square": "X", "bubbles": "B", "fish": "F",
    "squid": "S", "izakaya_lantern": "L", "star2": "T",
}
UNICODE_TILES = {"⬛": "X", "🫧": "B", "🐟": "F", "🦑": "S", "🏮": "L", "🌟": "T"}

# Puzzle numbers map to calendar days: Krillion #132 was 2026-11-24.
ANCHOR_NUM, ANCHOR_DATE = 132, datetime.date(2026, 11, 24)

SCORE_RE = re.compile(r"Krillion\s*#\s*(\d+)[^\n]*\n\s*(\d{1,4})\b", re.I)
TILE_RE = re.compile(r":([a-z0-9_+\-]+):|(⬛|🫧|🐟|🦑|🏮|🌟)")


def slack(method, **params):
    url = f"https://slack.com/api/{method}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "5")))
                continue
            raise
        if not data.get("ok"):
            raise SystemExit(f"Slack error from {method}: {data.get('error')}")
        return data
    raise SystemExit("Slack kept rate-limiting; try again later.")


def parse(text):
    m = SCORE_RE.search(text or "")
    if not m:
        return None
    num, score = int(m.group(1)), int(m.group(2))
    tiles = ""
    for code, uni in TILE_RE.findall(text[m.end():]):
        t = TILES.get(code) if code else UNICODE_TILES.get(uni)
        if t:
            tiles += t
            if len(tiles) == 7:
                break
    return num, score, tiles


def main():
    messages, cursor = [], None
    while True:
        params = {"channel": CHANNEL_ID, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        page = slack("conversations.history", **params)
        messages += page.get("messages", [])
        cursor = page.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    puzzles = {}
    for msg in sorted(messages, key=lambda m: float(m["ts"])):  # oldest first
        if msg.get("subtype") or not msg.get("user"):
            continue
        got = parse(msg.get("text", ""))
        if not got:
            continue
        num, score, tiles = got
        name = MEMBERS.get(msg["user"], msg["user"])
        day = puzzles.setdefault(num, {})
        if name not in day:  # first post per person per puzzle counts
            day[name] = {"score": score, "tiles": tiles}

    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "puzzles": [
            {
                "num": n,
                "date": (ANCHOR_DATE + datetime.timedelta(days=n - ANCHOR_NUM)).isoformat(),
                "scores": [{"name": k, **v} for k, v in
                           sorted(puzzles[n].items(), key=lambda kv: -kv[1]["score"])],
            }
            for n in sorted(puzzles, reverse=True)
        ],
    }
    # Leave the file alone when no new scores came in, so the repo only gets a
    # commit when something actually changed (not every 15 minutes).
    try:
        with open("data.json") as f:
            if json.load(f).get("puzzles") == out["puzzles"]:
                print("No new scores.")
                return
    except (FileNotFoundError, ValueError):
        pass
    with open("data.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"Wrote {len(out['puzzles'])} puzzles, "
          f"{sum(len(p['scores']) for p in out['puzzles'])} dives.")


if __name__ == "__main__":
    main()
