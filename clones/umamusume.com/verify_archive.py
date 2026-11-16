#!/usr/bin/env python3
"""Verify captured hashes and report stylesheet coverage of the archived app bundle."""
import hashlib
import json
from pathlib import Path
import re
import sys

raw = Path(__file__).resolve().parent / '_raw'
errors = []
checked = 0
for manifest_path in [raw / 'FETCH_MANIFEST.json', *sorted(raw.glob('FETCH_MANIFEST-[0-9]*.json'))]:
    if not manifest_path.exists():
        errors.append(f'missing {manifest_path.name}')
        continue
    manifest = json.loads(manifest_path.read_text())
    for name, record in manifest['files'].items():
        file = raw / name
        if not file.is_file():
            errors.append(f'{manifest_path.name}: missing {name}')
        elif len(file.read_bytes()) != record['bytes'] or hashlib.sha256(file.read_bytes()).hexdigest() != record['sha256']:
            errors.append(f'{manifest_path.name}: hash or length mismatch: {name}')
        else:
            checked += 1
additional = raw / 'additional-css-fetch.json'
if additional.exists():
    for name, record in json.loads(additional.read_text()).items():
        if record.get('status') != 'fetched':
            continue
        subdir = 'external/parts.umamusume.com/assets/css' if name.startswith(('header.', 'footer.')) else 'css'
        file = raw / subdir / name
        if not file.is_file() or len(file.read_bytes()) != record['bytes'] or hashlib.sha256(file.read_bytes()).hexdigest() != record['sha256']:
            errors.append(f'{additional.name}: missing or mismatched {name}')
        else:
            checked += 1
app = raw / 'js' / 'app.D_SVNIEA.js'
if not app.exists():
    errors.append('missing app bundle; stylesheet coverage cannot be checked')
    referenced = set()
else:
    referenced = set(re.findall(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.css', app.read_text()))
missing = sorted(name for name in referenced if not (raw / 'css' / name).is_file())
for path in sorted((raw / 'external/parts.umamusume.com').glob('*/index.html')):
    for url in re.findall(r'href="(https://parts\.umamusume\.com/assets/css/[^"]+\.css)"', path.read_text()):
        dest = raw / 'external/parts.umamusume.com/assets/css' / url.rsplit('/', 1)[-1]
        if not dest.exists():
            missing.append(url)
print(f'Verified {checked} manifest entries; {len(referenced)} app CSS filenames referenced.')
print(f'Missing {len(missing)} known stylesheet(s):')
for name in missing:
    print('  ' + name)
for error in errors:
    print('ERROR:', error, file=sys.stderr)
if errors:
    sys.exit(2)
if missing:
    sys.exit(1)
