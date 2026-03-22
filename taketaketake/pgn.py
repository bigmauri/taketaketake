"""
taketaketake/pgn.py
===================
Multi-game PGN parser and GameTree serialiser.

Supported features:
- Multi-game PGN files separated by [Event ...] headers
- Nested variations to any depth via an iterative stack-based parser
- Comments { text }
- NAG values $1–$6
- Move numbers attached directly to SAN tokens (e.g. "1.e4")
- Castling O-O / O-O-O and 0-0 / 0-0-0
- Promotion with = (e.g. e8=Q)

Internal dependencies: constants, engine, tree.
Does NOT depend on tkinter.
"""

import copy
import datetime
import re

from .constants import NAG_SYM
from .engine   import apply_move, san_to_move, opponent
from .tree     import GameTree, MoveNode


# ─────────────────────────────────────────────────────────────────────────────
# TOKENISER
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize_pgn_body(body: str) -> list[str]:
    """
    Split the move-text section of a PGN game into meaningful tokens.

    Parentheses ``(`` and ``)`` are emitted as individual tokens so that
    the stack parser can handle nested variations correctly.
    """
    pattern = (
        r"(\{[^}]*\}"                    # comment { ... }
        r"|\("                           # variation open
        r"|\)"                           # variation close
        r"|\$\d+"                        # NAG $N
        r"|1-0|0-1|1/2-1/2|\*"          # game results
        r"|\d+\.+"                       # move numbers  1.  3...
        r"|[^\s{}()$\d][^\s{}()]*"       # SAN token starting with letter/symbol
        r"|[^\s{}()]+)"                  # any other non-whitespace token
    )
    return re.findall(pattern, body)


# ─────────────────────────────────────────────────────────────────────────────
# PARSER  (iterative stack — supports arbitrarily nested variations)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_variation_stack(tokens: list[str], tree: GameTree) -> None:
    """
    Build the move tree from PGN tokens using an explicit stack, avoiding
    recursion so that deeply nested files do not hit Python's call limit.

    Each stack element holds the current context:
    ``(parent, board, color, move_num)``.
    """
    stack: list[tuple] = [(tree, copy.deepcopy(tree.board), "w", 1)]
    last_node_at_depth: dict[int, MoveNode | None] = {0: None}
    depth = 0

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # ── Variation open ───────────────────────────────────────────────────
        if tok == "(":
            ln = last_node_at_depth.get(depth)
            if ln and ln.parent is not None:
                fork_parent = ln.parent
                fork_board = (
                    fork_parent.board
                    if isinstance(fork_parent, MoveNode)
                    else fork_parent.board
                )
                stack.append((fork_parent, copy.deepcopy(fork_board), ln.color, ln.move_num))
                depth += 1
                last_node_at_depth[depth] = None
            i += 1
            continue

        # ── Variation close ──────────────────────────────────────────────────
        if tok == ")":
            if depth > 0:
                stack.pop()
                depth -= 1
            i += 1
            continue

        parent, board, color, move_num = stack[-1]

        # ── Comment ──────────────────────────────────────────────────────────
        if tok.startswith("{"):
            txt = tok[1:-1].strip()
            ln = last_node_at_depth.get(depth)
            if ln:
                ln.comment = (ln.comment + " " + txt).strip() if ln.comment else txt
            elif isinstance(parent, GameTree):
                parent.comment = (parent.comment + " " + txt).strip() if parent.comment else txt
            i += 1
            continue

        # ── NAG ──────────────────────────────────────────────────────────────
        if tok.startswith("$"):
            nm = re.match(r"\$(\d+)$", tok)
            if nm:
                nag_n = int(nm.group(1))
                ln = last_node_at_depth.get(depth)
                if ln and 1 <= nag_n <= 6:
                    ln.nag = nag_n
            i += 1
            continue

        # ── Move number ──────────────────────────────────────────────────────
        if re.match(r"^\d+\.+$", tok):
            i += 1
            continue

        # ── Game result ──────────────────────────────────────────────────────
        if tok in ("1-0", "0-1", "1/2-1/2", "*"):
            i += 1
            continue

        # ── SAN move (strip any attached move number, e.g. "1.e4") ──────────
        san = re.sub(r"^\d+\.+", "", tok).strip()
        if not san:
            i += 1
            continue

        mv = san_to_move(board, color, san)
        if mv is None:
            i += 1
            continue

        fr, fc, tr, tc, promo = mv
        new_board = apply_move(board, fr, fc, tr, tc, promo)
        node = MoveNode(san, new_board, color, move_num, parent)
        parent.children.append(node)

        new_color = opponent(color)
        new_num   = move_num + 1 if new_color == "w" else move_num
        stack[-1] = (node, new_board, new_color, new_num)
        last_node_at_depth[depth] = node
        i += 1


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — PARSER
# ─────────────────────────────────────────────────────────────────────────────

def parse_pgn(text: str) -> list[GameTree]:
    """
    Parse a PGN string (potentially containing multiple games) and return
    a list of ``GameTree`` objects, one per game found.

    Parameters
    ----------
    text : str
        Raw content of a ``.pgn`` file.

    Returns
    -------
    list[GameTree]
        List of move trees. Empty if no valid game is found.
    """
    trees: list[GameTree] = []
    chunks = re.split(r"(?=\[Event\s)", text)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Extract headers [Tag "Value"]
        headers: dict[str, str] = {}
        for m in re.finditer(r'\[(\w+)\s+"([^"]*)"\]', chunk):
            headers[m.group(1)] = m.group(2)
        if not headers:
            continue

        # Move body: everything after the last ]
        body_start = 0
        for m in re.finditer(r"\[[^\]]*\]", chunk):
            body_start = m.end()
        body = chunk[body_start:]

        tree = GameTree()
        tree.headers = headers
        tree.result  = headers.get("Result", "*")

        tokens = _tokenize_pgn_body(body)
        _parse_variation_stack(tokens, tree)
        trees.append(tree)

    return trees


def parse_pgn_file(path: str, encoding: str = "utf-8") -> list[GameTree]:
    """
    Read a ``.pgn`` file from disk and return the list of GameTree objects.

    Parameters
    ----------
    path : str
        Path to the PGN file.
    encoding : str
        File encoding (default ``utf-8``).
    """
    with open(path, encoding=encoding, errors="replace") as fh:
        return parse_pgn(fh.read())


# ─────────────────────────────────────────────────────────────────────────────
# SERIALISER  (recursive)
# ─────────────────────────────────────────────────────────────────────────────

def _serialize_node(
    parent: GameTree | MoveNode,
    node: MoveNode | None,
    start_color: str,
    start_num: int,
    depth: int,
) -> str:
    """Recursively serialise a tree branch to PGN text."""
    if node is None:
        return ""

    parts: list[str] = []

    # Pre-game comment (only on the GameTree root)
    if isinstance(parent, GameTree) and parent.comment:
        parts.append(f"{{ {parent.comment} }}")

    color    = start_color
    move_num = start_num
    cur: MoveNode | None = node

    while cur is not None:
        # Move number
        if color == "w":
            parts.append(f"{move_num}.")
        elif not parts or not parts[-1].endswith("..."):
            parts.append(f"{move_num}...")

        parts.append(cur.san)

        if cur.nag:
            parts.append(f"${cur.nag}")

        if cur.comment:
            parts.append(f"{{ {cur.comment} }}")

        # Variations (children[1:])
        for var_child in cur.children[1:]:
            var_text = _serialize_node(cur, var_child, cur.color, cur.move_num, depth + 1)
            parts.append(f"( {var_text.strip()} )")

        # Advance along the main line
        if cur.children:
            color = opponent(color)
            if color == "w":
                move_num += 1
            cur = cur.children[0]
        else:
            break

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — SERIALISER
# ─────────────────────────────────────────────────────────────────────────────

def tree_to_pgn(tree: GameTree) -> str:
    """
    Serialise a ``GameTree`` to standard PGN text, including mandatory
    headers, moves, variations, comments, NAG values, and the result.

    The output is wrapped at 80 columns following PGN conventions.

    Parameters
    ----------
    tree : GameTree
        The game tree to serialise.

    Returns
    -------
    str
        Complete PGN text.
    """
    today = datetime.date.today().strftime("%Y.%m.%d")
    h = tree.headers
    header_lines = [
        f'[Event "{h.get("Event", "Local game")}"]',
        f'[Site "{h.get("Site", "Python Chess")}"]',
        f'[Date "{h.get("Date", today)}"]',
        f'[White "{h.get("White", "White")}"]',
        f'[Black "{h.get("Black", "Black")}"]',
        f'[Result "{h.get("Result", tree.result)}"]',
        "",
    ]

    body = _serialize_node(
        tree,
        tree.children[0] if tree.children else None,
        start_color="w",
        start_num=1,
        depth=0,
    )
    body = (body.strip() + " " + tree.result).strip()

    # Wrap at 80 columns
    wrapped_lines: list[str] = []
    line = ""
    for word in body.split():
        if line and len(line) + 1 + len(word) > 80:
            wrapped_lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        wrapped_lines.append(line)

    return "\n".join(header_lines + wrapped_lines)


def tree_to_pgn_file(tree: GameTree, path: str, encoding: str = "utf-8") -> None:
    """
    Serialise a ``GameTree`` and write it to a file.

    Parameters
    ----------
    tree : GameTree
        The game tree to save.
    path : str
        Destination file path.
    encoding : str
        File encoding (default ``utf-8``).
    """
    with open(path, "w", encoding=encoding) as fh:
        fh.write(tree_to_pgn(tree))
