#!/usr/bin/env python3
import hashlib, json, os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
fails = []
pages = sorted(os.path.join(r, f) for r, ds, fs in os.walk(ROOT) for f in fs if f.endswith('.html') and '.git' not in r and os.sep + 'admin' not in r)
linked = set()
for p in pages:
    s = open(p, encoding='utf-8').read(); d = os.path.dirname(p)
    for m in re.finditer(r'(?:href|src)="([^"#]+)', s):
        h = m.group(1)
        if re.match(r'^(https?:|mailto:|data:)', h): continue
        t = os.path.normpath(os.path.join(d, h))
        if not os.path.exists(t): fails.append(f'{os.path.relpath(p, ROOT)}: broken link {h}')
        elif t.endswith('.html'): linked.add(t)
    if not os.path.exists(p[:-5] + '.md'): fails.append(f'{os.path.relpath(p, ROOT)}: no markdown twin')
    if '—' in re.sub(r'title="[^"]*"', '', s): fails.append(f'{os.path.relpath(p, ROOT)}: em-dash')
for p in pages:
    if p != os.path.join(ROOT, 'index.html') and p not in linked: fails.append(f'{os.path.relpath(p, ROOT)}: orphan')
llms = open(os.path.join(ROOT, 'llms.txt'), encoding='utf-8').read()
for p in pages:
    if os.path.relpath(p, ROOT)[:-5] + '.md' not in llms: fails.append(f'{os.path.relpath(p, ROOT)}: not in llms.txt')
def th():
    h = hashlib.sha256()
    for p in pages + [p[:-5] + '.md' for p in pages] + [os.path.join(ROOT, 'llms.txt')]:
        h.update(open(p, 'rb').read())
    return h.hexdigest()
b = th(); subprocess.run([sys.executable, os.path.join(ROOT, 'admin', 'build', 'build.py')], check=True, capture_output=True)
if th() != b: fails.append('build is not deterministic')
PAT = re.compile(r'sgit_private_(vault|read)_[0-9a-f]{12,}|BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}')
for r, ds, fs in os.walk(ROOT):
    ds[:] = [x for x in ds if x != '.git']
    for f in fs:
        try: t = open(os.path.join(r, f), 'rb').read().decode('utf-8', 'replace')
        except Exception: continue
        if PAT.search(t): fails.append(f'{f}: credential shape')
ver = open(os.path.join(ROOT, 'VERSION')).read().strip(); vs = json.load(open(os.path.join(ROOT, 'data', 'versions.json')))
if vs['current'] != ver or not any(v['version'] == ver for v in vs['versions']): fails.append('VERSION and data/versions.json disagree')
for f in fails: print('FAIL:', f)
print(f'{len(fails)} failures' if fails else f'gate passed: {len(pages)} pages, deterministic, v{ver}'); sys.exit(1 if fails else 0)
