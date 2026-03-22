"""
taketaketake/tree.py
====================
Move tree data structures for representing chess games with full support
for variations, comments, and NAG annotations.

Depends only on taketaketake.engine (for initial_board).
Does NOT import from taketaketake.pgn — no circular imports.
"""

from __future__ import annotations
from .engine import initial_board


# ─────────────────────────────────────────────────────────────────────────────
# MOVE NODE
# ─────────────────────────────────────────────────────────────────────────────

class MoveNode:
    """
    A single node in the move tree.

    Attributes
    ----------
    san      : str
        Move in Standard Algebraic Notation (e.g. "e4", "Nf3", "O-O").
    board    : list
        Board state **after** this move has been played.
    color    : str
        Colour that played this move ("w" or "b").
    move_num : int
        Move number (1-based).
    parent   : MoveNode | GameTree | None
        Parent node in the tree.
    children : list[MoveNode]
        Child nodes: ``children[0]`` is the main line continuation,
        ``children[1:]`` are alternative variations.
    comment  : str
        PGN comment attached to this move (``{ text }`` format).
    nag      : int | None
        Numeric Annotation Glyph (1–6), or None.
    """

    __slots__ = ("san", "board", "color", "move_num", "parent", "children", "comment", "nag")

    def __init__(
        self,
        san: str,
        board: list,
        color: str,
        move_num: int,
        parent: MoveNode | GameTree | None = None,
    ) -> None:
        self.san      = san
        self.board    = board
        self.color    = color
        self.move_num = move_num
        self.parent   = parent
        self.children: list[MoveNode] = []
        self.comment  = ""
        self.nag: int | None = None

    # ── Navigation ───────────────────────────────────────────────────────────

    def is_main_line(self) -> bool:
        """
        Return True if this node is on the main line, i.e. it is the first
        child of its parent.
        """
        if self.parent is None:
            return True
        return bool(self.parent.children) and self.parent.children[0] is self

    def depth(self) -> int:
        """
        Return the variation depth of this node:
        0 = main line, +1 for each variation level.
        """
        d = 0
        n: MoveNode | GameTree = self
        while n.parent is not None and isinstance(n.parent, MoveNode):
            if not n.is_main_line():
                d += 1
            n = n.parent
        # Final hop toward the GameTree root
        if n.parent is not None and not n.is_main_line():
            d += 1
        return d

    def root(self) -> GameTree:
        """Walk up the tree and return the GameTree root."""
        n: MoveNode | GameTree = self
        while isinstance(n, MoveNode):
            n = n.parent  # type: ignore[assignment]
        return n  # type: ignore[return-value]

    def ancestors(self) -> list[MoveNode]:
        """
        Return the list of MoveNode ancestors from the root down to this node
        (excluding the GameTree root itself).
        """
        path: list[MoveNode] = []
        n: MoveNode | GameTree = self
        while isinstance(n, MoveNode):
            path.append(n)
            n = n.parent  # type: ignore[assignment]
        path.reverse()
        return path

    # ── Representation ───────────────────────────────────────────────────────

    def __repr__(self) -> str:
        num = f"{self.move_num}." if self.color == "w" else f"{self.move_num}..."
        return f"<MoveNode {num}{self.san} depth={self.depth()}>"


# ─────────────────────────────────────────────────────────────────────────────
# GAME TREE
# ─────────────────────────────────────────────────────────────────────────────

class GameTree:
    """
    Virtual root of the move tree; represents the starting position before
    any move has been played.

    Attributes
    ----------
    board    : list
        Board in the starting position.
    children : list[MoveNode]
        First-level nodes. ``children[0]`` is the first move of the main
        line; ``children[1:]`` are variations from the starting position.
    comment  : str
        Pre-game comment (before any move).
    headers  : dict[str, str]
        PGN headers (Event, White, Black, Date, Result, …).
    result   : str
        Game result ("1-0", "0-1", "1/2-1/2", or "*").
    """

    def __init__(self) -> None:
        self.board:    list = initial_board()
        self.children: list[MoveNode] = []
        self.comment:  str = ""
        self.headers:  dict[str, str] = {}
        self.result:   str = "*"

    # ── Mutation ─────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset the tree to the starting position."""
        self.board    = initial_board()
        self.children = []
        self.comment  = ""
        self.headers  = {}
        self.result   = "*"

    # ── Queries ──────────────────────────────────────────────────────────────

    def main_line(self) -> list[MoveNode]:
        """
        Return the ordered list of MoveNode objects on the main line,
        always following the first child of each node.
        """
        line: list[MoveNode] = []
        node: MoveNode | None = self.children[0] if self.children else None
        while node:
            line.append(node)
            node = node.children[0] if node.children else None
        return line

    def all_nodes(self) -> list[MoveNode]:
        """
        Return every MoveNode in the tree via a DFS traversal
        (main line + all variations).
        """
        result: list[MoveNode] = []

        def dfs(node: MoveNode) -> None:
            result.append(node)
            for child in node.children:
                dfs(child)

        for child in self.children:
            dfs(child)
        return result

    def find_by_san_path(self, san_list: list[str]) -> MoveNode | None:
        """
        Navigate the tree following the given SAN sequence and return the
        node for the last move, or None if the path does not exist.
        """
        current: MoveNode | GameTree = self
        for san in san_list:
            match = next((ch for ch in current.children if ch.san == san), None)
            if match is None:
                return None
            current = match
        return current if isinstance(current, MoveNode) else None

    def __repr__(self) -> str:
        w = self.headers.get("White", "?")
        b = self.headers.get("Black", "?")
        n = len(self.main_line())
        return f"<GameTree {w} vs {b} — {n} moves, {self.result}>"
