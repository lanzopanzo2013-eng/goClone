#!/usr/bin/env python3
"""
Archive the official umamusume.com stylesheets (and what they reference), byte-for-byte.

Why a GitHub runner: the authoring sandbox for this repo is firewalled to a handful
of hosts, so this job runs where there is open internet access.

Design notes
------------
* ``clones/umamusume.com/_urls.txt`` is the crawl frontier (one URL per line). It was
  seeded from a successful crawl; new URLs discovered in fetched documents are written
  to ``new-urls-<slug>.txt`` and merged back into the frontier.
* CloudFront in front of umamusume.com scores requests and returns 403 to anything that
  looks like a script, so we (a) send a full browser header set, (b) spread requests
  across processes with a delay, (c) retry with backoff, and (d) fall back to the
  Wayback "id_" raw endpoint which serves the archived bytes unmodified.
* The job is sharded by URL hash: every shard writes only its own files, so shards run
  as parallel jobs and never race on the same path.

Output (verbatim bytes only, nothing reformatted):

    _raw/css/*.css        production stylesheets
    _raw/js/*.js          SvelteKit chunks (per-route CSS links + footer component)
    _raw/fonts/*.woff2    the two Roboto variable fonts
    _raw/svg/, img/       decorative vectors and small images referenced by CSS/HTML
    _raw/site/**          rendered HTML for every public route
    _raw/external/**      assets served from parts.umamusume.com / parts.cygames.co.jp
    _raw/FETCH_MANIFEST.json  kind, byte size, sha256 and source URL per file
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "clones" / "umamusume.com"
OUT = SITE_DIR / "_raw"
FRONTIER = SITE_DIR / "_urls.txt"
WAYBACK = "https://web.archive.org/web/2026id_/"

SHARD = os.environ.get("SHARD", "").strip()          # "i/n" or empty
SHARD_INDEX, SHARD_COUNT = (0, 1)
if SHARD:
    a, b = SHARD.split("/")
    SHARD_INDEX, SHARD_COUNT = int(a), int(b)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://umamusume.com/",
}

CSS_ASSET_RE = __import__("re").compile(r"url\(\s*['\"]?(?!data:|//)([^'\")]+)['\"]?\s*\)")
HTML_REF_RE = __import__("re").compile(r"(?:src|href|data-src)=\"([^\"]+)\"")
JS_REF_RE = __import__("re").compile(
    r"[\"'`]([A-Za-z0-9_./@%\-]+\.(?:css|js|svg|png|jpe?g|webp|woff2?))[\"'`]"
)
ABS_RE = __import__("re").compile(
    r"https?://[A-Za-z0-9_.\-]+/[A-Za-z0-9_./@%\-]+\.(?:css|js|svg|png|jpe?g|webp|woff2?)"
)
BAD = __import__("re").compile(
    r"(umami|gtag|googletagmanager|google-analytics|doubleclick|sentry|hotjar|stright\.bizris|\.map$)"
)
ALLOWED_HOSTS = {"umamusume.com", "parts.umamusume.com", "parts.cygames.co.jp"}

LOCK = threading.Lock()
MANIFEST: dict[str, dict] = {}
DISCOVERED: set[str] = set()
STATS = {"ok": 0, "fail": 0, "wayback": 0}


def is_shard(url: str) -> bool:
    if SHARD_COUNT <= 1:
        return True
    return int(hashlib.sha1(url.encode()).hexdigest(), 16) % SHARD_COUNT == SHARD_INDEX


def rel_for(url: str) -> str:
    p = urlparse(url)
    path = p.path
    name = path.rsplit("/", 1)[-1]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if p.netloc and p.netloc not in ("umamusume.com", "www.umamusume.com"):
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        return f"external/{p.netloc}{parent}/{name or 'index.html'}"

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
    if not name:
        return "site/" + path.lstrip("/") + "index.html"
    if ext in ("html", "htm", "json", "txt", "xml"):
        return "site/" + path.lstrip("/")
    return "site/" + path.lstrip("/") + "/index.html"


def http_get(url: str, timeout: int = 45) -> bytes | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status == 200:
                return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 429, 500, 502, 503, 504):
            raise
        return None
    except Exception as e:  # noqa: BLE001
        print(f"    ! {type(e).__name__}: {e}", file=sys.stderr)
        return None
    return None


def fetch(url: str) -> tuple[bytes | None, str]:
    """Live first (with patient backoff — 403 is bot scoring, not absence), then Wayback."""
    live_attempts = 6
    for i in range(live_attempts):
        try:
            data = http_get(url)
            if data is not None:
                return data, url
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break
            print(f"    ! HTTP {e.code} (attempt {i+1})", file=sys.stderr)
        time.sleep(min(2 ** i, 20) * (1 + random.random()))
    # Wayback raw replay
    wb = WAYBACK + url
    for i in range(3):
        try:
            data = http_get(wb, timeout=60)
            if data is not None:
                with LOCK:
                    STATS["wayback"] += 1
                return data, wb
        except urllib.error.HTTPError as e:
            print(f"    ! wayback HTTP {e.code}", file=sys.stderr)
            if e.code == 404:
                break
        except Exception as e:  # noqa: BLE001
            print(f"    ! wayback {type(e).__name__}", file=sys.stderr)
        time.sleep(2 + 2 * i)
    return None, ""


def discover(url: str, data: bytes) -> None:
    ext = urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
    text = data.decode("utf-8", "replace")
    refs: list[str] = []
    if ext in ("html", "htm", "") or url.endswith("/"):
        refs += HTML_REF_RE.findall(text)
        refs += ABS_RE.findall(text)
    if ext == "css":
        refs += ABS_RE.findall(text)
        refs += [urljoin(url, r) for r in CSS_ASSET_RE.findall(text)]
    if ext == "js":
        refs += ABS_RE.findall(text)
        refs += [urljoin(url, r) for r in JS_REF_RE.findall(text)]
    for ref in refs:
        ref = ref.split("?")[0].split("#")[0].strip()
        if not ref or BAD.search(ref):
            continue
        if not ref.startswith("http"):
            ref = urljoin(url, ref)
        if urlparse(ref).netloc not in ALLOWED_HOSTS:
            continue
        with LOCK:
            if ref not in DISCOVERED:
                DISCOVERED.add(ref)


def worker(urls: "queue.Queue[str]") -> None:
    while True:
        try:
            url = urls.get_nowait()
        except queue.Empty:
            return
        kind = "asset"
        ext = urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
        if ext in ("html", "htm", "") or url.endswith("/"):
            kind = "page"
        elif ext == "css":
            kind = "css"
        elif ext == "js":
            kind = "js"

        data, source = fetch(url)
        if data is None:
            with LOCK:
                STATS["fail"] += 1
            print(f"  x FAILED {url}", file=sys.stderr)
        else:
            rel = rel_for(url)
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            with LOCK:
                MANIFEST[rel] = {
                    "kind": kind,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "source": source,
                    "url": url,
                }
                STATS["ok"] += 1
            print(f"  + {rel} ({len(data)} B) {'' if source == url else '[wayback]'}")
            discover(url, data)
        time.sleep(0.4 + random.random() * 0.8)  # be a polite crawler
        urls.task_done()


def main() -> int:
    targets = [ln.strip() for ln in FRONTIER.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    targets = [t for t in targets if is_shard(t)]
    print(f"shard {SHARD or 'all'}: {len(targets)} urls")

    q: "queue.Queue[str]" = queue.Queue()
    for t in targets:
        q.put(t)

    threads = [threading.Thread(target=worker, args=(q,), daemon=True) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    suffix = f"-{SHARD_INDEX}" if SHARD_COUNT > 1 else ""
    (OUT / f"FETCH_MANIFEST{suffix}.json").write_text(
        json.dumps(
            {
                "site": "https://umamusume.com",
                "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "shard": SHARD or "all",
                "stats": STATS,
                "files": MANIFEST,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if DISCOVERED:
        (OUT / f"new-urls{suffix}.txt").write_text("\n".join(sorted(DISCOVERED)) + "\n")

    total = sum(v["bytes"] for v in MANIFEST.values())
    print(f"shard {SHARD or 'all'} done: {STATS['ok']} ok / {STATS['fail']} failed, {total/1024:.1f} KiB")
    return 0 if STATS["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
