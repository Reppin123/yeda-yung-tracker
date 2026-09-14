"""
02_pull_thumbnails.py
-----------------------
Pulls a thumbnail image URL for every UNIQUE shortcode in data/merged.json, using
the same Instagram private-API approach as 01_pull_live_metrics.py. These URLs
are signed CDN links (fbcdn.net, with `oh`/`oe` signature params) — they can be
dropped straight into an <img src="..."> tag and will work directly, but they
DO expire after a while, so re-run this script whenever thumbnails in the
dashboard start breaking (stale signed URLs).

Run this AFTER 03_merge_and_clean.py, since it reads shortcodes from
data/merged.json (the cleaned file), not the raw live_results.json.

USAGE
  python 02_pull_thumbnails.py
  python 02_pull_thumbnails.py --browser chrome
  python 02_pull_thumbnails.py --merged ../data/merged.json --out ../data/thumbs.json

OUTPUT
  data/thumbs.json — a {shortcode: thumbnail_url} map. The dashboard HTML embeds
  this directly as its THUMBS JS object (see README for how to refresh the
  dashboard with new data).
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
    ap.add_argument('--browser', default='safari', choices=['safari', 'chrome'])
    ap.add_argument('--merged', default='../data/merged.json', help='Path to the cleaned merged.json (source of shortcodes)')
    ap.add_argument('--out', default='../data/thumbs.json', help='Path to write thumbs.json')
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

    merged = json.load(open(args.merged))
    unique_scs = sorted(set(r['shortcode'] for r in merged))

    thumbs = {}
    for i, sc in enumerate(unique_scs):
        media_id = shortcode_to_media_id(sc)
        headers['Referer'] = f'https://www.instagram.com/reel/{sc}/'
        try:
            r = requests.get(f'https://www.instagram.com/api/v1/media/{media_id}/info/', headers=headers, cookies=cookies, timeout=15)
            if r.status_code == 200:
                item = r.json()['items'][0]
                cands = ((item.get('image_versions2') or {}).get('candidates') or [])
                url = cands[0]['url'] if cands else None
            else:
                url = None
        except Exception:
            url = None
        thumbs[sc] = url
        print(f"[{i+1}/{len(unique_scs)}] {sc} -> {'OK' if url else 'MISS'}", flush=True)
        time.sleep(random.uniform(2, 4))

    json.dump(thumbs, open(args.out, 'w'), indent=2)
    print('DONE', len(thumbs), 'thumbnails written to', args.out)


if __name__ == '__main__':
    main()
