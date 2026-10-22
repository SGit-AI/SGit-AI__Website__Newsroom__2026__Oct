#!/usr/bin/env python3
"""Build a hub site (a year or a month of the SGit Newsroom) from data/site.json. Deterministic; no clock."""
import html, json, os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
E = html.escape
S = json.load(open(os.path.join(ROOT, 'data', 'site.json'), encoding='utf-8'))
VERSION = open(os.path.join(ROOT, 'VERSION'), encoding='utf-8').read().strip()
VS = json.load(open(os.path.join(ROOT, 'data', 'versions.json'), encoding='utf-8'))
SITE, BASE = S['site'], 'https://' + S['site']
PAGES = []

def to_md(fragment):
    s = re.sub(r'<(h1)[^>]*>(.*?)</h1>', lambda m: '\n# ' + strip(m.group(2)) + '\n', fragment, flags=re.S)
    s = re.sub(r'<(h2)[^>]*>(.*?)</h2>', lambda m: '\n## ' + strip(m.group(2)) + '\n', s, flags=re.S)
    s = re.sub(r'<(h3)[^>]*>(.*?)</h3>', lambda m: '\n### ' + strip(m.group(2)) + '\n', s, flags=re.S)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', lambda m: f'[{strip(m.group(2))}]({m.group(1)})', s, flags=re.S)
    s = re.sub(r'<li[^>]*>(.*?)</li>', lambda m: '- ' + strip(m.group(1)) + '\n', s, flags=re.S)
    s = re.sub(r'<p[^>]*>(.*?)</p>', lambda m: '\n' + strip(m.group(1)) + '\n', s, flags=re.S)
    s = html.unescape(re.sub(r'<[^>]+>', '', s))
    return re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'

def strip(x):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x))).strip()

def layout(path, title, desc, body):
    up = '../' * path.count('/')
    PAGES.append((path, title, desc))
    crumbs = ' / '.join(f'<a href="{E(c["url"])}">{E(c["label"])}</a>' for c in S['up']) + f' / <b>{E(S["short"])}</b>'
    nav = ''.join(f'<a class="nl{" here" if p == path else ""}" href="{up}{p}">{E(t)}</a>' for p, t in S['nav'])
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)} &middot; {SITE}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{BASE}/{path}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:site_name" content="{SITE}"><meta property="og:url" content="{BASE}/{path}">
<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">
<link rel="icon" href="data:,">
<link rel="alternate" type="text/markdown" href="{up}{path[:-5]}.md">
<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>
<nav class="site"><div class="row">
  <a class="brand" href="{up}index.html">{E(S["brand"])}<span>{E(S["brand_suffix"])}</span></a>
  <a class="ver" href="{up}versions/index.html#v{E(VERSION)}" title="Release history">v{E(VERSION)}</a>
  <span class="crumbs">{crumbs}</span>
  <div class="nav-items">{nav}<a class="nl ext" href="{up}llms.txt">llms.txt</a></div>
</div></nav>
<main>
{body}
</main>
<footer class="site"><div class="row">
<p><b>{SITE}</b> {S["footer"]} Part of the <a href="https://newsroom.sgit.ai/">SGit Newsroom</a> and the <a href="https://sgit.ai/network/index.html">sgit.ai network</a>. Built by one editor and a team of software agents; the site is generated from <code>data/site.json</code> and never written by hand.</p>
<p class="disc">&#9888; Participant disclosure: published by the sgit project, which builds the stack the newsroom runs on. Content CC BY 4.0, code Apache-2.0.</p>
<p class="small">site v{E(VERSION)} &middot; <a href="{up}{path[:-5]}.md">this page as markdown</a> &middot; <a href="{E(S["repo"])}">GitHub</a></p>
</div></footer>
</body>
</html>
'''

def write(path, content):
    full = os.path.join(ROOT, path); os.makedirs(os.path.dirname(full) or ROOT, exist_ok=True)
    open(full, 'w', encoding='utf-8', newline='\n').write(content)

def page(path, title, desc, body):
    write(path, layout(path, title, desc, body))
    write(path[:-5] + '.md', f'# {title}\n\n{desc}\n\n' + to_md(body) + f'\n---\nsite v{VERSION} · {BASE}/{path}\n')

def card(item):
    kids = ''
    if item.get('children'):
        kids = '<ul class="kids">' + ''.join(f'<li><a href="{E(k["url"])}">{E(k["title"])}</a> <span class="small">{E(k.get("blurb", ""))}</span></li>' for k in item['children']) + '</ul>'
    status = f'<span class="st st-{E(item.get("status", "open").lower().replace(" ", "-"))}">{E(item.get("status", ""))}</span>' if item.get('status') else ''
    url = item.get('url')
    head = f'<a href="{E(url)}">{E(item["title"])}</a>' if url else E(item['title'])
    return f'<article class="card{" lead" if item.get("lead") else ""}"><p class="kicker">{E(item.get("kicker", ""))} {status}</p><h3>{head}</h3><p>{item.get("blurb_html") or E(item.get("blurb", ""))}</p>{kids}</article>'

def build():
    s = S
    cards = ''.join(card(i) for i in s['items'])
    down = ''.join(f'<li><a href="{E(d["url"])}"><b>{E(d["label"])}</b></a>: {E(d["blurb"])}</li>' for d in s['down'])
    upl = ''.join(f'<li><a href="{E(u["url"])}"><b>{E(u["label"])}</b></a>: {E(u["blurb"])}</li>' for u in s['up'])
    body = f'''
<header class="hero"><p class="kicker">{E(s["kicker"])}</p><h1>{E(s["title"])}</h1><p class="lead">{s["lead_html"]}</p></header>
<section><h2>{E(s["items_heading"])}</h2><div class="cards">{cards}</div></section>
<section><h2>Where this sits</h2><p>{s["where_html"]}</p><h3>Up</h3><ul>{upl}</ul><h3>Down</h3><ul>{down}</ul></section>
<section><h2>How this site works</h2><p>{s["how_html"]}</p></section>
'''
    page('index.html', s['title'], s['description'], body)
    rows = ''.join(f'<article class="rel" id="v{E(v["version"])}"><h3>v{E(v["version"])} &middot; {E(v["date"])}</h3><p>{E(v["title"])}</p></article>' for v in VS['versions'])
    page('versions/index.html', 'Release history', 'Every release of this site, one sentence each.', f'<h1>Release history</h1><p class="lead">Current: v{E(VS["current"])}. One entry per release, newest first.</p>{rows}')
    lines = [f'# {SITE}', '', f'> {s["description"]}', '', f'Site v{VERSION}. Every page has a markdown twin at the same path.', '']
    for p, t, d in PAGES: lines.append(f'- [{t}]({BASE}/{p[:-5]}.md): {d}')
    lines += ['', '## Up'] + [f'- [{u["label"]}]({u["url"]}): {u["blurb"]}' for u in s['up']] + ['', '## Down'] + [f'- [{d["label"]}]({d["url"]}): {d["blurb"]}' for d in s['down']] + ['']
    write('llms.txt', '\n'.join(lines))
    print(f'built {len(PAGES)} pages for v{VERSION}')

if __name__ == '__main__':
    build()
