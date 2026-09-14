"""
01_pull_live_metrics.py
------------------------
Pulls LIVE Instagram engagement metrics (views/plays, likes, comments, posted-at)
for every post listed in data/targets.json, using Instagram's private mobile API
(the same endpoint the Instagram app itself calls) — not the public oEmbed/Graph API,
which does not expose engagement numbers for arbitrary posts.

HOW AUTH WORKS
  Instagram's private API requires a logged-in session. Instead of managing a
  username/password/2FA flow, this script just reads the `sessionid` + `csrftoken`
  cookies straight out of a browser you're already logged into Instagram on
  (via the `browser_cookie3` library). No credentials are stored anywhere in
  this repo — the cookies are read live from the browser's local cookie store
  each time you run the script.

  Default browser is Safari (macOS). If you're logged into Instagram in Chrome
  instead, pass --browser chrome. On Chrome, cookies are often encrypted at the
  OS keychain level and browser_cookie3 may prompt for your Mac password —
  that's expected and safe (it's a local OS Keychain prompt, nothing leaves
  your machine).

USAGE
  python 01_pull_live_metrics.py                  # uses Safari cookies (default)
  python 01_pull_live_metrics.py --browser chrome  # uses Chrome cookies instead
  python 01_pull_live_metrics.py --targets ../data/targets.json --out ../data/live_results.json

INPUT
  data/targets.json — a flat list of {"profile", "creator", "shortcode"} objects.
  "shortcode" is the part of an Instagram reel/post URL right after /reel/ or /p/,
  e.g. for https://www.instagram.com/reel/DdOK_VAvVnm/ the shortcode is DdOK_VAvVnm.

OUTPUT
  data/live_results.json — one row per target, with raw fields from the IG API
  (play_count, like_count, comment_count, taken_at as a unix timestamp, plus an
  `error` field if that particular post failed to fetch). This is the RAW pull —
  run 03_merge_and_clean.py afterward to get the cleaned, dashboard-ready file.

NOTES FOR FUTURE RUNS / AUTOMATION
  - Paced at a random 2-4s between each *unique* shortcode to stay well under
    Instagram's rate limits. Duplicate shortcodes in targets.json (same post
    tracked under two profiles) are only fetched once and reused.
  - Safe to re-run any time to refresh numbers — it always does a full fresh
    pull, it does not diff against the previous run.
  - If you see NO SESSIONID printed, log into instagram.com in that browser
    first, then re-run.
"""

import argparse
import json
import random
import sys
import time

import browser_cookie3
import requests

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'


def shortcode_to_media_id(shortcode: str) -> int:
    media_id = 0
    for letter in shortcode:
        media_id = (media_id * 64) + ALPHABET.index(letter)
    return media_id


def get_cookies(browser: str) -> dict:
    if browser == 'safari':
        cj = browser_cookie3.safari(domain_name='instagram.com')
    elif browser == 'chrome':
        cj = browser_cookie3.chrome(domain_name='instagram.com')
    else:
        raise ValueError(f'Unsupported browser: {browser}')
    return {c.name: c.value for c in cj}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--browser', default='safari', choices=['safari', 'chrome'], help='Browser to read the logged-in Instagram session from (default: safari)')
    ap.add_argument('--targets', default='../data/targets.json', help='Path to targets.json')
    ap.add_argument('--out', default='../data/live_results.json', help='Path to write live_results.json')
    args = ap.parse_args()

    cookies = get_cookies(args.browser)
    if 'sessionid' not in cookies:
        print(f'NO SESSIONID found in {args.browser} cookies. Log into instagram.com in {args.browser} and try again.')
        sys.exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'X-IG-App-ID': '936619743392459',
        'X-CSRFToken': cookies.get('csrftoken', ''),
    }

    targets = json.load(open(args.targets))

    results = []
    seen = {}
    for i, t in enumerate(targets):
        sc = t['shortcode']
        if sc in seen:
            item = seen[sc]
        else:
            media_id = shortcode_to_media_id(sc)
            headers['Referer'] = f'https://www.instagram.com/reel/{sc}/'
            try:
                r = requests.get(f'https://www.instagram.com/api/v1/media/{media_id}/info/', headers=headers, cookies=cookies, timeout=15)
                if r.status_code == 200:
                    item = r.json()['items'][0]
                else:
                    item = {'error': f'HTTP {r.status_code}'}
            except Exception as e:
                item = {'error': str(e)}
            seen[sc] = item
            time.sleep(random.uniform(2, 4))
        row = {
            'profile': t['profile'], 'creator': t['creator'], 'shortcode': sc,
            'error': item.get('error'),
            'owner': (item.get('user') or {}).get('username'),
            'like_count': item.get('like_count'),
            'comment_count': item.get('comment_count'),
            'play_count': item.get('play_count') or item.get('ig_play_count'),
            'taken_at': item.get('taken_at'),
        }
        results.append(row)
        print(f"[{i+1}/{len(targets)}] {t['profile']:6s} {t['creator']:22s} plays={row['play_count']} likes={row['like_count']} comments={row['comment_count']}", flush=True)

    json.dump(results, open(args.out, 'w'), indent=2)
    print('DONE', len(results), 'rows written to', args.out)


if __name__ == '__main__':
    main()
