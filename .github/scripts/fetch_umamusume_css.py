#!/usr/bin/env python3
"""Fetch missing CSS chunks referenced by the archived SvelteKit application."""
import concurrent.futures, hashlib, json, pathlib, re, urllib.request

out = pathlib.Path('clones/umamusume.com/_raw')
app = (out / 'js/app.D_SVNIEA.js').read_text()
names = sorted(set(re.findall(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.css', app)))
names += ['header.7t5x1aId.css', 'footer.DrBbS_Io.css']
manifest = {}
previous_path = out / 'additional-css-fetch.json'
previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
def fetch(name):
    if name.startswith(('header.', 'footer.')):
        url = 'https://parts.umamusume.com/assets/css/' + name
        dst = out / 'external/parts.umamusume.com/assets/css' / name
        dst.parent.mkdir(parents=True, exist_ok=True)
    else:
        url = 'https://umamusume.com/_app/immutable/assets/' + name
        dst = out / 'css' / name
    if dst.exists():
        entry = previous.get(name, {})
        if entry.get('status') == 'fetched' and hashlib.sha256(dst.read_bytes()).hexdigest() == entry.get('sha256'):
            return name, entry
        return name, {'status': 'already archived'}
    errors = []
    for candidate in (url, 'https://web.archive.org/web/2026id_/' + url):
        try:
            req = urllib.request.Request(candidate, headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                final_url = resp.geturl()
                content_type = resp.headers.get('Content-Type', '')
            if not data or 'text/html' in content_type or data.lstrip().lower().startswith(b'<!doctype html'):
                raise ValueError('not a CSS response: ' + content_type)
            dst.write_bytes(data)
            return name, {'status':'fetched', 'url':url, 'source':candidate, 'final_url':final_url,
                          'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()}
        except Exception as e:
            errors.append(type(e).__name__ + ': ' + str(e))
    return name, {'status':'failed', 'url':url, 'errors':errors}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for name, result in pool.map(fetch, names):
        manifest[name] = result
        print(name, result['status'], flush=True)
(out / 'additional-css-fetch.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
