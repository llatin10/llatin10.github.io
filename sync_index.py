#!/usr/bin/env python3
"""Regenerate index.html: Deep links first; other *.html sorted A–Z by <title>."""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SKIP = {"index.html"}
SITE_BASE = "https://llatin10.github.io"


def is_deep_links_page(title: str, filename: str) -> bool:
    """Pin the deeplinks tester page first; match by title or filename."""
    if title.strip().casefold() == "deep links":
        return True
    if "deeplink" in filename.casefold():
        return True
    return False


def extract_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if m:
        raw = re.sub(r"\s+", " ", m.group(1)).strip()
        return html.unescape(raw) or path.stem
    return path.stem


def _list_items(rows: list[tuple[str, str]]) -> str:
    lines = []
    for title, filename in rows:
        safe_href = html.escape(filename, quote=True)
        label = html.escape(title)
        lines.append(f'            <li><a href="{safe_href}">{label}</a></li>')
    return "\n".join(lines)


def main() -> int:
    all_pages: list[tuple[str, str]] = []
    for p in sorted(ROOT.glob("*.html")):
        if p.name.lower() in {s.lower() for s in SKIP}:
            continue
        title = extract_title(p)
        all_pages.append((title, p.name))

    pinned: list[tuple[str, str]] = []
    rest: list[tuple[str, str]] = []
    for title, name in all_pages:
        if is_deep_links_page(title, name):
            pinned.append((title, name))
        else:
            rest.append((title, name))

    pinned.sort(key=lambda x: x[1].casefold())
    rest.sort(key=lambda x: x[0].casefold())

    pages: list[tuple[str, str]] = pinned + rest

    if not all_pages:
        body = "            <li><em>No pages yet</em></li>"
        section_note = ""
    elif pinned:
        block_pinned = _list_items(pinned)
        block_rest = _list_items(rest) if rest else "            <li><em>No other pages</em></li>"
        body = f"""            <h2 class="section">Deep links</h2>
            <ul class="page-list">
{block_pinned}
            </ul>
            <h2 class="section section-other">Other pages</h2>
            <p class="section-hint">Sorted A–Z by title.</p>
            <ul class="page-list">
{block_rest}
            </ul>"""
        section_note = '<p style="font-size:0.875rem;color:#78716c;margin-bottom:12px;">Deep links first; other pages A–Z by title.</p>'
    else:
        block = _list_items(rest)
        body = f"""            <ul class="page-list">
{block}
            </ul>"""
        section_note = '<p style="font-size:0.875rem;color:#78716c;margin-bottom:12px;">Sorted A–Z by page title.</p>'

    out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>llatin10 — pages</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: #faf9f7;
            padding: 24px;
            line-height: 1.6;
            color: #44403c;
        }}
        .container {{
            max-width: 560px;
            margin: 0 auto;
            background: #fff;
            border-radius: 12px;
            padding: 28px 32px;
            box-shadow: 0 2px 16px rgba(45, 42, 38, 0.06);
        }}
        h1 {{ font-size: 1.25rem; font-weight: 600; color: #1c1917; margin-bottom: 16px; }}
        h2.section {{ font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #78716c; margin: 20px 0 10px 0; }}
        h2.section:first-of-type {{ margin-top: 0; }}
        h2.section-other {{ margin-top: 28px; padding-top: 20px; border-top: 1px solid #e7e5e4; }}
        .section-hint {{ font-size: 0.75rem; color: #a8a29e; margin: -4px 0 10px 0; }}
        ul.page-list {{ list-style: none; }}
        ul.page-list li {{ margin-bottom: 10px; }}
        a {{ color: #0d9488; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .hint {{ font-size: 0.875rem; color: #78716c; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Pages</h1>
{section_note}
{body}
        <p class="hint">Add <code>.html</code> files in this folder, run <strong>/html URL</strong> in Cursor to refresh this list and push.</p>
    </div>
</body>
</html>
"""
    index_path = ROOT / "index.html"
    index_path.write_text(out, encoding="utf-8")
    print(f"Wrote {index_path} ({len(pages)} page(s))")
    print()
    print("Home:", SITE_BASE + "/")
    print("Pages (copy for chat):")
    if pinned:
        print("  Deep links:")
        for title, filename in pinned:
            url = f"{SITE_BASE}/{quote(filename, safe='/')}"
            print(f"  - {title} — {url}")
        if rest:
            print()
            print("  Other pages (A–Z):")
            for title, filename in rest:
                url = f"{SITE_BASE}/{quote(filename, safe='/')}"
                print(f"  - {title} — {url}")
    else:
        for title, filename in pages:
            url = f"{SITE_BASE}/{quote(filename, safe='/')}"
            print(f"  - {title} — {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
