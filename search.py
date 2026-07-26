#!/usr/bin/env python3
"""Search engine wrapper. Saves raw HTML for debugging."""
import os, sys, json, re
from urllib.request import Request, urlopen
from urllib.parse import quote

ENGINE = os.environ.get('ENGINE', 'duckduckgo')
QUERY = os.environ.get('QUERY', '')
COUNT = int(os.environ.get('COUNT', '10'))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch(url):
    req = Request(url, headers=HEADERS)
    resp = urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')
    return html

# Try different search URLs based on engine
results = []

if ENGINE == 'google':
    html = fetch(f'https://www.google.com/search?q={quote(QUERY)}&num={COUNT}')
elif ENGINE == 'duckduckgo':
    html = fetch(f'https://html.duckduckgo.com/html/?q={quote(QUERY)}')
elif ENGINE == 'brave':
    html = fetch(f'https://search.brave.com/search?q={quote(QUERY)}')
elif ENGINE == 'qwant':
    html = fetch(f'https://www.qwant.com/?q={quote(QUERY)}')
elif ENGINE == 'startpage':
    html = fetch(f'https://www.startpage.com/sp/search?query={quote(QUERY)}')
else:
    html = ''

# Save raw HTML for debugging
with open('search_results.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Parse links
seen = set()
skip_domains = ['google.', 'duckduckgo.', 'brave.', 'qwant.', 'startpage.', 'accounts.google']

for m in re.finditer(r'<a[^>]*href\s*=\s*["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
    url = m.group(1)
    title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    domain = url.split('/')[2] if '//' in url else ''
    
    if url not in seen and title and len(title) > 3:
        if not any(d in domain for d in skip_domains):
            seen.add(url)
            results.append({'title': title, 'url': url})

# DuckDuckGo specific: try alternative parsing
if ENGINE == 'duckduckgo' and len(results) < 3:
    # DDG uses result__a class
    for m in re.finditer(r'class="result__a"[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
        url = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if url not in seen and title:
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

print(f'Results: {len(results)}, HTML size: {len(html)} bytes, first 200: {html[:200]}', file=sys.stderr)
