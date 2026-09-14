# YEDA YUNG — BB Campaign Tracker

Live Instagram engagement tracker for the YEDA YUNG campaign across 3 creator
profiles (Karan, Sanju, Aditi) — 65 tracked posts. Everything needed to view
the dashboard, and to refresh it with new numbers, is in this repo.

## What's in here

```
dashboard/    the tracker itself — a single self-contained HTML file, open it and go
data/         the tracked post list + every pull's raw and cleaned output
scraping/     the 4-step pipeline that refreshes data/ and the dashboard
```

### `dashboard/YEDA_YUNG_Live_Campaign_Tracker.html`
Just double-click it / open in any browser. No server, no build step — all
data is embedded directly in the file. It's also editable: click any text on
the page to edit it in place (a small formatting toolbar appears when you
select text), and there's a "Copy HTML" button bottom-right if you want to
grab the whole page's current HTML after making edits.

### `data/`
- `targets.json` — the master list of tracked posts: `{profile, creator, shortcode}`.
  **This is the only file you edit by hand** when a new post needs tracking —
  add a row with the profile name, creator handle, and the post's shortcode
  (the part of the URL right after `/reel/` or `/p/`).
- `live_results.json` — raw output of the metrics pull (step 1 below).
- `merged.json` — cleaned, sorted, dashboard-ready version of the above (step 2).
- `thumbs.json` — `{shortcode: thumbnail_url}` map used for the post thumbnails (step 3).

### `scraping/`
Four scripts, meant to be run in order from inside this folder:

| # | Script | What it does |
|---|--------|---------------|
| 1 | `01_pull_live_metrics.py` | Pulls live views/likes/comments for every post in `targets.json` via Instagram's private API |
| 2 | `03_merge_and_clean.py` | Cleans + renames + sorts step 1's output into `merged.json` |
| 3 | `02_pull_thumbnails.py` | Pulls a thumbnail image URL for every unique post into `thumbs.json` |
| 4 | `04_update_dashboard.py` | Writes `merged.json` + `thumbs.json` straight into the dashboard HTML |

(Numbered by pipeline position, not literal run order — 3 and 2 are correctly
swapped since thumbnails are pulled from the cleaned/deduped shortcode list.)

## Setup

Needs Python 3.9+ and two packages:

```bash
pip install -r requirements.txt
```

**Auth:** these scripts don't store any Instagram login. They read the
`sessionid`/`csrftoken` cookies live out of a browser you're already logged
into Instagram on (via `browser_cookie3`). Default is Safari; pass
`--browser chrome` to use Chrome instead. Just make sure you're logged into
instagram.com in that browser before running.

## Refreshing the dashboard with new data

From the `scraping/` folder:

```bash
python 01_pull_live_metrics.py          # → data/live_results.json
python 03_merge_and_clean.py            # → data/merged.json
python 02_pull_thumbnails.py            # → data/thumbs.json
python 04_update_dashboard.py           # writes both into dashboard/*.html
```

Each script has `--help` for its full options (custom paths, `--browser chrome`,
etc.) — they all default to the folder layout above, so on a fresh checkout
you can usually just run all four with no arguments.

To track a **new post**: add a row to `data/targets.json` first, then run the
four steps above — the new post will flow through automatically.

This whole sequence is safe to hand to an AI agent / cron job — every script
is idempotent (re-running just refreshes the numbers) and paced at 2–4s
between requests to stay well under Instagram's rate limits.
