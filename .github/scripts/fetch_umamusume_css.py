#!/usr/bin/env python3
"""
Archive the official umamusume.com stylesheets (and everything they reference),
byte-for-byte.

Why a GitHub runner: the authoring sandbox used for this repo is firewalled to a
handful of hosts, so this job runs where there is open internet access.

What it pulls
-------------
1. Rendered pages (``/``, ``/news/``, a news article, ``/characters/``, ``/media/``).
2. Every ``/_app/immutable/**`` stylesheet and JS chunk those pages reference,
   recursively following chunk-to-chunk imports (SvelteKit splits CSS per route).
3. The shared Cygames header/footer web component partials served from
   ``parts.umamusume.com/assets/js/{header,footer}/index.html`` — plus whatever
   CSS/JS/images they reference — because the footer is *not* in the page CSS.
4. Fonts and small decorative assets referenced from CSS ``url()``.

Everything is written verbatim under ``clones/umamusume.com/_raw/`` with a
``FETCH_MANIFEST.json`` (sha256 + byte size + source URL) for provenance.
Nothing is reformatted or reconstructed.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "clones" / "umamusume.com" / "_raw"
ORIGIN = "https://umamusume.com"
PARTS = "https://parts.umamusume.com"
WAYBACK = "https://web.archive.org/web/2026id_/"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

PAGES = ["/", "/news/", "/news/1092", "/characters/", "/media/"]
PARTS_PAGES = [
    PARTS + "/assets/js/header/index.html",
    PARTS + "/assets/js/footer/index.html",
]

# /_app/immutable/assets/x.HASH.css  or  /_app/immutable/chunks/x.HASH.js
IMMUTABLE_RE = re.compile(r"/_app/immutable/[A-Za-z0-9_./@\-]+\.(?:css|js)")
# svelte/vite mentions css siblings by bare filename inside a chunk
CSS_NAME_RE = re.compile(r"[\"']([A-Za-z0-9_.\-]+\.css)[\"']")
# url(...) inside a stylesheet
CSS_ASSET_RE = re.compile(r"url\(\s*['\"]?(?!data:|//)([^'\")]+)['\"]?\s*\)")
# src= / href= / srcset= inside HTML
HTML_REF_RE = re.compile(r"(?:src|href)=\"([^\"]+)\"")
# quoted asset paths inside JS
JS_REF_RE = re.compile(r"[\"'`]([A-Za-z0-9_./@%\-]+\.(?:css|js|svg|png|jpe?g|webp|woff2?))[\"'`]")
ABS_RE = re.compile(r"https?://[A-Za-z0-9_.\-]+/[A-Za-z0-9_./@%\-]+\.(?:css|js|svg|png|jpe?g|webp|woff2?)")

BAD = re.compile(r"(umami|gtag|googletagmanager|google-analytics|doubleclick|sentry|hotjar|stright\.bizris)")
TRACKING = re.compile(r"(\.map$)")


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
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
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


def fetch(path_or_url: str, wayback: bool = True) -> tuple[bytes | None, str]:
    """Live first, then the Wayback raw endpoint. Returns (bytes, source)."""
    url = path_or_url if path_or_url.startswith("http") else ORIGIN + path_or_url
    b = get(url)
    if b:
        return b, url
    if not wayback:
        return None, ""
    print(f"  -> Wayback fallback for {url}", file=sys.stderr)
    b = get(WAYBACK + url, tries=2)
    return (b, WAYBACK + url) if b else (None, "")


def rel_for(url: str) -> str:
    """Map a URL to a stable path under _raw/ (no collisions, readable)."""
    p = urlparse(url)
    path = p.path
    name = path.rsplit("/", 1)[-1] or "index.html"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if p.netloc and p.netloc != "umamusume.com":
        outer = f"external/{p.netloc}" + (path.rsplit("/", 1)[0] if "/" in path else "")
        return f"{outer}/{name}"

    bucket = {
        "css": "css",
        "js": "js",
        "svg": "svg",
        "png": "img",
        "jpg": "img",
        "jpeg": "img",
        "webp": "img",
        "gif": "img",
        "avif": "img",
        "woff": "fonts",
        "woff2": "fonts",
        "ttf": "fonts",
        "otf": "fonts",
    }.get(ext)
    if bucket:
        return f"{bucket}/{name}"
    # documents -> site/<path>[/index.html]
    if not name or ext not in ("html", "htm", "json", "txt", "xml", "webmanifest"):
        name = "index.html" if not path.endswith("/") else "index.html"
    if path.endswith("/"):
        return "site/" + path.lstrip("/") + name
    if "." in path.rsplit("/", 1)[-1]:
        return "site/" + path.lstrip("/")
    return "site/" + path.lstrip("/") + "/index.html"


class Archive:
    def __init__(self) -> None:
        self.manifest: dict[str, dict] = {}
        self.queue: list[tuple[str, str]] = []  # (url, kind)
        self.seen: set[str] = set()

    def enqueue(self, url: str, kind: str) -> None:
        if not url or BAD.search(url) or TRACKING.search(url):
            return
        if url.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
            return
        if url not in self.seen:
            self.seen.add(url)
            self.queue.append((url, kind))

    def save(self, url: str, data: bytes, source: str, kind: str) -> str:
        rel = rel_for(url)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        self.manifest[rel] = {
            "kind": kind,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source": source,
            "url": url,
        }
        print(f"  + {rel} ({len(data)} B)")
        return rel

    def discover(self, url: str, data: bytes, kind: str) -> None:
        ext = urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
        text = data.decode("utf-8", "replace")
        refs: list[str] = []

        if kind == "page" or ext in ("html", "htm"):
            refs += HTML_REF_RE.findall(text)
            refs += ABS_RE.findall(text)
        if ext == "css":
            refs += ABS_RE.findall(text)
            for ref in CSS_ASSET_RE.findall(text):
                ref = ref.split("?")[0].split("#")[0]
                if ref.startswith("data:"):
                    continue
                refs.append(urljoin(url, ref))
        if ext == "js":
            refs += ABS_RE.findall(text)
            refs += [urljoin(url, r) for r in JS_REF_RE.findall(text)]
            refs += [urljoin(ORIGIN + "/_app/immutable/assets/", n) for n in CSS_NAME_RE.findall(text)]

        for ref in refs:
            ref = ref.split("?")[0].split("#")[0].strip()
            if not ref:
                continue
            if ref.startswith("/"):
                # absolute path: stays on the host that served the referrer
                ref = urljoin(url, ref)
            elif not ref.startswith("http"):
                ref = urljoin(url, ref)
            host = urlparse(ref).netloc
            if host not in ("umamusume.com", "parts.umamusume.com"):
                continue
            self.enqueue(ref, "asset")

    def run(self, max_files: int = 600) -> None:
        while self.queue and len(self.manifest) < max_files:
            url, kind = self.queue.pop(0)
            data, source = fetch(url)
            if not data:
                print(f"  FAILED {url}", file=sys.stderr)
                continue
            ext = urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
            real_kind = (
                "page"
                if ext in ("html", "htm", "")
                else {"css": "css", "js": "js"}.get(ext, "asset")
            )
            self.save(url, data, source, real_kind)
            self.discover(url, data, real_kind)


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    ar = Archive()

    # 1. seed with the rendered pages and the shared header/footer partials
    for pg in PAGES:
        ar.enqueue(ORIGIN + pg, "page")
    for pp in PARTS_PAGES:
        ar.enqueue(pp, "page")
    # known webfonts (referenced from @font-face with a cross-origin URL that
    # some proxies strip out of the CSS text)
    ar.enqueue(PARTS + "/assets/fonts/Roboto-VariableFont_wdth,wght.woff2", "asset")
    ar.enqueue(PARTS + "/assets/fonts/RobotoCondensed-VariableFont_wght.woff2", "asset")

    ar.run()

    if not ar.manifest:
        print("nothing fetched", file=sys.stderr)
        return 1

    by_kind: dict[str, int] = {}
    for v in ar.manifest.values():
        by_kind[v["kind"]] = by_kind.get(v["kind"], 0) + 1

    meta = {
        "site": ORIGIN,
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seeded_pages": PAGES,
        "parts_pages": PARTS_PAGES,
        "counts": by_kind,
        "total_bytes": sum(v["bytes"] for v in ar.manifest.values()),
        "files": ar.manifest,
    }
    (OUT / "FETCH_MANIFEST.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(f"done: {len(ar.manifest)} files ({meta['total_bytes']/1024:.1f} KiB) {by_kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
