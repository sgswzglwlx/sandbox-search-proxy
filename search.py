#!/usr/bin/env python3
"""Search engine wrapper using proper Python libraries."""
import os, sys, json, re
from urllib.request import Request, urlopen
from urllib.parse import quote

ENGINE = os.environ.get('ENGINE', 'google')
QUERY = os.environ.get('QUERY', '')
COUNT = int(os.environ.get('COUNT', '10'))

def fetch_url(url, headers=None):
    """Fetch a URL with proper headers."""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    req = Request(url, headers=headers)
    try:
        resp = urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='replace')
        return html
    except Exception as e:
        print(f'Fetch error: {e}', file=sys.stderr)
        return ''

def extract_links(html, skip_domains=None):
    """Extract meaningful links from search results HTML."""
    if skip_domains is None:
        skip_domains = ['google.', 'duckduckgo.', 'brave.', 'qwant.', 'startpage.']
    
    results = []
    seen = set()
    
    for m in re.finditer(r'<a[^>]*href\s*=\s*["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        url = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        domain = url.split('/')[2] if '//' in url else ''
        
        if url not in seen and title and len(title) > 3:
            if not any(d in domain for d in skip_domains):
                seen.add(url)
                results.append({'title': title, 'url': url})
    
    return results

def search_google(query, count=10):
    """Search Google."""
    url = f'https://www.google.com/search?q={quote(query)}&num={count}'
    html = fetch_url(url)
    results = extract_links(html)
    return results[:count]

def search_duckduckgo(query, count=10):
    """Search DuckDuckGo."""
    url = f'https://html.duckduckgo.com/html/?q={quote(query)}'
    html = fetch_url(url)
    results = extract_links(html, ['duckduckgo.com'])
    
    if len(results) < count:
        # Try lite version
        url2 = f'https://lite.duckduckgo.com/lite/?q={quote(query)}'
        html2 = fetch_url(url2)
        results2 = extract_links(html2, ['duckduckgo.com'])
        results.extend(r for r in results2 if r['url'] not in {x['url'] for x in results})
    
    return results[:count]

def search_brave(query, count=10):
    """Search Brave."""
    url = f'https://search.brave.com/search?q={quote(query)}'
    html = fetch_url(url)
    return extract_links(html, ['brave.com'])[:count]

def search_qwant(query, count=10):
    """Search Qwant."""
    url = f'https://www.qwant.com/?q={quote(query)}'
    html = fetch_url(url)
    return extract_links(html, ['qwant.com'])[:count]

def search_startpage(query, count=10):
    """Search Startpage (uses Google results)."""
    url = f'https://www.startpage.com/sp/search?query={quote(query)}'
    html = fetch_url(url)
    return extract_links(html, ['startpage.com'])[:count]

# Main
searchers = {
    'google': search_google,
    'duckduckgo': search_duckduckgo,
    'brave': search_brave,
    'qwant': search_qwant,
    'startpage': search_startpage,
}

results = []
if ENGINE in searchers:
    try:
        results = searchers[ENGINE](QUERY, COUNT)
        print(f'{ENGINE}: {len(results)} results for "{QUERY}"', file=sys.stderr)
    except Exception as e:
        print(f'Error searching {ENGINE}: {e}', file=sys.stderr)

# Save results
with open('results.json', 'w', encoding='utf-8') as f:
    json.dump({'engine': ENGINE, 'query': QUERY, 'count': len(results), 'results': results},
              f, ensure_ascii=False, indent=2)

with open('results_summary.md', 'w', encoding='utf-8') as f:
    f.write(f'# Search Results: {ENGINE} for "{QUERY}"\n\n')
    for i, r in enumerate(results, 1):
        f.write(f'{i}. {r["title"]}\n')
        f.write(f'   {r["url"]}\n\n')
