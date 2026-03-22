"""
taketaketake
============
Desktop chess application written in pure Python 3 (standard library only).

Package structure
-----------------
taketaketake/
├── __init__.py   ← this file: public API
├── __main__.py   ← entry point: ``python -m taketaketake``
├── constants.py  ← colour palette, board sizing, piece symbols, NAG definitions
├── engine.py     ← pure chess logic (moves, SAN, check detection …)
├── tree.py       ← MoveNode / GameTree data structures
├── pgn.py        ← PGN parser → GameTree, serialiser GameTree → PGN
└── app.py        ← tkinter GUI (ChessApp)

Quick start
-----------
Launch the application::

    python -m taketaketake

Use as a library::

    from taketaketake import initial_board, legal_moves, build_san
    from taketaketake import parse_pgn, tree_to_pgn
    from taketaketake import GameTree, MoveNode
"""

__version__ = "1.0.0"
__author__  = "TakeTakeTake"
__license__ = "MIT"

# ── Chess logic ───────────────────────────────────────────────────────────────
from .engine import (
    initial_board,
    color_of,
    opponent,
    in_bounds,
    sq,
    sq_to_rc,
    raw_moves,
    find_king,
    is_in_check,
    apply_move,
    legal_moves,
    has_any_legal_move,
    build_san,
    san_to_move,
)

# ── Tree structures ───────────────────────────────────────────────────────────
from .tree import (
    MoveNode,
    GameTree,
)

# ── PGN ───────────────────────────────────────────────────────────────────────
from .pgn import (
    parse_pgn,
    parse_pgn_file,
    tree_to_pgn,
    tree_to_pgn_file,
)

# ── Public constants ──────────────────────────────────────────────────────────
from .constants import (
    FILES,
    PIECES,
    NAG_INFO,
    NAG_SYM,
    SYM_NAG,
)

# ── Theme ─────────────────────────────────────────────────────────────────────
from .theme import (
    Theme,
    load_theme,
    find_theme_file,
    THEME_FILENAME,
)
from .constants import (
    ACTIVE_THEME,
    THEME_PATH,
)

# ── Training ──────────────────────────────────────────────────────────────────
from .training import (
    load_training_config,
    find_config_file,
    CONFIG_FILENAME,
)

# ── GUI (imported lazily to avoid requiring tkinter in headless environments) ─
# Use:  from taketaketake.app import ChessApp


def run() -> None:
    """Launch the TakeTakeTake desktop application."""
    from .app import ChessApp
    app = ChessApp()
    app.mainloop()


__all__ = [
    # engine
    "initial_board", "color_of", "opponent", "in_bounds",
    "sq", "sq_to_rc", "raw_moves", "find_king",
    "is_in_check", "apply_move", "legal_moves", "has_any_legal_move",
    "build_san", "san_to_move",
    # tree
    "MoveNode", "GameTree",
    # pgn
    "parse_pgn", "parse_pgn_file", "tree_to_pgn", "tree_to_pgn_file",
    # constants
    "FILES", "PIECES", "NAG_INFO", "NAG_SYM", "SYM_NAG",
    # theme
    "Theme", "load_theme", "find_theme_file", "THEME_FILENAME",
    "ACTIVE_THEME", "THEME_PATH",
    # training
    "load_training_config", "find_config_file", "CONFIG_FILENAME",
    # entry point
    "run",
]
