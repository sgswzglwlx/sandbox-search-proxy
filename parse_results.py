#!/usr/bin/env python3
"""Parse search results HTML into structured JSON and text summary."""
import os, re, json, sys

html_file = sys.argv[1] if len(sys.argv) > 1 else 'search_results.html'

ENGINE = os.environ.get('ENGINE', 'google')
QUERY = os.environ.get('QUERY', '')
COUNT = int(os.environ.get('COUNT', '10'))

try:
    with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
except:
    html = ''

results = []
seen = set()

for m in re.finditer(r'<a[^>]*href\s*=\s*["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
    url = m.group(1)
    title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    domain = url.split('/')[2] if '//' in url else ''
    skip_domains = ['google.', 'duckduckgo.', 'brave.', 'qwant.', 'startpage.']
    if url not in seen and title and len(title) > 3:
        if not any(d in domain for d in skip_domains):
            seen.add(url)
            results.append({'title': title, 'url': url})

results = results[:COUNT]

with open('results.json', 'w', encoding='utf-8') as f:
    json.dump({'engine': ENGINE, 'query': QUERY, 'count': len(results), 'results': results},
              f, ensure_ascii=False, indent=2)

with open('results_summary.md', 'w', encoding='utf-8') as f:
    f.write(f'# Search Results: {ENGINE} for "{QUERY}"\n\n')
    for i, r in enumerate(results, 1):
        f.write(f'{i}. {r["title"]}\n')
        f.write(f'   {r["url"]}\n\n')

print(f'Parsed {len(results)} results from {html_file}')
