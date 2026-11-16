#!/usr/bin/env python3
"""
Fetch the official umamusume.com stylesheets byte-for-byte.

Strategy
--------
1. Try the live site (https://umamusume.com/) with a normal browser UA.
2. If a request fails, fall back to the Wayback Machine "id_" raw endpoint,
   which replays the archived bytes without rewriting them.
3. Write every response verbatim to clones/umamusume.com/_raw/ ...
   plus a manifest (sha256 + byte size + source URL) so provenance is provable.

Nothing here "reconstructs" CSS: files are stored exactly as served.
"""

from __future__ import annotations

import hashlib
import json
import os
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
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)

PAGES = ["/", "/news/", "/characters/", "/media/"]

CSS_RE = re.compile(r"/_app/immutable/assets/[A-Za-z0-9_.\-]+\.css")
# url(./foo.svg) / url(foo.woff2) / url(/_app/...) inside a stylesheet
CSS_ASSET_RE = re.compile(r"url\(\s*['\"]?(?!data:|https?:|//)([^'\")]+)['\"]?\s*\)")
FONT_RE = re.compile(r"/assets/fonts/[A-Za-z0-9_.%,\-]+\.(?:woff2?|ttf|otf)")


def get(url: str, tries: int = 3) -> bytes | None:
    for i in range(tries):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status == 200:
                    return r.read()
                print(f"  ! {r.status} {url}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {type(e).__name__}: {e} ({url})", file=sys.stderr)
        time.sleep(1.5 * (i + 1))
    return None


def fetch(path: str) -> tuple[bytes | None, str]:
    """Live first, then Wayback. Returns (bytes, source)."""
    b = get(ORIGIN + path)
    if b:
        return b, ORIGIN + path
    print(f"  -> falling back to Wayback for {path}", file=sys.stderr)
    b = get(WAYBACK + ORIGIN + path, tries=2)
    if b:
        return b, WAYBACK + ORIGIN + path
    return None, ""


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
    print(f"  + {rel} ({len(data)} B) <- {source.split('/')[2]}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}
    pages: dict = {}
    css_paths: set[str] = set()
    extra_paths: set[str] = set()

    # --- 1. pages -----------------------------------------------------------
    for pg in PAGES:
        data, src = fetch(pg)
        if not data:
            print(f"FAILED page {pg}", file=sys.stderr)
            continue
        name = "index.html" if pg == "/" else pg.strip("/").replace("/", "_") + ".html"
        save(f"pages/{name}", data, src, manifest, "page")
        pages[pg] = src
        html = data.decode("utf-8", "replace")
        for m in CSS_RE.findall(html):
            css_paths.add(m)

    if not css_paths:
        print("no stylesheet links found in any page", file=sys.stderr)
        return 1

    # --- 2. stylesheets -----------------------------------------------------
    srcs: list[tuple[str, bytes]] = []
    for cp in sorted(css_paths):
        data, src = fetch(cp)
        if not data:
            print(f"FAILED css {cp}", file=sys.stderr)
            continue
        srcs.append((cp, data))
        save(cp.lstrip("/").replace("_app/immutable/assets/", "css/"), data, src, manifest, "css")
        txt = data.decode("utf-8", "replace")
        for ref in CSS_ASSET_RE.findall(txt):
            ref = ref.split("?")[0].split("#")[0]
            if not ref or ref.startswith("../.."):
                continue
            if ref.startswith("/"):
                extra_paths.add(ref)
            else:  # relative to the stylesheet directory
                extra_paths.add("/_app/immutable/assets/" + ref.lstrip("./"))
        for f in FONT_RE.findall(txt):
            extra_paths.add(f)

    # font URLs are written as ../../../assets/fonts/... -> normalise to /assets/fonts/...
    extra_paths = {p if p.startswith("/") else "/" + p for p in extra_paths}

    # --- 3. assets referenced by the CSS (fonts, svg decorations, images) ---
    for ap in sorted(extra_paths):
        if ap.endswith(".css"):
            continue
        rel = "assets/" + ap.lstrip("/").replace("_app/immutable/assets/", "immutable/")
        if (OUT / rel).exists():
            continue
        data, src = fetch(ap)
        if not data:
            print(f"FAILED asset {ap}", file=sys.stderr)
            continue
        save(rel, data, src, manifest, "asset")

    # --- 4. manifest --------------------------------------------------------
    meta = {
        "site": ORIGIN,
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages": pages,
        "css_files": sorted(css_paths),
        "files": manifest,
    }
    (OUT / "FETCH_MANIFEST.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"done: {len(manifest)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
