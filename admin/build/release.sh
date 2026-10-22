#!/usr/bin/env bash
# Bump (patch by default: every push is a new version), build, validate, tripwire, push to dev, verify live.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
MSG="${1:?release message required}"; PART="${2:-patch}"; BRANCH="${RELEASE_BRANCH:-dev}"
OLD="$(cat VERSION)"; IFS=. read -r MA MI PA <<< "$OLD"
case "$PART" in major) MA=$((MA+1)); MI=0; PA=0;; minor) MI=$((MI+1)); PA=0;; *) PA=$((PA+1));; esac
NEW="$MA.$MI.$PA"
python3 - "$NEW" "$MSG" <<'PY'
import json, sys, datetime
new, msg = sys.argv[1], sys.argv[2]; p = 'data/versions.json'; j = json.load(open(p)); j['current'] = new
j['versions'].insert(0, {'version': new, 'date': datetime.date.today().isoformat(), 'title': msg}); json.dump(j, open(p, 'w'), indent=1); open(p, 'a').write('\n'); open('VERSION', 'w').write(new + '\n')
PY
echo "v$OLD -> v$NEW"; python3 admin/build/build.py; python3 admin/build/validate.py
git add -A
if git diff --cached | grep -E -q 'sgit_private_(vault|read)_[0-9a-f]{12,}|BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}'; then echo "tripwire: credential shape; aborted"; exit 1; fi
if [ -n "${RELEASE_TRAILER:-}" ]; then git commit -q -m "v$NEW: $MSG" -m "$RELEASE_TRAILER"; else git commit -q -m "v$NEW: $MSG"; fi
git push -u origin "HEAD:$BRANCH"
URL="https://$(cat CNAME)/index.html"
for i in $(seq 1 40); do if curl -fsS --max-time 20 "$URL" 2>/dev/null | grep -q ">v$NEW<"; then echo "live: $URL serves v$NEW"; exit 0; fi; sleep 15; done
echo "NOT VERIFIED: $URL does not serve v$NEW after 10 minutes; the push succeeded, the release is not done."; exit 2
