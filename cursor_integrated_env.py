"""If ATLASSIAN_* are unset, copy them from Cursor User settings (terminal.integrated.env.*).

Lets agent-run / html URL subprocesses use the same credentials as the integrated terminal,
without reading settings.json manually each time."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_KEYS = ("ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN")


def _cursor_user_settings_path() -> Path | None:
    home = Path.home()
    if sys.platform == "darwin":
        p = home / "Library/Application Support/Cursor/User/settings.json"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "").strip()
        if not appdata:
            return None
        p = Path(appdata) / "Cursor" / "User" / "settings.json"
    else:
        p = home / ".config/Cursor/User/settings.json"
    return p if p.is_file() else None


def _terminal_env_settings_key() -> str:
    if sys.platform == "darwin":
        return "terminal.integrated.env.osx"
    if sys.platform == "win32":
        return "terminal.integrated.env.windows"
    return "terminal.integrated.env.linux"


def apply_atlassian_from_cursor_settings() -> None:
    """Set ATLASSIAN_EMAIL / ATLASSIAN_API_TOKEN from Cursor settings when missing."""
    if all(os.environ.get(k, "").strip() for k in _KEYS):
        return
    path = _cursor_user_settings_path()
    if path is None:
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return
    block = data.get(_terminal_env_settings_key())
    if not isinstance(block, dict):
        return
    for key in _KEYS:
        if os.environ.get(key, "").strip():
            continue
        val = block.get(key)
        if isinstance(val, str) and val.strip():
            os.environ[key] = val
