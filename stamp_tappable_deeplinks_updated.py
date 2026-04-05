#!/usr/bin/env python3
"""Set <title> and visible 'Updated on' line for deeplinks-tappable-mobile copy.html (local date).

The published URL must stay: deeplinks-tappable-mobile%20copy.html
Run automatically from sync_index.py on each /html URL pass."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

FILENAME = "deeplinks-tappable-mobile copy.html"
BASE_TITLE = "Deep links (tap to open app)"


def stamp(site_root: Path, when: date | None = None) -> bool:
    when = when or date.today()
    path = site_root.resolve() / FILENAME
    if not path.is_file():
        print(f"Stamp: skip (missing {path.name})", file=sys.stderr)
        return False

    text = path.read_text(encoding="utf-8")
    full_title = f"{BASE_TITLE} — updated on {when.isoformat()}"
    text, n_title = re.subn(
        r"<title>.*?</title>",
        f"<title>{escape(full_title)}</title>",
        text,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if n_title != 1:
        print("Stamp: could not replace <title>", file=sys.stderr)
        return False

    new_p = f'  <p class="page-updated">Updated on {when.isoformat()}</p>'
    if re.search(r'<p class="page-updated">', text):
        text = re.sub(
            r'<p class="page-updated">.*?</p>',
            new_p,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        text, n_h1 = re.subn(
            r"(<h1>Deep links</h1>)",
            rf"\1\n{new_p}",
            text,
            count=1,
        )
        if n_h1 != 1:
            print("Stamp: could not insert page-updated after <h1>", file=sys.stderr)
            return False

    if ".page-updated {" not in text:
        needle = "    .lead {"
        insert = """    .page-updated {
      color: var(--muted);
      font-size: 0.82rem;
      margin: -4px 0 12px;
      font-weight: 500;
    }
    .lead {"""
        if needle in text:
            text = text.replace(needle, insert, 1)

    path.write_text(text, encoding="utf-8")
    print(f"Stamp: {path.name} — updated on {when.isoformat()}")
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--site-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Folder containing the tappable deeplinks HTML (default: this script's directory)",
    )
    p.add_argument(
        "--date",
        type=str,
        default="",
        help="ISO date YYYY-MM-DD (default: today local)",
    )
    args = p.parse_args(argv)
    d: date | None = None
    if args.date.strip():
        d = date.fromisoformat(args.date.strip())
    return 0 if stamp(args.site_root, d) else 1


if __name__ == "__main__":
    sys.exit(main())
