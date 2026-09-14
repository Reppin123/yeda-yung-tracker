"""
03_merge_and_clean.py
-----------------------
Takes the raw pull from 01_pull_live_metrics.py (data/live_results.json) and
produces the cleaned, dashboard-ready data/merged.json.

WHAT "CLEAN" MEANS HERE
  - Drops any row that errored out during the pull (private/deleted post,
    rate-limited, network blip, etc.) — logged to stdout so you know what
    got dropped and can re-run step 01 to retry just those.
  - Renames Instagram's raw field names to the friendlier ones the dashboard
    expects: play_count -> views, like_count -> likes, comment_count -> comments.
  - Sorts every row chronologically by taken_at (post time), oldest first —
    this is what makes the dashboard's per-post trend chart read left-to-right
    as a real timeline instead of the arbitrary order posts were listed in
    targets.json.

USAGE
  python 03_merge_and_clean.py
  python 03_merge_and_clean.py --in ../data/live_results.json --out ../data/merged.json

After this, run 02_pull_thumbnails.py to attach thumbnail URLs, then drop the
refreshed data/merged.json + data/thumbs.json into the dashboard (see the
top-level README's "Refreshing the dashboard with new data" section).
"""

import argparse
import json


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in', dest='inp', default='../data/live_results.json')
    ap.add_argument('--out', default='../data/merged.json')
    args = ap.parse_args()

    raw = json.load(open(args.inp))

    cleaned = []
    dropped = []
    for r in raw:
        if r.get('error'):
            dropped.append(r)
            continue
        cleaned.append({
            'profile': r['profile'],
            'creator': r['creator'],
            'shortcode': r['shortcode'],
            'owner': r.get('owner'),
            'views': r.get('play_count') or 0,
            'likes': r.get('like_count') or 0,
            'comments': r.get('comment_count') or 0,
            'taken_at': r.get('taken_at') or 0,
        })

    cleaned.sort(key=lambda r: r['taken_at'])

    json.dump(cleaned, open(args.out, 'w'), indent=2)
    print(f'DONE — {len(cleaned)} rows written to {args.out}')
    if dropped:
        print(f'Dropped {len(dropped)} row(s) with errors:')
        for r in dropped:
            print(f"  {r['profile']:6s} {r['creator']:22s} {r['shortcode']:14s} -> {r.get('error')}")


if __name__ == '__main__':
    main()
