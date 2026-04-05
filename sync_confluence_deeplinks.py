#!/usr/bin/env python3
"""
Fetch the Confluence 'Deeplinks' page and generate an HTML page in this folder.

This is intended to run as part of /html URL automation.

Preferred input:
  - Use Atlassian MCP to fetch the page and save JSON locally, then run:
      python3 sync_confluence_deeplinks.py --from-mcp-json deeplinks.mcp.json

Fallback auth (direct Confluence REST API):
  - Set ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN in your environment.

Output:
  - deeplinks-atlassian.html (generated)
  - deeplinks-atlassian.meta.json (page id + version + updated timestamp)
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGE_ID = "475794673"
CONFLUENCE_BASE = "https://thefirstdigitalbankinsetup.atlassian.net/wiki"
API_URL = f"{CONFLUENCE_BASE}/rest/api/content/{PAGE_ID}?expand=body.storage,version"

OUT_HTML = ROOT / "deeplinks-atlassian.html"
OUT_META = ROOT / "deeplinks-atlassian.meta.json"


@dataclass(frozen=True)
class Link:
    label: str
    href: str


def _basic_auth_header(email: str, token: str) -> str:
    raw = f"{email}:{token}".encode("utf-8")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"Basic {b64}"


def fetch_confluence_json() -> dict:
    email = os.environ.get("ATLASSIAN_EMAIL", "").strip()
    token = os.environ.get("ATLASSIAN_API_TOKEN", "").strip()
    if not email or not token:
        raise RuntimeError(
            "Missing ATLASSIAN_EMAIL / ATLASSIAN_API_TOKEN. Skipping Confluence sync."
        )

    req = urllib.request.Request(
        API_URL,
        headers={
            "Authorization": _basic_auth_header(email, token),
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise RuntimeError(f"Confluence API HTTP {e.code}: {body[:400]}") from e
    except Exception as e:
        raise RuntimeError(f"Confluence API request failed: {e}") from e

    return json.loads(data.decode("utf-8", errors="replace"))


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return html.unescape(s)


def extract_links_from_storage(storage_html: str) -> list[Link]:
    """
    Best-effort extraction:
      - Find <a href="...">label</a>
      - Keep only links that look like "deep links" targets:
        app.*fdb*.net domains, tfd-bank.com, or paths starting with /
    """
    links: list[Link] = []
    for m in re.finditer(
        r'<a\b[^>]*\bhref="([^"]+)"[^>]*>(.*?)</a>',
        storage_html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        href = html.unescape(m.group(1)).strip()
        label = _strip_tags(m.group(2)) or href

        # Normalize Confluence relative links
        if href.startswith("/wiki/"):
            href = "https://thefirstdigitalbankinsetup.atlassian.net" + href

        keep = False
        if href.startswith("/"):
            keep = True
        if re.search(r"https?://app\.(stg|dev)fdb\.net\b", href):
            keep = True
        if re.search(r"https?://app\.tfd-bank\.com\b", href):
            keep = True
        if re.search(r"https?://app\.onezerobank\.com\b", href):
            keep = True
        if re.search(r"^onezerobank://", href, re.IGNORECASE):
            keep = True

        if keep:
            links.append(Link(label=label, href=href))

    # Deduplicate while preserving order
    seen: set[tuple[str, str]] = set()
    out: list[Link] = []
    for l in links:
        key = (l.label, l.href)
        if key in seen:
            continue
        seen.add(key)
        out.append(l)
    return out


def extract_links_from_markdownish(text: str) -> list[Link]:
    """
    Best-effort extraction from MCP markdown output (which may include:
      - Markdown links: [label](url)
      - Bare URLs: https://...
      - Confluence smartlinks/mentions rendered as <custom ...>...</custom>
    """
    links: list[Link] = []
    s = text or ""

    # Markdown links
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", s, flags=re.IGNORECASE):
        label = m.group(1).strip()
        href = html.unescape(m.group(2)).strip()
        links.append(Link(label=label or href, href=href))

    # Bare URLs
    for m in re.finditer(r"(https?://[^\s)>\"]+)", s, flags=re.IGNORECASE):
        href = html.unescape(m.group(1)).strip()
        links.append(Link(label=href, href=href))

    # Extract URLs embedded in <custom ...>https://...</custom>
    for m in re.finditer(r"<custom\b[^>]*>(.*?)</custom>", s, flags=re.IGNORECASE | re.DOTALL):
        inner = _strip_tags(m.group(1))
        for u in re.finditer(r"(https?://[^\s)]+)", inner, flags=re.IGNORECASE):
            href = html.unescape(u.group(1)).strip()
            links.append(Link(label=href, href=href))

    # Normalize and filter
    out: list[Link] = []
    seen: set[tuple[str, str]] = set()
    for l in links:
        href = l.href
        label = l.label

        if href.startswith("/wiki/"):
            href = "https://thefirstdigitalbankinsetup.atlassian.net" + href

        keep = False
        if href.startswith("/"):
            keep = True
        if re.search(r"https?://app\.(stg|dev)fdb\.net\b", href):
            keep = True
        if re.search(r"https?://app\.tfd-bank\.com\b", href):
            keep = True
        if re.search(r"https?://app\.onezerobank\.com\b", href):
            keep = True
        if re.search(r"^onezerobank://", href, re.IGNORECASE):
            keep = True
        if "thefirstdigitalbankinsetup.atlassian.net/wiki/" in href:
            keep = True
        if "thefirstdigitalbankinsetup.atlassian.net/browse/" in href:
            keep = True

        if not keep:
            continue

        key = (label, href)
        if key in seen:
            continue
        seen.add(key)
        out.append(Link(label=label, href=href))

    return out


def render_html(links: list[Link], meta: dict) -> str:
    version_obj = meta.get("version", {}) if isinstance(meta.get("version", {}), dict) else {}
    updated = version_obj.get("when") or version_obj.get("createdAt") or ""
    version = version_obj.get("number")
    title = meta.get("title") or "Deep links (from Confluence)"

    def esc(s: str) -> str:
        return html.escape(str(s), quote=True)

    rows = "\n".join(
        f"""      <a class="row" href="{esc(l.href)}" rel="noopener noreferrer">
        <div class="label">{esc(l.label)}</div>
        <div class="href">{esc(l.href)}</div>
      </a>"""
        for l in links
    ) or '<div class="empty">No links found (check Confluence formatting / filters).</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="color-scheme" content="light dark" />
  <title>Deep links (from Confluence)</title>
  <style>
    :root {{
      --bg: #f4f4f5;
      --card: #fff;
      --text: #18181b;
      --muted: #71717a;
      --accent: #0d9488;
      --border: #e4e4e7;
      --rowbg: #ecfdf5;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #09090b;
        --card: #18181b;
        --text: #fafafa;
        --muted: #a1a1aa;
        --accent: #2dd4bf;
        --border: #27272a;
        --rowbg: #134e4a;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
      padding: max(12px, env(safe-area-inset-top)) 16px max(24px, env(safe-area-inset-bottom));
      max-width: 780px;
      margin-left: auto;
      margin-right: auto;
    }}
    h1 {{
      font-size: 1.35rem;
      margin: 0 0 6px;
      font-weight: 700;
    }}
    .sub {{
      margin: 0 0 16px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
    }}
    .row {{
      display: block;
      padding: 12px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: var(--rowbg);
      text-decoration: none;
      color: var(--text);
      margin-bottom: 10px;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
    }}
    .row:active {{ opacity: 0.86; transform: scale(0.995); }}
    .label {{ font-weight: 600; }}
    .href {{
      margin-top: 6px;
      font-size: 0.82rem;
      color: var(--muted);
      word-break: break-all;
    }}
    .empty {{ color: var(--muted); font-size: 0.95rem; }}
    .meta {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.8rem;
      border-top: 1px solid var(--border);
      padding-top: 12px;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 0.92em;
    }}
  </style>
</head>
<body>
  <h1>{esc(title)}</h1>
  <p class="sub">Generated from Confluence page <code>{esc(PAGE_ID)}</code>. Tap a row to open.</p>
  <div class="panel">
{rows}
    <div class="meta">
      Confluence version: <code>{esc(version)}</code><br />
      Updated: <code>{esc(updated)}</code>
    </div>
  </div>
</body>
</html>
"""


def _load_mcp_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(payload, dict):
        raise ValueError("MCP JSON must be a JSON object")

    # Atlassian MCP fetchAtlassian export (confluence-page) uses `text` and ARI `id`.
    if payload.get("type") == "confluence-page" and isinstance(payload.get("text"), str):
        meta = payload.get("metadata") or {}
        return {
            "id": PAGE_ID,
            "type": "page",
            "status": str(meta.get("status") or "current"),
            "title": str(payload.get("title") or "Deeplinks"),
            "version": {
                "number": meta.get("version"),
                "createdAt": meta.get("createdAt"),
                "message": "",
                "minorEdit": False,
            },
            "body": payload["text"],
            "webUrl": f"{CONFLUENCE_BASE}/spaces/RD/pages/{PAGE_ID}/Deeplinks",
        }

    if str(payload.get("id", "")).strip() != PAGE_ID:
        raise ValueError(f"MCP JSON page id mismatch (expected {PAGE_ID})")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync Confluence Deeplinks HTML into this folder.")
    parser.add_argument(
        "--from-mcp-json",
        dest="from_mcp_json",
        type=str,
        default="",
        help="Path to Atlassian MCP getConfluencePage JSON response",
    )
    args = parser.parse_args(argv)

    payload: dict
    if args.from_mcp_json:
        try:
            payload = _load_mcp_json(Path(args.from_mcp_json))
        except Exception as e:
            print(f"Confluence(MCP): failed to load {args.from_mcp_json}: {e}", file=sys.stderr)
            return 1
    else:
        try:
            payload = fetch_confluence_json()
        except RuntimeError as e:
            print(f"Confluence: {e}")
            return 0

    current_version = payload.get("version", {}).get("number")
    try:
        if OUT_META.is_file():
            prev = json.loads(OUT_META.read_text(encoding="utf-8", errors="replace"))
            if prev.get("confluenceVersion") == current_version and OUT_HTML.is_file():
                print(f"Confluence: up to date (version {current_version}).")
                return 0
    except Exception:
        # If meta is corrupted/unreadable, just regenerate.
        pass

    links: list[Link]
    if isinstance(payload.get("body"), dict):
        storage_html = payload.get("body", {}).get("storage", {}).get("value", "")
        links = extract_links_from_storage(storage_html)
    else:
        links = extract_links_from_markdownish(str(payload.get("body", "")))

    OUT_HTML.write_text(render_html(links, payload), encoding="utf-8")
    OUT_META.write_text(
        json.dumps(
            {
                "pageId": PAGE_ID,
                "fetchedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "confluenceVersion": current_version,
                "confluenceUpdatedAt": payload.get("version", {}).get("when")
                or payload.get("version", {}).get("createdAt"),
                "linksCount": len(links),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Confluence: wrote {OUT_HTML.name} ({len(links)} link(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

