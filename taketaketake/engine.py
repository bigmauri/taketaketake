"""
taketaketake/engine.py
======================
Pure chess logic: board representation, move generation, check/checkmate/
stalemate detection, and SAN notation.

Does not depend on tkinter or any other sub-module of the package.
"""

import copy
import re
from .constants import FILES


# ─────────────────────────────────────────────────────────────────────────────
# BASIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def initial_board() -> list[list[str | None]]:
    """Return an 8×8 board in the standard starting position."""
    b: list[list[str | None]] = [[None] * 8 for _ in range(8)]
    order = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    for c, p in enumerate(order):
        b[0][c] = f"b{p}"
        b[7][c] = f"w{p}"
    for c in range(8):
        b[1][c] = "bP"
        b[6][c] = "wP"
    return b


def color_of(piece: str | None) -> str | None:
    """Return the colour of *piece* ('w' or 'b'), or None for an empty square."""
    return piece[0] if piece else None


def opponent(color: str) -> str:
    """Return the opposing colour."""
    return "b" if color == "w" else "w"


def in_bounds(r: int, c: int) -> bool:
    """Return True if (r, c) is a valid board coordinate."""
    return 0 <= r < 8 and 0 <= c < 8


def sq(r: int, c: int) -> str:
    """Convert (row, col) to algebraic notation, e.g. (6, 4) → 'e2'."""
    return FILES[c] + str(8 - r)


def sq_to_rc(s: str) -> tuple[int, int]:
    """Convert algebraic notation to (row, col), e.g. 'e2' → (6, 4)."""
    return 8 - int(s[1]), FILES.index(s[0])


# ─────────────────────────────────────────────────────────────────────────────
# RAW MOVE GENERATION  (without check filtering)
# ─────────────────────────────────────────────────────────────────────────────

def raw_moves(board: list, r: int, c: int) -> list[tuple[int, int]]:
    """
    Return all theoretically reachable destinations for the piece at (r, c),
    without filtering moves that leave the king in check.
    """
    piece = board[r][c]
    if not piece:
        return []
    col, typ = piece[0], piece[1]
    opp = opponent(col)
    moves: list[tuple[int, int]] = []

    def slide(dr: int, dc: int) -> None:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            if board[nr][nc]:
                if color_of(board[nr][nc]) == opp:
                    moves.append((nr, nc))
                break
            moves.append((nr, nc))
            nr += dr
            nc += dc

    if typ == "P":
        d = -1 if col == "w" else 1
        sr = 6 if col == "w" else 1
        nr = r + d
        if in_bounds(nr, c) and not board[nr][c]:
            moves.append((nr, c))
            if r == sr and not board[r + 2 * d][c]:
                moves.append((r + 2 * d, c))
        for dc in [-1, 1]:
            nc = c + dc
            if in_bounds(nr, nc) and board[nr][nc] and color_of(board[nr][nc]) == opp:
                moves.append((nr, nc))

    elif typ == "N":
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and color_of(board[nr][nc]) != col:
                moves.append((nr, nc))

    elif typ == "B":
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            slide(dr, dc)

    elif typ == "R":
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            slide(dr, dc)

    elif typ == "Q":
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]:
            slide(dr, dc)

    elif typ == "K":
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and color_of(board[nr][nc]) != col:
                    moves.append((nr, nc))

    return moves


# ─────────────────────────────────────────────────────────────────────────────
# CHECK DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def find_king(board: list, color: str) -> tuple[int, int] | None:
    """Return the position of *color*'s king, or None if not found."""
    for r in range(8):
        for c in range(8):
            if board[r][c] == f"{color}K":
                return r, c
    return None


def is_in_check(board: list, color: str) -> bool:
    """Return True if *color*'s king is currently in check."""
    pos = find_king(board, color)
    if not pos:
        return False
    kr, kc = pos
    opp = opponent(color)
    for r in range(8):
        for c in range(8):
            if color_of(board[r][c]) == opp and (kr, kc) in raw_moves(board, r, c):
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# MOVE APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def apply_move(
    board: list,
    fr: int, fc: int,
    tr: int, tc: int,
    promo: str | None = None,
) -> list:
    """
    Apply a move and return a new board (deep copy).
    Handles: normal moves, kingside/queenside castling, pawn promotion.
    The original board is never modified.
    """
    nb = copy.deepcopy(board)
    nb[tr][tc] = nb[fr][fc]
    nb[fr][fc] = None

    # Castling: also move the rook
    if nb[tr][tc] and nb[tr][tc][1] == "K":
        if fc == 4 and tc == 6:    # kingside
            nb[tr][5] = nb[tr][7]
            nb[tr][7] = None
        elif fc == 4 and tc == 2:  # queenside
            nb[tr][3] = nb[tr][0]
            nb[tr][0] = None

    # Promotion
    if nb[tr][tc] == "wP" and tr == 0:
        nb[tr][tc] = f"w{promo or 'Q'}"
    if nb[tr][tc] == "bP" and tr == 7:
        nb[tr][tc] = f"b{promo or 'Q'}"

    return nb


# ─────────────────────────────────────────────────────────────────────────────
# LEGAL MOVE GENERATION  (with check filtering)
# ─────────────────────────────────────────────────────────────────────────────

def legal_moves(board: list, r: int, c: int) -> list[tuple[int, int]]:
    """
    Return all legal destinations for the piece at (r, c),
    including castling moves when available.
    """
    piece = board[r][c]
    if not piece:
        return []
    col = color_of(piece)
    result: list[tuple[int, int]] = []

    for tr, tc in raw_moves(board, r, c):
        nb = apply_move(board, r, c, tr, tc)
        if not is_in_check(nb, col):
            result.append((tr, tc))

    # Castling (checked separately because raw_moves does not include it)
    if piece[1] == "K" and not is_in_check(board, col):
        row = r
        # Kingside
        if (
            board[row][5] is None and board[row][6] is None
            and board[row][7] and board[row][7][1] == "R" and board[row][7][0] == col
        ):
            nb1 = apply_move(board, r, c, row, 5)
            nb2 = apply_move(board, r, c, row, 6)
            if not is_in_check(nb1, col) and not is_in_check(nb2, col):
                result.append((row, 6))
        # Queenside
        if (
            board[row][3] is None and board[row][2] is None and board[row][1] is None
            and board[row][0] and board[row][0][1] == "R" and board[row][0][0] == col
        ):
            nb1 = apply_move(board, r, c, row, 3)
            nb2 = apply_move(board, r, c, row, 2)
            if not is_in_check(nb1, col) and not is_in_check(nb2, col):
                result.append((row, 2))

    return result


def has_any_legal_move(board: list, color: str) -> bool:
    """Return True if *color* has at least one legal move."""
    for r in range(8):
        for c in range(8):
            if color_of(board[r][c]) == color and legal_moves(board, r, c):
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# SAN NOTATION
# ─────────────────────────────────────────────────────────────────────────────

def build_san(
    board: list,
    fr: int, fc: int,
    tr: int, tc: int,
    promo: str | None = None,
) -> str:
    """
    Build the SAN string for the given move.
    Handles: normal moves, captures, castling, promotion, disambiguation,
    check (+) and checkmate (#) suffixes.
    """
    piece = board[fr][fc]
    if not piece:
        return "?"
    col, typ = piece[0], piece[1]
    is_cap = board[tr][tc] is not None
    dest = sq(tr, tc)

    # Castling
    if typ == "K":
        if fc == 4 and tc == 6:
            base = "O-O"
        elif fc == 4 and tc == 2:
            base = "O-O-O"
        else:
            base = None
        if base:
            nb = apply_move(board, fr, fc, tr, tc)
            opp_col = opponent(col)
            if not has_any_legal_move(nb, opp_col) and is_in_check(nb, opp_col):
                base += "#"
            elif is_in_check(nb, opp_col):
                base += "+"
            return base

    # Disambiguation
    piece_sym = "" if typ == "P" else typ
    ambig = [
        (r, c) for r in range(8) for c in range(8)
        if (r, c) != (fr, fc)
        and board[r][c] == piece
        and (tr, tc) in legal_moves(board, r, c)
    ]
    disambig = ""
    if ambig:
        if all(c != fc for _, c in ambig):
            disambig = FILES[fc]
        elif all(r != fr for r, _ in ambig):
            disambig = str(8 - fr)
        else:
            disambig = FILES[fc] + str(8 - fr)

    # Pawn capture: prefix with departure file
    if typ == "P" and is_cap:
        piece_sym = FILES[fc]

    cap = "x" if is_cap else ""
    san = f"{piece_sym}{disambig}{cap}{dest}"

    # Promotion
    if promo:
        san += f"={promo}"
    elif piece == "wP" and tr == 0:
        san += "=Q"
    elif piece == "bP" and tr == 7:
        san += "=Q"

    # Check / checkmate
    nb = apply_move(board, fr, fc, tr, tc, promo)
    opp_col = opponent(col)
    if not has_any_legal_move(nb, opp_col) and is_in_check(nb, opp_col):
        san += "#"
    elif is_in_check(nb, opp_col):
        san += "+"

    return san


def san_to_move(
    board: list,
    color: str,
    san: str,
) -> tuple[int, int, int, int, str | None] | None:
    """
    Parse a SAN string into the tuple (fr, fc, tr, tc, promo).
    Returns None if the move is not legal in the current position.
    """
    clean = san.rstrip("+#!?")

    # Castling
    if clean in ("O-O-O", "0-0-0"):
        row = 7 if color == "w" else 0
        fr, fc = row, 4
        return (fr, fc, row, 2, None) if (row, 2) in legal_moves(board, fr, fc) else None
    if clean in ("O-O", "0-0"):
        row = 7 if color == "w" else 0
        fr, fc = row, 4
        return (fr, fc, row, 6, None) if (row, 6) in legal_moves(board, fr, fc) else None

    # Promotion
    promo: str | None = None
    pm = re.search(r"=([QRBN])$", clean)
    if pm:
        promo = pm.group(1)
        clean = clean[: pm.start()]

    # Destination square
    dm = re.search(r"([a-h][1-8])$", clean)
    if not dm:
        return None
    dest = dm.group(1)
    tr, tc = sq_to_rc(dest)
    prefix = clean[: dm.start()].replace("x", "")

    # Piece type and disambiguation
    if prefix and prefix[0].isupper():
        piece_type = prefix[0]
        disambig = prefix[1:]
    else:
        piece_type = "P"
        disambig = prefix

    piece_code = f"{color}{piece_type}"
    candidates = [
        (r, c)
        for r in range(8) for c in range(8)
        if board[r][c] == piece_code and (tr, tc) in legal_moves(board, r, c)
    ]
    if not candidates:
        return None

    if disambig:
        filtered = []
        for r, c in candidates:
            ok = True
            for ch in disambig:
                if ch.isdigit() and str(8 - r) != ch:
                    ok = False
                    break
                if ch.islower() and FILES[c] != ch:
                    ok = False
                    break
            if ok:
                filtered.append((r, c))
        candidates = filtered

    if len(candidates) != 1:
        return None
    fr, fc = candidates[0]
    return (fr, fc, tr, tc, promo)
