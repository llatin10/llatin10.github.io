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
  - deeplinks-atlassian.html (generated — single link to the Confluence wiki; no mirrored table)
  - deeplinks-atlassian.meta.json (version + bodySha256 + timestamps)
  - deeplinks-confluence-body.snapshot.txt (gitignored — full raw body from last fetch)
  - deeplinks-confluence-body.previous.txt (gitignored — prior snapshot when body hash changes, for diff)

Change detection uses SHA-256 of the canonical page body, not only Confluence's version number
(edits sometimes ship without a visible version bump in MCP/API metadata).

Do not commit deeplinks.mcp.json (gitignored). Keep MCP exports local only.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGE_ID = "475794673"
CONFLUENCE_BASE = "https://thefirstdigitalbankinsetup.atlassian.net/wiki"
API_URL = f"{CONFLUENCE_BASE}/rest/api/content/{PAGE_ID}?expand=body.storage,version"

OUT_HTML = ROOT / "deeplinks-atlassian.html"
OUT_META = ROOT / "deeplinks-atlassian.meta.json"
# Canonical Deeplinks wiki URL (published HTML points here only).
WIKI_PAGE_URL = f"{CONFLUENCE_BASE}/spaces/RD/pages/{PAGE_ID}/Deeplinks"
# Bumps when generated HTML shape changes (forces rewrite even if Confluence version unchanged).
HTML_TEMPLATE_MARK = "confluence-deeplinks-template:wiki-link-v1"

SNAPSHOT_BODY = ROOT / "deeplinks-confluence-body.snapshot.txt"
SNAPSHOT_PREVIOUS = ROOT / "deeplinks-confluence-body.previous.txt"


def canonical_body_text(payload: dict) -> str:
    """Raw page body as returned by API (storage HTML) or MCP (markdown-ish string)."""
    b = payload.get("body")
    if isinstance(b, dict):
        return str(b.get("storage", {}).get("value", "") or "")
    return str(b or "")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def render_wiki_link_page(meta: dict) -> str:
    """Single link to Confluence — no extracted URLs or MCP body on GitHub Pages."""
    version_obj = meta.get("version", {}) if isinstance(meta.get("version", {}), dict) else {}
    updated = version_obj.get("when") or version_obj.get("createdAt") or ""
    version = version_obj.get("number")
    title = "Deep links (from Confluence)"

    def esc(s: str) -> str:
        return html.escape(str(s), quote=True)

    wiki = WIKI_PAGE_URL
    return f"""<!DOCTYPE html>
<!-- {HTML_TEMPLATE_MARK} -->
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="color-scheme" content="light dark" />
  <title>{esc(title)}</title>
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
      max-width: 560px;
      margin-left: auto;
      margin-right: auto;
    }}
    h1 {{
      font-size: 1.35rem;
      margin: 0 0 8px;
      font-weight: 700;
    }}
    .sub {{
      margin: 0 0 18px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
    }}
    .wiki-link {{
      display: block;
      padding: 14px 16px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: var(--rowbg);
      text-decoration: none;
      color: var(--text);
      font-weight: 600;
      text-align: center;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
    }}
    .wiki-link:active {{ opacity: 0.86; transform: scale(0.995); }}
    .url {{
      margin-top: 10px;
      font-size: 0.78rem;
      font-weight: 400;
      color: var(--muted);
      word-break: break-all;
    }}
    .meta {{
      margin-top: 16px;
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
  <p class="sub">Open the canonical Deeplinks table in Confluence (sign in if prompted).</p>
  <div class="panel">
    <a class="wiki-link" href="{esc(wiki)}" rel="noopener noreferrer">Open Deeplinks in Confluence</a>
    <p class="url">{esc(wiki)}</p>
    <div class="meta">
      Page ID: <code>{esc(PAGE_ID)}</code><br />
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
            "webUrl": WIKI_PAGE_URL,
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
    body_text = canonical_body_text(payload)
    body_hash = sha256_hex(body_text)

    try:
        if OUT_META.is_file() and OUT_HTML.is_file():
            prev = json.loads(OUT_META.read_text(encoding="utf-8", errors="replace"))
            html_text = OUT_HTML.read_text(encoding="utf-8", errors="replace")
            prev_hash = prev.get("bodySha256")
            if (
                prev_hash == body_hash
                and HTML_TEMPLATE_MARK in html_text
            ):
                print(
                    f"Confluence: up to date (body sha256 unchanged; "
                    f"Confluence reports version {current_version})."
                )
                return 0
    except Exception:
        # If meta is corrupted/unreadable, just regenerate.
        pass

    prev_hash_for_msg: str | None = None
    try:
        if OUT_META.is_file():
            prev_hash_for_msg = json.loads(
                OUT_META.read_text(encoding="utf-8", errors="replace")
            ).get("bodySha256")
    except Exception:
        pass

    if prev_hash_for_msg and prev_hash_for_msg != body_hash:
        print(
            f"Confluence: page body changed (sha256 {prev_hash_for_msg[:12]}… → {body_hash[:12]}…). "
            f"Compare: diff -u {SNAPSHOT_PREVIOUS.name} {SNAPSHOT_BODY.name} "
            f"(after sync, previous copy is the last snapshot).",
            file=sys.stderr,
        )
        if SNAPSHOT_BODY.is_file():
            try:
                shutil.copy2(SNAPSHOT_BODY, SNAPSHOT_PREVIOUS)
            except OSError as e:
                print(f"Confluence: could not save {SNAPSHOT_PREVIOUS.name}: {e}", file=sys.stderr)

    SNAPSHOT_BODY.write_text(body_text, encoding="utf-8")

    OUT_HTML.write_text(render_wiki_link_page(payload), encoding="utf-8")
    OUT_META.write_text(
        json.dumps(
            {
                "pageId": PAGE_ID,
                "fetchedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "confluenceVersion": current_version,
                "confluenceUpdatedAt": payload.get("version", {}).get("when")
                or payload.get("version", {}).get("createdAt"),
                "wikiPageUrl": WIKI_PAGE_URL,
                "bodySha256": body_hash,
                "bodyCharCount": len(body_text),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Confluence: wrote {OUT_HTML.name} (wiki link only → {WIKI_PAGE_URL})")
    print(f"Confluence: saved body snapshot {SNAPSHOT_BODY.name} ({len(body_text)} chars, sha256={body_hash[:16]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

