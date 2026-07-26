#!/usr/bin/env python3
"""Search engine wrapper - handles DDG redirect URLs correctly."""
import os, sys, json, re
from urllib.request import Request, urlopen
from urllib.parse import quote, unquote

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
    return resp.read().decode('utf-8', errors='replace')

def resolve_url(raw_url):
    """Resolve a URL from search results to a real URL."""
    raw = raw_url.strip()
    # Handle DDG redirect URLs: //duckduckgo.com/l/?uddg=REALURL&rut=...
    if 'uddg=' in raw:
        import urllib.parse as up
        parsed = up.urlparse(raw)
        qs = up.parse_qs(parsed.query)
        if 'uddg' in qs:
            return unquote(qs['uddg'][0])
    # Handle protocol-relative URLs
    if raw.startswith('//'):
        return 'https:' + raw
    return raw

def extract_results(html, engine):
    """Extract search results from HTML."""
    seen = set()
    results = []
    
    if engine == 'duckduckgo':
        # DDG uses result__a class
        for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            raw_url = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            url = resolve_url(raw_url)
            domain = url.split('/')[2] if '//' in url else ''
            skip = ['google.', 'duckduckgo.', 'brave.', 'qwant.', 'startpage.']
            if url not in seen and title and len(title) > 3 and not any(d in domain for d in skip):
                seen.add(url)
                results.append({'title': title, 'url': url})
        
        # Also get snippet descriptions from result__snippet
        snippets = list(re.finditer(r'class="result__snippet"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S))
        snippet_map = {}
        for m in snippets:
            url = resolve_url(m.group(1))
            snippet = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            snippet_map[url] = snippet
        
        # Attach snippets to results
        for r in results:
            if r['url'] in snippet_map:
                r['snippet'] = snippet_map[r['url']]
    
    else:
        # Generic: extract all links
        for m in re.finditer(r'<a[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
            raw_url = m.group(1)
            if not raw_url.startswith('http') and not raw_url.startswith('//'):
                continue
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            url = resolve_url(raw_url)
            domain = url.split('/')[2] if '//' in url else ''
            skip = ['google.', 'duckduckgo.', 'brave.', 'qwant.', 'startpage.']
            if url not in seen and title and len(title) > 3 and not any(d in domain for d in skip):
                seen.add(url)
                results.append({'title': title, 'url': url})
    
    return results[:COUNT]

def search_google():
    return extract_results(fetch(f'https://www.google.com/search?q={quote(QUERY)}&num={COUNT}'), 'google')

def search_duckduckgo():
    return extract_results(fetch(f'https://html.duckduckgo.com/html/?q={quote(QUERY)}'), 'duckduckgo')

def search_brave():
    return extract_results(fetch(f'https://search.brave.com/search?q={quote(QUERY)}'), 'brave')

def search_qwant():
    return extract_results(fetch(f'https://www.qwant.com/?q={quote(QUERY)}'), 'qwant')

def search_startpage():
    return extract_results(fetch(f'https://www.startpage.com/sp/search?query={quote(QUERY)}'), 'startpage')

# Run
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
        results = searchers[ENGINE]()
        print(f'{ENGINE}: {len(results)} results', file=sys.stderr)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)

# Save
with open('results.json', 'w', encoding='utf-8') as f:
    json.dump({'engine': ENGINE, 'query': QUERY, 'count': len(results), 'results': results},
              f, ensure_ascii=False, indent=2)

with open('results_summary.md', 'w', encoding='utf-8') as f:
    f.write(f'# Search Results: {ENGINE} for "{QUERY}"\n\n')
    for i, r in enumerate(results, 1):
        f.write(f'{i}. {r["title"]}\n')
        f.write(f'   {r["url"]}\n')
        if 'snippet' in r:
            f.write(f'   > {r["snippet"][:100]}\n')
        f.write('\n')

print(f'DONE: {len(results)} results', file=sys.stderr)
