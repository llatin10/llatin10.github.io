#!/usr/bin/env python3
"""Regenerate index.html: list all *.html except index, sorted alphabetically by <title>."""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP = {"index.html"}


def extract_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip() or path.stem
    return path.stem


def main() -> int:
    pages: list[tuple[str, str]] = []
    for p in sorted(ROOT.glob("*.html")):
        if p.name.lower() in {s.lower() for s in SKIP}:
            continue
        title = extract_title(p)
        pages.append((title, p.name))

    pages.sort(key=lambda x: x[0].casefold())

    items = []
    for title, filename in pages:
        safe_href = html.escape(filename, quote=True)
        label = html.escape(title)
        items.append(f'            <li><a href="{safe_href}">{label}</a></li>')

    body = "\n".join(items) if items else "            <li><em>No pages yet</em></li>"

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
        ul {{ list-style: none; }}
        li {{ margin-bottom: 10px; }}
        a {{ color: #0d9488; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .hint {{ font-size: 0.875rem; color: #78716c; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Pages</h1>
        <p style="font-size:0.875rem;color:#78716c;margin-bottom:12px;">Sorted A–Z by page title.</p>
        <ul>
{body}
        </ul>
        <p class="hint">Add <code>.html</code> files in this folder, run <strong>/html URL</strong> in Cursor to refresh this list and push.</p>
    </div>
</body>
</html>
"""
    index_path = ROOT / "index.html"
    index_path.write_text(out, encoding="utf-8")
    print(f"Wrote {index_path} ({len(pages)} page(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
