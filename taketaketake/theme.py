"""
taketaketake/theme.py
=====================
Loader for the visual theme configuration file ``taketaketake-theme.json``.

Search order for the config file
---------------------------------
1. Path in the environment variable ``TAKETAKETAKE_THEME`` (full path or dir)
2. Directory passed explicitly to ``load_theme(search_dir=...)``
3. Directory of the running script (``sys.argv[0]``)
4. Parent directory of this package (project root when installed editable)
5. Current working directory (``os.getcwd()``)

If the file is absent or invalid, built-in Slate Blue defaults are used and
a warning is printed to stderr.

Quick test — edit ``taketaketake-theme.json``, restart the app, done.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

THEME_FILENAME = "taketaketake-theme.json"


# ─────────────────────────────────────────────────────────────────────────────
# THEME DATACLASS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Theme:
    """All visual values used by the application (Slate Blue built-in defaults)."""

    theme_name: str = "Slate Blue"

    # Board
    light_sq:   str = "#DEE3E6"
    dark_sq:    str = "#8CA2AD"
    select_clr: str = "#F4F680"
    move_clr:   str = "#ACBF60"
    check_clr:  str = "#D64545"
    square_px:  int = 72

    # Application backgrounds
    bg:         str = "#111A26"
    list_bg:    str = "#1A2535"
    pgn_bg:     str = "#172030"
    var_bg:     str = "#0E1520"
    btn_bg:     str = "#1E2E42"
    btn_act:    str = "#243246"
    border_clr: str = "#2C3E54"
    list_sel:   str = "#243246"

    # Text / foreground colours
    label_fg:          str = "#DEE8F2"
    btn_fg:            str = "#DEE8F2"
    status_fg:         str = "#7EC8E3"
    pgn_head:          str = "#7EC8E3"
    list_head:         str = "#7EC8E3"
    nav_fg:            str = "#7EC8E3"
    pgn_fg:            str = "#8CAEC8"
    list_fg:           str = "#8CAEC8"
    var_fg:            str = "#6AB88A"
    pgn_num_fg:        str = "#456078"
    comment_fg:        str = "#88BBAA"
    nag_inline_fg:     str = "#FFD700"
    comment_box_bg:    str = "#1A1A35"
    comment_box_fg:    str = "#E8DFC0"
    cur_move_fg:       str = "#FFFFFF"   # highlighted move text in PGN panel

    # Fonts
    font_serif:        str = "Georgia"
    font_mono:         str = "Courier"
    font_piece_family: str = "Segoe UI Symbol"
    font_header_size:  int = 14
    font_label_size:   int = 11
    font_btn_size:     int = 10
    font_small_size:   int = 9
    font_tiny_size:    int = 8
    font_mono_size:    int = 11
    font_mono_small:   int = 10
    font_nag_size:     int = 12
    font_nav_size:     int = 14

    # NAG annotations
    nag_info: dict[int, tuple[str, str, str]] = field(default_factory=lambda: {
        1: ("!",  "Good move",        "#6AB88A"),
        2: ("?",  "Mistake",          "#C07070"),
        3: ("!!", "Brilliant move",   "#50A878"),
        4: ("??", "Blunder",          "#A85050"),
        5: ("!?", "Interesting move", "#7090C8"),
        6: ("?!", "Dubious move",     "#A89850"),
    })


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _candidate_paths(search_dir: pathlib.Path | str | None) -> list[pathlib.Path]:
    """
    Return an ordered, deduplicated list of candidate paths.

    Covers every realistic location where a user might place the theme file:
    env-var, explicit arg, script dir, package parent, and cwd.
    """
    seen: set[pathlib.Path] = set()
    candidates: list[pathlib.Path] = []

    def _add(p: pathlib.Path) -> None:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(p)

    # 1. Environment variable: can be a full path OR a directory
    env = os.environ.get("TAKETAKETAKE_THEME", "").strip()
    if env:
        ep = pathlib.Path(env)
        if ep.is_file():
            _add(ep)
        else:
            _add(ep / THEME_FILENAME)

    # 2. Explicit search_dir argument
    if search_dir is not None:
        _add(pathlib.Path(search_dir) / THEME_FILENAME)

    # 3. Directory of the running script (sys.argv[0])
    if sys.argv and sys.argv[0]:
        script_dir = pathlib.Path(sys.argv[0]).resolve().parent
        _add(script_dir / THEME_FILENAME)

    # 4. Parent of the package directory (project root for editable installs
    #    and direct-run usage; may be site-packages parent in regular installs)
    pkg_parent = pathlib.Path(__file__).resolve().parent.parent
    _add(pkg_parent / THEME_FILENAME)

    # 5. Current working directory
    _add(pathlib.Path.cwd() / THEME_FILENAME)

    return candidates


def find_theme_file(
    search_dir: pathlib.Path | str | None = None,
) -> pathlib.Path | None:
    """
    Return the path of ``taketaketake-theme.json``, or ``None`` if not found.

    Search order:
    ``TAKETAKETAKE_THEME`` env-var → *search_dir* → script dir →
    package parent → cwd.
    """
    for p in _candidate_paths(search_dir):
        if p.is_file():
            return p
    return None


# ─────────────────────────────────────────────────────────────────────────────
# VALUE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _hex(val: Any, default: str) -> str:
    if isinstance(val, str) and val.startswith("#") and len(val) in (4, 7, 9):
        return val
    return default


def _int(val: Any, default: int) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _str(val: Any, default: str) -> str:
    return val if isinstance(val, str) and val.strip() else default


# ─────────────────────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────────────────────

def _merge(theme: Theme, data: dict[str, Any]) -> None:
    """Overwrite *theme* with values from the parsed JSON dict."""
    d = Theme()  # defaults used only as fallback per-key

    b = data.get("board", {})
    theme.light_sq   = _hex(b.get("light_square"), d.light_sq)
    theme.dark_sq    = _hex(b.get("dark_square"),  d.dark_sq)
    theme.select_clr = _hex(b.get("selected"),     d.select_clr)
    theme.move_clr   = _hex(b.get("legal_move"),   d.move_clr)
    theme.check_clr  = _hex(b.get("check"),        d.check_clr)
    theme.square_px  = _int(b.get("square_px"),    d.square_px)

    p = data.get("palette", {})
    theme.bg         = _hex(p.get("bg"),       d.bg)
    theme.list_bg    = _hex(p.get("list_bg"),  d.list_bg)
    theme.pgn_bg     = _hex(p.get("pgn_bg"),   d.pgn_bg)
    theme.var_bg     = _hex(p.get("var_bg"),   d.var_bg)
    theme.btn_bg     = _hex(p.get("btn_bg"),   d.btn_bg)
    theme.btn_act    = _hex(p.get("btn_act"),  d.btn_act)
    theme.border_clr = _hex(p.get("border"),   d.border_clr)
    theme.list_sel   = _hex(p.get("list_sel"), d.list_sel)

    t = data.get("text", {})
    accent = _hex(t.get("accent"), d.status_fg)
    theme.label_fg       = _hex(t.get("label"),          d.label_fg)
    theme.btn_fg         = _hex(t.get("button"),         d.btn_fg)
    theme.status_fg      = accent
    theme.pgn_head       = accent
    theme.list_head      = accent
    theme.nav_fg         = accent
    theme.pgn_fg         = _hex(t.get("pgn"),            d.pgn_fg)
    theme.list_fg        = _hex(t.get("list"),           d.list_fg)
    theme.var_fg         = _hex(t.get("variant"),        d.var_fg)
    theme.pgn_num_fg     = _hex(t.get("move_num"),       d.pgn_num_fg)
    theme.comment_fg     = _hex(t.get("comment_fg"),     d.comment_fg)
    theme.nag_inline_fg  = _hex(t.get("nag_inline"),     d.nag_inline_fg)
    theme.comment_box_bg = _hex(t.get("comment_box_bg"), d.comment_box_bg)
    theme.comment_box_fg = _hex(t.get("comment_box_fg"), d.comment_box_fg)
    theme.cur_move_fg    = _hex(t.get("cur_move_fg"),    d.cur_move_fg)

    f = data.get("fonts", {})
    theme.font_serif        = _str(f.get("serif"),        d.font_serif)
    theme.font_mono         = _str(f.get("mono"),         d.font_mono)
    theme.font_piece_family = _str(f.get("piece_family"), d.font_piece_family)
    theme.font_header_size  = _int(f.get("header_size"),  d.font_header_size)
    theme.font_label_size   = _int(f.get("label_size"),   d.font_label_size)
    theme.font_btn_size     = _int(f.get("btn_size"),     d.font_btn_size)
    theme.font_small_size   = _int(f.get("small_size"),   d.font_small_size)
    theme.font_tiny_size    = _int(f.get("tiny_size"),    d.font_tiny_size)
    theme.font_mono_size    = _int(f.get("mono_size"),    d.font_mono_size)
    theme.font_mono_small   = _int(f.get("mono_small"),   d.font_mono_small)
    theme.font_nag_size     = _int(f.get("nag_size"),     d.font_nag_size)
    theme.font_nav_size     = _int(f.get("nav_size"),     d.font_nav_size)

    nag_raw = data.get("nag", {})
    nag_built: dict[int, tuple[str, str, str]] = {}
    for code in range(1, 7):
        raw  = nag_raw.get(str(code), {})
        dflt = d.nag_info[code]
        sym  = _str(raw.get("symbol"),      dflt[0])
        desc = _str(raw.get("description"), dflt[1])
        clr  = _hex(raw.get("colour", raw.get("color")), dflt[2])
        nag_built[code] = (sym, desc, clr)
    theme.nag_info = nag_built

    theme.theme_name = _str(data.get("theme_name"), "Custom")


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def load_theme(
    search_dir: pathlib.Path | str | None = None,
) -> tuple[Theme, pathlib.Path | None]:
    """
    Load the visual theme from ``taketaketake-theme.json``.

    Parameters
    ----------
    search_dir : Path | str | None
        Optional extra directory checked before the standard locations.

    Returns
    -------
    theme : Theme
        Fully populated theme (missing keys fall back to built-in defaults).
    theme_path : Path | None
        Path of the loaded file, or ``None`` if built-in defaults were used.

    Notes
    -----
    To point the loader at a custom file location without code changes, set
    the environment variable::

        export TAKETAKETAKE_THEME=/path/to/my-theme.json
    """
    theme_path = find_theme_file(search_dir)
    theme = Theme()

    if theme_path is None:
        # Print all candidate paths to help the user understand why the file
        # was not found.
        paths_tried = "\n".join(f"    {p}" for p in _candidate_paths(search_dir))
        print(
            f"[taketaketake] '{THEME_FILENAME}' not found — using built-in Slate Blue defaults.\n"
            f"  Searched:\n{paths_tried}\n"
            f"  Tip: place '{THEME_FILENAME}' next to your script, or set the\n"
            f"  TAKETAKETAKE_THEME environment variable to the full file path.",
            file=sys.stderr,
        )
        return theme, None

    try:
        raw = json.loads(theme_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Top-level JSON value must be an object.")
        _merge(theme, raw)
        return theme, theme_path

    except json.JSONDecodeError as exc:
        print(
            f"[taketaketake] '{theme_path}' is not valid JSON ({exc}).\n"
            f"  Using built-in defaults. Fix the file and restart the app.",
            file=sys.stderr,
        )
        return Theme(), None

    except Exception as exc:
        print(
            f"[taketaketake] Could not apply theme from '{theme_path}' ({exc}).\n"
            f"  Using built-in defaults.",
            file=sys.stderr,
        )
        return Theme(), None
