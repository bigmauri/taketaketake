"""
taketaketake/constants.py
=========================
Graphical constants, colour palette, piece symbols, and NAG definitions.

All visual values are loaded from ``taketaketake-theme.json`` every time
this module is imported into a fresh Python process (i.e. on every app
restart).  The theme file is searched automatically — see ``theme.py`` for
the full search order.

Editing visual appearance
-------------------------
1. Open ``taketaketake-theme.json`` in the project root (or the directory
   you launch the app from).
2. Change any colour, font, or size value.
3. Restart the application — the new values are picked up immediately.

No code changes are needed.  If the file is not found, built-in Slate Blue
defaults are used and a helpful message is printed to stderr.

Module-level names
------------------
All names (``BG``, ``LIGHT_SQ``, ``NAG_INFO``, …) are module attributes
populated from the theme at import time.  The module also exposes
``ACTIVE_THEME`` (the loaded ``Theme`` object) and ``THEME_PATH`` (the
``pathlib.Path`` of the file that was used, or ``None``).
"""

from __future__ import annotations
from .theme import load_theme as _load_theme

# ─────────────────────────────────────────────────────────────────────────────
# Load theme fresh on every module import (= every app restart)
# ─────────────────────────────────────────────────────────────────────────────
ACTIVE_THEME, THEME_PATH = _load_theme()

# ─────────────────────────────────────────────────────────────────────────────
# BOARD
# ─────────────────────────────────────────────────────────────────────────────
LIGHT_SQ   = ACTIVE_THEME.light_sq
DARK_SQ    = ACTIVE_THEME.dark_sq
SELECT_CLR = ACTIVE_THEME.select_clr
MOVE_CLR   = ACTIVE_THEME.move_clr
CHECK_CLR  = ACTIVE_THEME.check_clr

# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION BACKGROUNDS
# ─────────────────────────────────────────────────────────────────────────────
BG         = ACTIVE_THEME.bg
LIST_BG    = ACTIVE_THEME.list_bg
PGN_BG     = ACTIVE_THEME.pgn_bg
VAR_BG     = ACTIVE_THEME.var_bg
BTN_BG     = ACTIVE_THEME.btn_bg
BTN_ACT    = ACTIVE_THEME.btn_act

# ─────────────────────────────────────────────────────────────────────────────
# BORDERS AND SELECTIONS
# ─────────────────────────────────────────────────────────────────────────────
BORDER_CLR = ACTIVE_THEME.border_clr
LIST_SEL   = ACTIVE_THEME.list_sel

# ─────────────────────────────────────────────────────────────────────────────
# TYPOGRAPHY
# ─────────────────────────────────────────────────────────────────────────────
LABEL_FG   = ACTIVE_THEME.label_fg
BTN_FG     = ACTIVE_THEME.btn_fg
STATUS_FG  = ACTIVE_THEME.status_fg
PGN_HEAD   = ACTIVE_THEME.pgn_head
LIST_HEAD  = ACTIVE_THEME.list_head
NAV_FG     = ACTIVE_THEME.nav_fg
PGN_FG     = ACTIVE_THEME.pgn_fg
LIST_FG    = ACTIVE_THEME.list_fg
VAR_FG     = ACTIVE_THEME.var_fg
PGN_NUM_FG = ACTIVE_THEME.pgn_num_fg

# ─────────────────────────────────────────────────────────────────────────────
# BOARD SIZING  (also overridden at runtime by ChessApp._build_ui)
# ─────────────────────────────────────────────────────────────────────────────
SQUARE: int = ACTIVE_THEME.square_px
OFFSET: int = ACTIVE_THEME.square_px // 2

# ─────────────────────────────────────────────────────────────────────────────
# NOTATION
# ─────────────────────────────────────────────────────────────────────────────
FILES = "abcdefgh"

# ─────────────────────────────────────────────────────────────────────────────
# PIECE UNICODE SYMBOLS
# ─────────────────────────────────────────────────────────────────────────────
PIECES: dict[str, str] = {
    "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
    "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
}

# ─────────────────────────────────────────────────────────────────────────────
# NAG — Numeric Annotation Glyphs, PGN standard, values 1–6
# Format: { nag_number: (display_symbol, description, ui_button_colour) }
# ─────────────────────────────────────────────────────────────────────────────
NAG_INFO: dict[int, tuple[str, str, str]] = ACTIVE_THEME.nag_info

# Quick-lookup maps
NAG_SYM: dict[int, str] = {k: v[0] for k, v in NAG_INFO.items()}  # 1 → "!"
SYM_NAG: dict[str, int] = {v[0]: k for k, v in NAG_INFO.items()}  # "!" → 1
