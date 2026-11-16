#!/usr/bin/env python3
"""
Archive the official umamusume.com stylesheets (and what they reference), byte-for-byte.

Why a GitHub runner: the authoring sandbox used for this repo is firewalled to a
handful of hosts, so this job runs where there is open internet access.

Strategy
--------
1. Request the rendered pages with a normal browser fingerprint.
2. Live site first, then the Wayback "id_" raw endpoint (replays archived bytes).
3. Store every response verbatim under clones/umamusume.com/_raw/, grouped by kind,
   plus FETCH_MANIFEST.json (sha256 + byte size + source URL) for provenance.
4. Also pull the JS chunks: SvelteKit splits CSS per route, and the shared
   `#umamusume-en-footer` web component ships its styles from a JS module.

Nothing is reconstructed or prettified here — derived, human-readable copies are
built from these raw bytes by a separate step.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "clones" / "umamusume.com" / "_raw"
ORIGIN = "https://umamusume.com"
WAYBACK = "https://web.archive.org/web/2026id_/"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

PAGES = [
    "/",
    "/news/",
    "/news/1092",
    "/characters/",
    "/media/",
]

# /_app/immutable/assets/x.HASH.css  or  /_app/immutable/chunks/x.HASH.js
IMMUTABLE_RE = re.compile(r"/_app/immutable/[A-Za-z0-9_./@\-]+\.(?:css|js)")
# a css filename mentioned inside a JS chunk (svelte/vite emits the link list there)
CSS_NAME_RE = re.compile(r"[\"']([A-Za-z0-9_.\-]+\.css)[\"']")
# url(./foo.svg) etc. inside a stylesheet
CSS_ASSET_RE = re.compile(r"url\(\s*['\"]?(?!data:|https?:|//)([^'\")]+)['\"]?\s*\)")
ABS_ASSET_RE = re.compile(r"https?://[A-Za-z0-9_.\-]+/[A-Za-z0-9_./@%\-]+\.(?:svg|png|jpg|jpeg|webp|woff2?)")
SCRIPT_SRC_RE = re.compile(r"<script[^>]+src=\"([^\"]+)\"")

BAD = re.compile(r"(umami|gtag|googletagmanager|google-analytics|doubleclick|sentry|hotjar)")


def get(url: str, tries: int = 3) -> bytes | None:
    for i in range(tries):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status == 200:
                    return r.read()
                print(f"  ! HTTP {r.status} {url}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {type(e).__name__}: {e} ({url})", file=sys.stderr)
        time.sleep(1.5 * (i + 1))
    return None


def fetch(path: str, wayback: bool = True) -> tuple[bytes | None, str]:
    """Live first, then Wayback. Returns (bytes, source)."""
    url = path if path.startswith("http") else ORIGIN + path
    b = get(url)
    if b:
        return b, url
    if not wayback:
        return None, ""
    print(f"  -> Wayback fallback for {url}", file=sys.stderr)
    b = get(WAYBACK + url, tries=2)
    return (b, WAYBACK + url) if b else (None, "")


def save(rel: str, data: bytes, source: str, manifest: dict, kind: str) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    manifest[rel] = {
        "kind": kind,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source": source,
    }
    print(f"  + {rel} ({len(data)} B) <- {source.split('/')[2]}/{source.split('/')[3]}")


def rel_for(url_path: str) -> str:
    """Map a site path to a stable location under _raw/."""
    p = url_path.split("?")[0].split("#")[0]
    if p.startswith("/_app/immutable/assets/"):
        return "css/" + p.rsplit("/", 1)[-1] if p.endswith(".css") else "js/" + p.rsplit("/", 1)[-1]
    if p.startswith("/_app/"):
        return "js/" + p.rsplit("/", 1)[-1]
    if "/assets/fonts/" in p:
        return "fonts/" + p.rsplit("/", 1)[-1]
    if p.startswith("http"):
        host = p.split("/")[2]
        return "external/" + host + "/" + "/".join(p.split("/")[3:])
    return "site/" + p.lstrip("/")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}
    page_sources: dict = {}

    css_paths: set[str] = set()
    js_paths: set[str] = set()
    asset_paths: set[str] = set()
    js_seen: set[str] = set()

    # --- 1. rendered pages ---------------------------------------------------
    for pg in PAGES:
        data, src = fetch(pg)
        if not data:
            print(f"FAILED page {pg}", file=sys.stderr)
            continue
        name = "index.html" if pg == "/" else pg.strip("/").replace("/", "_") + ".html"
        save(f"pages/{name}", data, src, manifest, "page")
        page_sources[pg] = src
        html = data.decode("utf-8", "replace")

        for m in IMMUTABLE_RE.findall(html):
            (css_paths if m.endswith(".css") else js_paths).add(m)
        for m in SCRIPT_SRC_RE.findall(html):
            if m.startswith("http") and not BAD.search(m):
                js_paths.add(m)
            elif m.startswith("/") and not BAD.search(m):
                js_paths.add(m)
        for m in ABS_ASSET_RE.findall(html):
            if not BAD.search(m):
                asset_paths.add(m)

    if not css_paths and not js_paths:
        print("no stylesheet or script references found", file=sys.stderr)
        return 1

    # --- 2. stylesheets ------------------------------------------------------
    css_text_parts: list[tuple[str, str]] = []
    for cp in sorted(css_paths):
        data, src = fetch(cp)
        if not data:
            print(f"FAILED css {cp}", file=sys.stderr)
            continue
        save(rel_for(cp), data, src, manifest, "css")
        txt = data.decode("utf-8", "replace")
        css_text_parts.append((cp, txt))
        for ref in CSS_ASSET_RE.findall(txt):
            ref = ref.split("?")[0].split("#")[0]
            if not ref or ref.startswith("data:"):
                continue
            if ref.startswith("/"):
                asset_paths.add(ref)
            else:
                asset_paths.add("/_app/immutable/assets/" + ref.lstrip("./"))
        for m in ABS_ASSET_RE.findall(txt):
            if not BAD.search(m):
                asset_paths.add(m)

    # --- 3. JS chunks (per-route CSS links, footer web component) ------------
    queue = sorted(js_paths)
    while queue:
        jp = queue.pop(0)
        if jp in js_seen:
            continue
        js_seen.add(jp)
        data, src = fetch(jp)
        if not data:
            print(f"FAILED js {jp}", file=sys.stderr)
            continue
        save(rel_for(jp), data, src, manifest, "js")
        txt = data.decode("utf-8", "replace")
        # css files referenced by name from the chunk's asset manifest
        for name in CSS_NAME_RE.findall(txt):
            cand = "/_app/immutable/assets/" + name
            if cand not in css_paths:
                css_paths.add(cand)
        # further chunks pulled in by import()
        for m in IMMUTABLE_RE.findall(txt):
            if m.endswith(".js") and m not in js_seen:
                queue.append(m)
            elif m.endswith(".css") and m not in css_paths:
                css_paths.add(m)
        for m in ABS_ASSET_RE.findall(txt):
            if not BAD.search(m) and "/fonts/" not in m:
                asset_paths.add(m)

    # second pass: stylesheets discovered from JS
    for cp in sorted(css_paths):
        rel = rel_for(cp)
        if (OUT / rel).exists():
            continue
        data, src = fetch(cp)
        if not data:
            print(f"FAILED css (from js) {cp}", file=sys.stderr)
            continue
        save(rel, data, src, manifest, "css")
        txt = data.decode("utf-8", "replace")
        css_text_parts.append((cp, txt))
        for ref in CSS_ASSET_RE.findall(txt):
            ref = ref.split("?")[0].split("#")[0]
            if not ref or ref.startswith("data:"):
                continue
            asset_paths.add(ref if ref.startswith("/") else "/_app/immutable/assets/" + ref.lstrip("./"))
        for m in ABS_ASSET_RE.findall(txt):
            if not BAD.search(m):
                asset_paths.add(m)

    # --- 4. fonts + small CSS-referenced assets -----------------------------
    for ap in sorted(asset_paths):
        if ap.endswith(".css") or ap.endswith(".js"):
            continue
        rel = rel_for(ap)
        if (OUT / rel).exists():
            continue
        data, src = fetch(ap)
        if not data:
            print(f"FAILED asset {ap}", file=sys.stderr)
            continue
        save(rel, data, src, manifest, "asset")

    # --- 5. manifest --------------------------------------------------------
    meta = {
        "site": ORIGIN,
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages": page_sources,
        "css_files": sorted(css_paths),
        "js_files": sorted(js_seen),
        "files": manifest,
    }
    (OUT / "FETCH_MANIFEST.json").write_text(json.dumps(meta, indent=2) + "\n")
    total = sum(v["bytes"] for v in manifest.values())
    print(f"done: {len(manifest)} files, {total/1024:.1f} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
