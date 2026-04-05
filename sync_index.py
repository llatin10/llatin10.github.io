#!/usr/bin/env python3
"""Regenerate index.html: Deep links first; QA Features by version (newest first); other A–Z by title.

After writing index.html, stages all *.html in this folder, commits if needed, and git push."""
from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SKIP = {"index.html"}
SITE_BASE = "https://llatin10.github.io"
CONFLUENCE_SYNC = ROOT / "sync_confluence_deeplinks.py"


def is_deep_links_page(title: str, filename: str) -> bool:
    """Pin the deeplinks tester page first; match by title or filename."""
    if title.strip().casefold() == "deep links":
        return True
    if "deeplink" in filename.casefold():
        return True
    return False


def is_qa_features_page(title: str, filename: str) -> bool:
    """QA Features Summary pages (by title or filename pattern)."""
    if "qa features summary" in title.casefold():
        return True
    if filename.casefold().startswith("qa_features_summary") and filename.lower().endswith(
        ".html"
    ):
        return True
    return False


def version_tuple_for_sort(title: str, filename: str) -> tuple[int, int, int]:
    """Parse X.Y.Z (or X.Y) from title/filename for ordering; missing -> (0,0,0)."""
    for s in (title, filename):
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", s)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        m = re.search(r"(?<![.\d])(\d+)\.(\d+)(?!\.?\d)", s)
        if m:
            return int(m.group(1)), int(m.group(2)), 0
    return (0, 0, 0)


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


def git_push_site() -> int:
    """Stage *.html and sync_index.py, commit if there are changes, push. No-op if not a git repo."""
    if not (ROOT / ".git").is_dir():
        print("Git: skip push (not a git repository).")
        return 0

    paths: list[str] = [p.name for p in sorted(ROOT.glob("*.html"))]
    # Include sync scripts + generated metadata.
    for extra in (
        "sync_index.py",
        "sync_confluence_deeplinks.py",
        "deeplinks-atlassian.meta.json",
        "deeplinks.mcp.json",
    ):
        p = ROOT / extra
        if p.is_file():
            paths.append(p.name)
    try:
        subprocess.run(
            ["git", "add", "--", *paths],
            cwd=ROOT,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Git: git add failed: {e}", file=sys.stderr)
        return 1

    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if r.returncode == 0:
        print("Git: nothing to commit (HTML unchanged).")
        return 0

    r = subprocess.run(
        ["git", "commit", "-m", "Update site index and HTML pages"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout or "git commit failed", file=sys.stderr)
        return r.returncode

    r = subprocess.run(
        ["git", "push"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout or "git push failed", file=sys.stderr)
        return r.returncode

    print("Git: committed and pushed.")
    return 0


def main() -> int:
    # Step 0: Try to sync deep links from Confluence (safe no-op if missing creds).
    if CONFLUENCE_SYNC.is_file():
        try:
            r = subprocess.run(
                [sys.executable, str(CONFLUENCE_SYNC)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if out:
                print(out)
            if err:
                print(err, file=sys.stderr)
            if r.returncode != 0:
                print(
                    f"Confluence: sync script returned {r.returncode} (continuing).",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"Confluence: sync failed ({e}) — continuing.", file=sys.stderr)

    all_pages: list[tuple[str, str]] = []
    for p in sorted(ROOT.glob("*.html")):
        if p.name.lower() in {s.lower() for s in SKIP}:
            continue
        title = extract_title(p)
        all_pages.append((title, p.name))

    pinned: list[tuple[str, str]] = []
    qa_features: list[tuple[str, str]] = []
    rest: list[tuple[str, str]] = []
    for title, name in all_pages:
        if is_deep_links_page(title, name):
            pinned.append((title, name))
        elif is_qa_features_page(title, name):
            qa_features.append((title, name))
        else:
            rest.append((title, name))

    pinned.sort(key=lambda x: x[1].casefold())
    qa_features.sort(
        key=lambda row: version_tuple_for_sort(row[0], row[1]),
        reverse=True,
    )
    rest.sort(key=lambda x: x[0].casefold())

    pages: list[tuple[str, str]] = pinned + qa_features + rest

    if not all_pages:
        body = "            <li><em>No pages yet</em></li>"
        section_note = ""
    else:
        blocks: list[str] = []
        hints: list[str] = []
        if pinned:
            hints.append("Deep links first")
            blocks.append(
                f"""            <h2 class="section">Deep links</h2>
            <ul class="page-list">
{_list_items(pinned)}
            </ul>"""
            )
        if qa_features:
            hints.append("QA Features by version (newest first)")
            blocks.append(
                f"""            <h2 class="section section-qa">QA Features Summary</h2>
            <p class="section-hint">Sorted by version number (newest first).</p>
            <ul class="page-list">
{_list_items(qa_features)}
            </ul>"""
            )
        if rest:
            hints.append("Other pages A–Z by title")
            sep = " section-other" if blocks else ""
            blocks.append(
                f"""            <h2 class="section{sep}">Other pages</h2>
            <p class="section-hint">Sorted A–Z by title.</p>
            <ul class="page-list">
{_list_items(rest)}
            </ul>"""
            )
        body = "\n".join(blocks)
        hint_text = "; ".join(hints) + "."
        section_note = f'<p style="font-size:0.875rem;color:#78716c;margin-bottom:12px;">{html.escape(hint_text)}</p>'

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
        h2.section-qa {{ margin-top: 28px; padding-top: 20px; border-top: 1px solid #e7e5e4; }}
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
        <p class="hint">Add <code>.html</code> files in this folder, run <strong>/html URL</strong> in Cursor to refresh this list (commits and pushes).</p>
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
    if qa_features:
        print()
        print("  QA Features Summary (by version, newest first):")
        for title, filename in qa_features:
            url = f"{SITE_BASE}/{quote(filename, safe='/')}"
            print(f"  - {title} — {url}")
    if rest:
        print()
        print("  Other pages (A–Z):")
        for title, filename in rest:
            url = f"{SITE_BASE}/{quote(filename, safe='/')}"
            print(f"  - {title} — {url}")
    print()
    return git_push_site()


if __name__ == "__main__":
    sys.exit(main())
