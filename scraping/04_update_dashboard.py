"""
04_update_dashboard.py
------------------------
The last step of the refresh pipeline: takes the cleaned data/merged.json and
data/thumbs.json and writes them straight into the dashboard HTML's embedded
`const DATA = [...]` and `const THUMBS = {...}` JS declarations, so the
dashboard is a single self-contained file with the latest numbers baked in
(no external file loading, works by just double-clicking the .html file).

This is a plain regex-based find/replace on those two exact `const NAME = ...;`
lines — it does not touch any other part of the dashboard (styling, layout,
chart logic, etc. are left completely alone).

FULL REFRESH PIPELINE (run in order, from the scraping/ folder):
  1. python 01_pull_live_metrics.py [--browser chrome]
  2. python 03_merge_and_clean.py
  3. python 02_pull_thumbnails.py [--browser chrome]
  4. python 04_update_dashboard.py

USAGE
  python 04_update_dashboard.py
  python 04_update_dashboard.py --merged ../data/merged.json --thumbs ../data/thumbs.json \
      --dashboard ../dashboard/index.html
"""

import argparse
import json
import re


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--merged', default='../data/merged.json')
    ap.add_argument('--thumbs', default='../data/thumbs.json')
    ap.add_argument('--dashboard', default='../dashboard/index.html')
    args = ap.parse_args()

    merged = json.load(open(args.merged))
    thumbs = json.load(open(args.thumbs))

    html = open(args.dashboard, encoding='utf-8').read()

    data_json = json.dumps(merged, separators=(',', ':'))
    thumbs_json = json.dumps(thumbs, separators=(',', ':'))

    new_html, n1 = re.subn(
        r'const DATA = \[.*?\];',
        lambda m: f'const DATA = {data_json};',
        html, count=1, flags=re.DOTALL,
    )
    if n1 != 1:
        raise SystemExit('Could not find `const DATA = [...];` in the dashboard HTML — aborting, nothing was written.')

    new_html, n2 = re.subn(
        r'const THUMBS = \{.*?\};',
        lambda m: f'const THUMBS = {thumbs_json};',
        new_html, count=1, flags=re.DOTALL,
    )
    if n2 != 1:
        raise SystemExit('Could not find `const THUMBS = {...};` in the dashboard HTML — aborting, nothing was written.')

    open(args.dashboard, 'w', encoding='utf-8').write(new_html)
    print(f'Updated {args.dashboard}')
    print(f'  DATA   -> {len(merged)} posts')
    print(f'  THUMBS -> {len(thumbs)} thumbnails')


if __name__ == '__main__':
    main()
