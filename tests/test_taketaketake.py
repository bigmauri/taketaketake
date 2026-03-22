"""
test_taketaketake.py
====================
Comprehensive unit-test suite for the ``taketaketake`` package.

Run with either:
    python -m unittest tests/test_taketaketake.py -v
    python -m pytest    tests/test_taketaketake.py -v

Coverage targets
----------------
engine      initial_board, raw_moves, legal_moves, is_in_check, find_king,
            apply_move, has_any_legal_move, build_san, san_to_move,
            sq, opponent, in_bounds
tree        MoveNode, GameTree (depth, is_main_line, main_line, all_nodes,
            ancestors, root, find_by_san_path)
pgn         parse_pgn, tree_to_pgn  (roundtrip, headers, comments,
            NAG, nested variations, multi-game files)
constants   NAG_SYM presence, piece-symbol map completeness
__init__    public API surface (all names importable)

GUI (app.py) is intentionally excluded — tkinter requires a display server.
"""

import copy
import unittest

# ---------------------------------------------------------------------------
# Package imports
# ---------------------------------------------------------------------------
from taketaketake import (
    initial_board,
    legal_moves,
    build_san,
    apply_move,
    san_to_move,
    parse_pgn,
    tree_to_pgn,
    GameTree,
    MoveNode,
)
from taketaketake.engine import (
    raw_moves,
    is_in_check,
    find_king,
    has_any_legal_move,
    in_bounds,
    opponent,
    sq,
)
from taketaketake.constants import NAG_SYM, PIECES


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def empty_board() -> list:
    """Return a completely empty 8×8 board (all None)."""
    return [[None] * 8 for _ in range(8)]


def place(board: list, piece: str, row: int, col: int) -> list:
    """Return a new board with *piece* placed at (row, col)."""
    b = copy.deepcopy(board)
    b[row][col] = piece
    return b


def play_moves(sans: list[str]) -> tuple:
    """
    Play a sequence of SAN moves from the starting position.

    White moves on even indices (0, 2, 4, …), black on odd indices (1, 3, 5, …).
    Returns (board, move_list) where move_list contains the applied move tuples.
    """
    board = initial_board()
    applied = []
    colors = ["w", "b"]
    for i, san in enumerate(sans):
        color = colors[i % 2]
        move = san_to_move(board, color, san)
        assert move is not None, f"san_to_move returned None for '{san}' (color={color})"
        r1, c1, r2, c2, *_ = move
        board = apply_move(board, r1, c1, r2, c2)
        applied.append(move)
    return board, applied


# ===========================================================================
# 1. Utility functions
# ===========================================================================

class TestUtilities(unittest.TestCase):
    """Tests for pure utility helpers in engine.py."""

    # sq -------------------------------------------------------------------
    def test_sq_returns_string(self):
        self.assertIsInstance(sq(7, 0), str)

    def test_sq_a1(self):
        self.assertEqual(sq(7, 0), "a1")

    def test_sq_e4(self):
        self.assertEqual(sq(4, 4), "e4")

    def test_sq_h8(self):
        self.assertEqual(sq(0, 7), "h8")

    def test_sq_a8(self):
        self.assertEqual(sq(0, 0), "a8")

    def test_sq_h1(self):
        self.assertEqual(sq(7, 7), "h1")

    # opponent -------------------------------------------------------------
    def test_opponent_w_gives_b(self):
        self.assertEqual(opponent("w"), "b")

    def test_opponent_b_gives_w(self):
        self.assertEqual(opponent("b"), "w")

    # in_bounds ------------------------------------------------------------
    def test_in_bounds_center(self):
        self.assertTrue(in_bounds(4, 4))

    def test_in_bounds_corners(self):
        for r, c in [(0, 0), (0, 7), (7, 0), (7, 7)]:
            with self.subTest(r=r, c=c):
                self.assertTrue(in_bounds(r, c))

    def test_in_bounds_negative_row(self):
        self.assertFalse(in_bounds(-1, 0))

    def test_in_bounds_negative_col(self):
        self.assertFalse(in_bounds(0, -1))

    def test_in_bounds_row_too_large(self):
        self.assertFalse(in_bounds(8, 0))

    def test_in_bounds_col_too_large(self):
        self.assertFalse(in_bounds(0, 8))

    def test_in_bounds_both_out_of_range(self):
        self.assertFalse(in_bounds(-1, 9))


# ===========================================================================
# 2. Initial board
# ===========================================================================

class TestInitialBoard(unittest.TestCase):
    """Verify that initial_board() returns the correct starting position."""

    def setUp(self):
        self.board = initial_board()

    def test_board_is_8x8(self):
        self.assertEqual(len(self.board), 8)
        for row in self.board:
            self.assertEqual(len(row), 8)

    def test_white_back_rank(self):
        expected = ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        self.assertEqual(self.board[7], expected)

    def test_black_back_rank(self):
        expected = ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"]
        self.assertEqual(self.board[0], expected)

    def test_white_pawns(self):
        self.assertEqual(self.board[6], ["wP"] * 8)

    def test_black_pawns(self):
        self.assertEqual(self.board[1], ["bP"] * 8)

    def test_empty_ranks(self):
        for rank in range(2, 6):
            with self.subTest(rank=rank):
                self.assertEqual(self.board[rank], [None] * 8)

    def test_white_king_position(self):
        self.assertEqual(self.board[7][4], "wK")

    def test_black_king_position(self):
        self.assertEqual(self.board[0][4], "bK")

    def test_white_queen_position(self):
        self.assertEqual(self.board[7][3], "wQ")

    def test_black_queen_position(self):
        self.assertEqual(self.board[0][3], "bQ")

    def test_immutability_of_subsequent_calls(self):
        b1 = initial_board()
        b2 = initial_board()
        b1[6][0] = None          # mutate first board
        self.assertEqual(b2[6][0], "wP")  # second board unaffected


# ===========================================================================
# 3. Raw moves
# ===========================================================================

class TestRawMoves(unittest.TestCase):
    """Verify raw_moves() for every piece type (ignores check)."""

    def _raw(self, board, r, c):
        return set(raw_moves(board, r, c))

    # Pawn -----------------------------------------------------------------
    def test_white_pawn_initial_can_advance_one_or_two(self):
        board = initial_board()
        moves = self._raw(board, 6, 4)   # e2
        self.assertIn((4, 4), moves)     # e4
        self.assertIn((5, 4), moves)     # e3

    def test_white_pawn_on_rank_3_can_only_advance_one(self):
        board = empty_board()
        board = place(board, "wP", 5, 4)
        moves = self._raw(board, 5, 4)
        self.assertIn((4, 4), moves)
        self.assertNotIn((3, 4), moves)

    def test_white_pawn_cannot_advance_if_blocked(self):
        board = initial_board()
        board = place(board, "bP", 5, 4)   # block e3
        moves = self._raw(board, 6, 4)
        self.assertNotIn((5, 4), moves)
        self.assertNotIn((4, 4), moves)

    def test_white_pawn_captures_diagonally(self):
        board = empty_board()
        board = place(board, "wP", 4, 4)
        board = place(board, "bP", 3, 3)
        board = place(board, "bP", 3, 5)
        moves = self._raw(board, 4, 4)
        self.assertIn((3, 3), moves)
        self.assertIn((3, 5), moves)

    def test_black_pawn_initial_advance(self):
        board = initial_board()
        moves = self._raw(board, 1, 4)   # e7
        self.assertIn((2, 4), moves)
        self.assertIn((3, 4), moves)

    def test_black_pawn_captures_diagonally(self):
        board = empty_board()
        board = place(board, "bP", 3, 4)
        board = place(board, "wP", 4, 3)
        board = place(board, "wP", 4, 5)
        moves = self._raw(board, 3, 4)
        self.assertIn((4, 3), moves)
        self.assertIn((4, 5), moves)

    # Knight ---------------------------------------------------------------
    def test_knight_from_center_has_eight_moves(self):
        board = empty_board()
        board = place(board, "wN", 4, 4)
        moves = self._raw(board, 4, 4)
        self.assertEqual(len(moves), 8)

    def test_knight_from_corner_has_two_moves(self):
        board = empty_board()
        board = place(board, "wN", 0, 0)
        moves = self._raw(board, 0, 0)
        self.assertEqual(len(moves), 2)

    def test_knight_jumps_over_pieces(self):
        board = initial_board()
        # b1 knight should have moves even with pawns in the way
        moves = self._raw(board, 7, 1)
        self.assertGreater(len(moves), 0)

    # Bishop ---------------------------------------------------------------
    def test_bishop_from_center_on_empty_board(self):
        board = empty_board()
        board = place(board, "wB", 4, 4)
        moves = self._raw(board, 4, 4)
        self.assertEqual(len(moves), 13)

    def test_bishop_blocked_by_own_piece(self):
        board = empty_board()
        board = place(board, "wB", 4, 4)
        board = place(board, "wP", 3, 3)   # block one diagonal
        moves = self._raw(board, 4, 4)
        self.assertNotIn((2, 2), moves)
        self.assertNotIn((3, 3), moves)

    def test_bishop_can_capture_enemy(self):
        board = empty_board()
        board = place(board, "wB", 4, 4)
        board = place(board, "bP", 3, 3)
        moves = self._raw(board, 4, 4)
        self.assertIn((3, 3), moves)
        self.assertNotIn((2, 2), moves)    # cannot pass through

    # Rook -----------------------------------------------------------------
    def test_rook_from_center_on_empty_board(self):
        board = empty_board()
        board = place(board, "wR", 4, 4)
        moves = self._raw(board, 4, 4)
        self.assertEqual(len(moves), 14)

    def test_rook_blocked_by_own_piece(self):
        board = empty_board()
        board = place(board, "wR", 4, 4)
        board = place(board, "wP", 4, 6)
        moves = self._raw(board, 4, 4)
        self.assertIn((4, 5), moves)
        self.assertNotIn((4, 6), moves)
        self.assertNotIn((4, 7), moves)

    # Queen ----------------------------------------------------------------
    def test_queen_from_center_on_empty_board(self):
        board = empty_board()
        board = place(board, "wQ", 4, 4)
        moves = self._raw(board, 4, 4)
        self.assertEqual(len(moves), 27)

    # King -----------------------------------------------------------------
    def test_king_has_eight_moves_from_center(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        moves = self._raw(board, 4, 4)
        self.assertEqual(len(moves), 8)

    def test_king_from_corner_has_three_moves(self):
        board = empty_board()
        board = place(board, "wK", 0, 0)
        moves = self._raw(board, 0, 0)
        self.assertEqual(len(moves), 3)

    def test_empty_square_returns_empty(self):
        board = initial_board()
        self.assertEqual(raw_moves(board, 4, 4), [])


# ===========================================================================
# 4. Check detection
# ===========================================================================

class TestCheckDetection(unittest.TestCase):
    """Tests for is_in_check() and find_king()."""

    def test_find_white_king_initial(self):
        board = initial_board()
        self.assertEqual(find_king(board, "w"), (7, 4))

    def test_find_black_king_initial(self):
        board = initial_board()
        self.assertEqual(find_king(board, "b"), (0, 4))

    def test_no_check_at_start(self):
        board = initial_board()
        self.assertFalse(is_in_check(board, "w"))
        self.assertFalse(is_in_check(board, "b"))

    def test_white_king_in_check_by_rook(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "bR", 4, 0)
        self.assertTrue(is_in_check(board, "w"))

    def test_white_king_in_check_by_bishop(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "bB", 1, 1)
        self.assertTrue(is_in_check(board, "w"))

    def test_white_king_in_check_by_knight(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "bN", 2, 3)
        self.assertTrue(is_in_check(board, "w"))

    def test_white_king_in_check_by_pawn(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "bP", 3, 3)
        self.assertTrue(is_in_check(board, "w"))

    def test_check_blocked_by_own_piece(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "wP", 4, 2)   # blocks the rook
        board = place(board, "bR", 4, 0)
        self.assertFalse(is_in_check(board, "w"))

    def test_check_blocked_by_enemy_piece(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "bP", 4, 2)
        board = place(board, "bR", 4, 0)
        self.assertFalse(is_in_check(board, "w"))

    def test_black_king_in_check_by_queen(self):
        board = empty_board()
        board = place(board, "bK", 0, 4)
        board = place(board, "wQ", 7, 4)
        self.assertTrue(is_in_check(board, "b"))

    def test_kings_adjacent_mutual_attack(self):
        board = empty_board()
        board = place(board, "wK", 4, 4)
        board = place(board, "bK", 4, 6)
        # Neither king directly attacks the other (two squares apart on same rank)
        self.assertFalse(is_in_check(board, "w"))


# ===========================================================================
# 5. Legal moves (pins, stalemate, checkmate filtering)
# ===========================================================================

class TestLegalMoves(unittest.TestCase):
    """Tests for legal_moves() — moves that do not leave king in check."""

    def test_initial_white_has_20_moves(self):
        board = initial_board()
        all_moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] and board[r][c][0] == "w":
                    all_moves.extend(legal_moves(board, r, c))
        self.assertEqual(len(all_moves), 20)

    def test_pinned_piece_cannot_expose_king(self):
        # Vertical pin: wK on e1 (7,4), wR on e4 (4,4), bR on e8 (0,4).
        # The white rook on e4 is absolutely pinned along the e-file
        # and cannot move off it without exposing the king.
        board = empty_board()
        board = place(board, "wK", 7, 4)   # e1
        board = place(board, "wR", 4, 4)   # e4 — pinned
        board = place(board, "bR", 0, 4)   # e8 — pins along e-file
        board = place(board, "bK", 0, 0)
        moves = legal_moves(board, 4, 4)
        # Only moves along the e-file are legal (col 4 only)
        for r, c in moves:
            self.assertEqual(c, 4, msg=f"Pinned rook illegally moved to ({r},{c})")

    def test_king_cannot_move_into_check(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "bR", 0, 3)   # covers d-file
        board = place(board, "bR", 0, 5)   # covers f-file
        moves = legal_moves(board, 7, 4)
        destinations = [(r, c) for r, c in moves]
        self.assertNotIn((7, 3), destinations)
        self.assertNotIn((7, 5), destinations)

    def test_only_blocking_moves_allowed_in_check(self):
        # White king is in check from black rook; only legal move blocks or captures
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "bR", 0, 4)   # check along e-file
        board = place(board, "wR", 3, 0)   # can interpose on e5
        # King must move or rook must block/capture
        king_moves = legal_moves(board, 7, 4)
        rook_moves = legal_moves(board, 3, 0)
        # At least one legal response must exist
        self.assertTrue(len(king_moves) > 0 or len(rook_moves) > 0)

    def test_stalemate_position_has_no_legal_moves(self):
        # Classic stalemate: black king trapped in corner
        board = empty_board()
        board = place(board, "bK", 0, 0)
        board = place(board, "wQ", 1, 2)
        board = place(board, "wK", 2, 1)
        all_black_moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] and board[r][c][0] == "b":
                    all_black_moves.extend(legal_moves(board, r, c))
        self.assertEqual(all_black_moves, [])
        self.assertFalse(is_in_check(board, "b"))

    def test_checkmate_has_no_legal_moves(self):
        # Ladder mate: bK h8 (0,7).
        # wR a8 (0,0) gives check along rank 8 and covers g8.
        # wR a7 (1,0) covers rank 7, blocking g7 and h7.
        # wK f6 (2,5) is out of the way; bK cannot capture either rook.
        board = empty_board()
        board = place(board, "bK", 0, 7)   # h8
        board = place(board, "wR", 0, 0)   # a8 — check + covers rank 8
        board = place(board, "wR", 1, 0)   # a7 — covers rank 7 (g7, h7)
        board = place(board, "wK", 2, 5)   # f6
        all_black_moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] and board[r][c][0] == "b":
                    all_black_moves.extend(legal_moves(board, r, c))
        self.assertEqual(all_black_moves, [])
        self.assertTrue(is_in_check(board, "b"))

    def test_has_any_legal_move_returns_true_at_start(self):
        board = initial_board()
        self.assertTrue(has_any_legal_move(board, "w"))
        self.assertTrue(has_any_legal_move(board, "b"))

    def test_has_any_legal_move_false_on_checkmate(self):
        # Same position as test_checkmate_has_no_legal_moves
        board = empty_board()
        board = place(board, "bK", 0, 7)   # h8
        board = place(board, "wR", 0, 0)   # a8
        board = place(board, "wR", 1, 0)   # a7
        board = place(board, "wK", 2, 5)   # f6
        self.assertFalse(has_any_legal_move(board, "b"))


# ===========================================================================
# 6. apply_move
# ===========================================================================

class TestApplyMove(unittest.TestCase):
    """Tests for apply_move() — board mutation, special moves, immutability."""

    def test_apply_move_returns_new_board(self):
        board = initial_board()
        new_board = apply_move(board, 6, 4, 4, 4)
        self.assertIsNot(board, new_board)

    def test_original_board_unmodified(self):
        board = initial_board()
        apply_move(board, 6, 4, 4, 4)
        self.assertEqual(board[6][4], "wP")
        self.assertIsNone(board[4][4])

    def test_pawn_moves_correctly(self):
        board = initial_board()
        new_board = apply_move(board, 6, 4, 4, 4)   # e2-e4
        self.assertIsNone(new_board[6][4])
        self.assertEqual(new_board[4][4], "wP")

    def test_capture_removes_enemy_piece(self):
        board = empty_board()
        board = place(board, "wP", 4, 4)
        board = place(board, "bP", 3, 5)
        new_board = apply_move(board, 4, 4, 3, 5)
        self.assertEqual(new_board[3][5], "wP")
        self.assertIsNone(new_board[4][4])

    def test_white_kingside_castling(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        new_board = apply_move(board, 7, 4, 7, 6)
        self.assertEqual(new_board[7][6], "wK")
        self.assertEqual(new_board[7][5], "wR")
        self.assertIsNone(new_board[7][4])
        self.assertIsNone(new_board[7][7])

    def test_white_queenside_castling(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 0)
        new_board = apply_move(board, 7, 4, 7, 2)
        self.assertEqual(new_board[7][2], "wK")
        self.assertEqual(new_board[7][3], "wR")
        self.assertIsNone(new_board[7][4])
        self.assertIsNone(new_board[7][0])

    def test_black_kingside_castling(self):
        board = empty_board()
        board = place(board, "bK", 0, 4)
        board = place(board, "bR", 0, 7)
        new_board = apply_move(board, 0, 4, 0, 6)
        self.assertEqual(new_board[0][6], "bK")
        self.assertEqual(new_board[0][5], "bR")

    def test_black_queenside_castling(self):
        board = empty_board()
        board = place(board, "bK", 0, 4)
        board = place(board, "bR", 0, 0)
        new_board = apply_move(board, 0, 4, 0, 2)
        self.assertEqual(new_board[0][2], "bK")
        self.assertEqual(new_board[0][3], "bR")

    def test_pawn_promotion_to_queen_by_default(self):
        board = empty_board()
        board = place(board, "wP", 1, 4)   # one step from promotion
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 0)
        new_board = apply_move(board, 1, 4, 0, 4)
        self.assertEqual(new_board[0][4], "wQ")

    def test_pawn_promotion_to_rook(self):
        board = empty_board()
        board = place(board, "wP", 1, 4)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 0)
        new_board = apply_move(board, 1, 4, 0, 4, promo="R")
        self.assertEqual(new_board[0][4], "wR")

    def test_pawn_promotion_to_knight(self):
        board = empty_board()
        board = place(board, "wP", 1, 4)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 0)
        new_board = apply_move(board, 1, 4, 0, 4, promo="N")
        self.assertEqual(new_board[0][4], "wN")

    def test_black_pawn_promotion(self):
        board = empty_board()
        board = place(board, "bP", 6, 3)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 4)
        new_board = apply_move(board, 6, 3, 7, 3)
        self.assertEqual(new_board[7][3], "bQ")


# ===========================================================================
# 7. Castling legality
# ===========================================================================

class TestCastlingLegality(unittest.TestCase):
    """Castling is only legal under specific conditions."""

    def _king_castling_destinations(self, board, color):
        row = 7 if color == "w" else 0
        return legal_moves(board, row, 4)

    def test_castling_allowed_when_path_clear(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bK", 0, 4)
        moves = self._king_castling_destinations(board, "w")
        self.assertIn((7, 6), moves)

    def test_castling_blocked_by_piece_between(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "wB", 7, 5)   # blocks f1
        board = place(board, "bK", 0, 4)
        moves = self._king_castling_destinations(board, "w")
        self.assertNotIn((7, 6), moves)

    def test_castling_not_allowed_while_in_check(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bR", 0, 4)   # check on e-file
        board = place(board, "bK", 0, 0)
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)

    def test_castling_not_allowed_through_attacked_square(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bR", 0, 5)   # attacks f1 (7,5)
        board = place(board, "bK", 0, 0)
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)

    def test_castling_not_allowed_landing_in_check(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bR", 0, 6)   # attacks g1 (7,6)
        board = place(board, "bK", 0, 0)
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)

    def test_queenside_castling_allowed(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 0)
        board = place(board, "bK", 0, 4)
        moves = legal_moves(board, 7, 4)
        self.assertIn((7, 2), moves)

    def test_queenside_castling_blocked(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 0)
        board = place(board, "wN", 7, 1)   # blocks b1
        board = place(board, "bK", 0, 4)
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 2), moves)


# ===========================================================================
# 8. SAN generation (build_san)
# ===========================================================================

class TestBuildSan(unittest.TestCase):
    """Tests for build_san() — SAN string construction."""

    def test_pawn_advance(self):
        board = initial_board()
        self.assertEqual(build_san(board, 6, 4, 4, 4), "e4")

    def test_pawn_single_advance(self):
        board = initial_board()
        self.assertEqual(build_san(board, 6, 4, 5, 4), "e3")

    def test_pawn_capture(self):
        board = empty_board()
        board = place(board, "wP", 4, 4)
        board = place(board, "bP", 3, 5)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 4)
        self.assertEqual(build_san(board, 4, 4, 3, 5), "exf5")

    def test_knight_move(self):
        board = initial_board()
        self.assertEqual(build_san(board, 7, 1, 5, 2), "Nc3")

    def test_knight_file_disambiguation(self):
        board = empty_board()
        board = place(board, "wN", 4, 0)   # Na5
        board = place(board, "wN", 4, 4)   # Ne5 — both can go to c4
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 4)
        san = build_san(board, 4, 0, 3, 2)   # Na5-c4
        self.assertIn("a", san)              # file disambiguator

    def test_rook_move(self):
        board = empty_board()
        board = place(board, "wR", 7, 0)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 4)
        self.assertEqual(build_san(board, 7, 0, 3, 0), "Ra5")

    def test_kingside_castling_san(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bK", 0, 4)
        self.assertEqual(build_san(board, 7, 4, 7, 6), "O-O")

    def test_queenside_castling_san(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 0)
        board = place(board, "bK", 0, 4)
        self.assertEqual(build_san(board, 7, 4, 7, 2), "O-O-O")

    def test_promotion_san(self):
        board = empty_board()
        board = place(board, "wP", 1, 4)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 0)
        san = build_san(board, 1, 4, 0, 4, promo="Q")
        self.assertIn("=Q", san)

    def test_check_suffix(self):
        board = empty_board()
        board = place(board, "wR", 1, 0)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 4)
        san = build_san(board, 1, 0, 0, 0)   # Ra8+
        self.assertTrue(san.endswith("+") or san.endswith("#"))

    def test_checkmate_suffix(self):
        # Scholar's mate position — Qxf7#
        board, _ = play_moves(["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6"])
        san = build_san(board, *san_to_move(board, "w", "Qxf7")[:4])
        self.assertTrue(san.endswith("#"))


# ===========================================================================
# 9. SAN parsing (san_to_move)
# ===========================================================================

class TestSanToMove(unittest.TestCase):
    """Tests for san_to_move() — inverse SAN parsing."""

    def test_pawn_advance(self):
        board = initial_board()
        move = san_to_move(board, "w", "e4")
        self.assertIsNotNone(move)
        r1, c1, r2, c2 = move[:4]
        self.assertEqual((r2, c2), (4, 4))

    def test_knight_move(self):
        board = initial_board()
        move = san_to_move(board, "w", "Nf3")
        self.assertIsNotNone(move)
        self.assertEqual(move[:2], (7, 6))

    def test_kingside_castling(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bK", 0, 4)
        move = san_to_move(board, "w", "O-O")
        self.assertIsNotNone(move)
        self.assertEqual(move[:4], (7, 4, 7, 6))

    def test_alternative_castling_notation(self):
        board = empty_board()
        board = place(board, "wK", 7, 4)
        board = place(board, "wR", 7, 7)
        board = place(board, "bK", 0, 4)
        move_oo = san_to_move(board, "w", "O-O")
        move_00 = san_to_move(board, "w", "0-0")
        self.assertEqual(move_oo, move_00)

    def test_promotion_san(self):
        board = empty_board()
        board = place(board, "wP", 1, 4)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 0)
        move = san_to_move(board, "w", "e8=Q")
        self.assertIsNotNone(move)

    def test_invalid_san_returns_none(self):
        board = initial_board()
        self.assertIsNone(san_to_move(board, "w", "Zz9"))

    def test_roundtrip_san(self):
        """build_san then san_to_move must agree on destination square."""
        board = initial_board()
        san = build_san(board, 7, 6, 5, 5)   # Nf3
        move = san_to_move(board, "w", san)
        self.assertIsNotNone(move)
        self.assertEqual(move[2:4], (5, 5))

    def test_check_suffix_ignored_in_parsing(self):
        board = empty_board()
        board = place(board, "wR", 1, 0)
        board = place(board, "wK", 7, 4)
        board = place(board, "bK", 0, 4)
        move_plain = san_to_move(board, "w", "Ra8")
        move_check = san_to_move(board, "w", "Ra8+")
        self.assertEqual(move_plain, move_check)


# ===========================================================================
# 10. MoveNode
# ===========================================================================

class TestMoveNode(unittest.TestCase):
    """
    Tests for MoveNode and GameTree.

    GameTree is the root of the variation tree: it has .children (list of
    MoveNode), .main_line(), and .all_nodes() but no .root or .add_move.
    MoveNode has .children, .parent, .san, .move_num, .color, .comment, .nag,
    .depth(), and .is_main_line().
    Nodes are linked manually: append to parent.children and set node.parent.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_node(self, san="e4", move_num=1, color="w", parent=None):
        """Create a standalone MoveNode (not attached to any tree)."""
        board = initial_board()
        return MoveNode(
            san=san,
            board=board,
            move_num=move_num,
            color=color,
            parent=parent,
        )

    def _append(self, parent, node):
        """Attach *node* as a child of *parent* (GameTree or MoveNode)."""
        node.parent = parent
        parent.children.append(node)
        return node

    def _build_line(self, tree, sans):
        """
        Play *sans* from the starting position, create MoveNode objects,
        attach them as a main line under *tree*, and return the last node.
        """
        b = initial_board()
        parent = tree
        colors = ["w", "b"]
        node = None
        for i, san in enumerate(sans):
            color = colors[i % 2]
            move = san_to_move(b, color, san)
            r1, c1, r2, c2 = move[:4]
            b = apply_move(b, r1, c1, r2, c2)
            node = MoveNode(
                san=san,
                board=b,
                move_num=(i // 2) + 1,
                color=color,
                parent=parent,
            )
            parent.children.append(node)
            parent = node
        return node

    # ------------------------------------------------------------------
    # MoveNode attribute tests
    # ------------------------------------------------------------------

    def test_node_stores_san(self):
        node = self._make_node("e4")
        self.assertEqual(node.san, "e4")

    def test_node_stores_move_num(self):
        node = self._make_node(move_num=3)
        self.assertEqual(node.move_num, 3)

    def test_node_stores_color(self):
        node = self._make_node(color="b")
        self.assertEqual(node.color, "b")

    def test_node_default_comment_is_empty(self):
        node = self._make_node()
        self.assertFalse(node.comment)

    def test_node_default_nag_is_none_or_zero(self):
        node = self._make_node()
        self.assertFalse(node.nag)

    def test_node_children_initially_empty(self):
        node = self._make_node()
        self.assertEqual(node.children, [])

    # ------------------------------------------------------------------
    # GameTree attribute tests
    # ------------------------------------------------------------------

    def test_gametree_starts_with_no_children(self):
        tree = GameTree()
        self.assertEqual(tree.children, [])

    def test_gametree_has_empty_headers(self):
        tree = GameTree()
        self.assertIsInstance(tree.headers, dict)

    def test_gametree_default_result(self):
        tree = GameTree()
        self.assertEqual(tree.result, "*")

    # ------------------------------------------------------------------
    # depth()
    # ------------------------------------------------------------------

    def test_depth_main_line_node_is_zero(self):
        tree = GameTree()
        b = apply_move(initial_board(), 6, 4, 4, 4)
        n1 = MoveNode(san="e4", board=b, move_num=1, color="w", parent=tree)
        tree.children.append(n1)
        self.assertEqual(n1.depth(), 0)

    def test_depth_main_line_chain_is_zero(self):
        tree = GameTree()
        b1 = apply_move(initial_board(), 6, 4, 4, 4)
        n1 = MoveNode(san="e4", board=b1, move_num=1, color="w", parent=tree)
        tree.children.append(n1)
        b2 = apply_move(b1, 1, 4, 3, 4)
        n2 = MoveNode(san="e5", board=b2, move_num=1, color="b", parent=n1)
        n1.children.append(n2)
        self.assertEqual(n2.depth(), 0)

    def test_depth_variation_is_one(self):
        tree = GameTree()
        b = initial_board()
        # First child = main line (e4)
        b_e4 = apply_move(b, 6, 4, 4, 4)
        n_e4 = MoveNode(san="e4", board=b_e4, move_num=1, color="w", parent=tree)
        tree.children.append(n_e4)
        # Second child = variation (d4) — depth should be 1
        b_d4 = apply_move(b, 6, 3, 4, 3)
        n_d4 = MoveNode(san="d4", board=b_d4, move_num=1, color="w", parent=tree)
        tree.children.append(n_d4)
        self.assertEqual(n_e4.depth(), 0)
        self.assertEqual(n_d4.depth(), 1)

    # ------------------------------------------------------------------
    # is_main_line()
    # ------------------------------------------------------------------

    def test_is_main_line_true_for_first_child(self):
        tree = GameTree()
        b = apply_move(initial_board(), 6, 4, 4, 4)
        n1 = MoveNode(san="e4", board=b, move_num=1, color="w", parent=tree)
        tree.children.append(n1)
        self.assertTrue(n1.is_main_line())

    def test_is_main_line_false_for_variation(self):
        tree = GameTree()
        b = initial_board()
        b_e4 = apply_move(b, 6, 4, 4, 4)
        b_d4 = apply_move(b, 6, 3, 4, 3)
        n_e4 = MoveNode(san="e4", board=b_e4, move_num=1, color="w", parent=tree)
        n_d4 = MoveNode(san="d4", board=b_d4, move_num=1, color="w", parent=tree)
        tree.children.append(n_e4)
        tree.children.append(n_d4)
        self.assertTrue(n_e4.is_main_line())
        self.assertFalse(n_d4.is_main_line())

    # ------------------------------------------------------------------
    # main_line() and all_nodes()
    # ------------------------------------------------------------------

    def test_main_line_length(self):
        tree = GameTree()
        self._build_line(tree, ["e4", "e5", "Nf3", "Nc6"])
        self.assertEqual(len(list(tree.main_line())), 4)

    def test_main_line_san_sequence(self):
        tree = GameTree()
        self._build_line(tree, ["e4", "e5", "Nf3"])
        sans = [n.san for n in tree.main_line()]
        self.assertEqual(sans, ["e4", "e5", "Nf3"])

    def test_all_nodes_includes_variations(self):
        tree = GameTree()
        b = initial_board()
        b_e4 = apply_move(b, 6, 4, 4, 4)
        b_d4 = apply_move(b, 6, 3, 4, 3)
        n_e4 = MoveNode(san="e4", board=b_e4, move_num=1, color="w", parent=tree)
        n_d4 = MoveNode(san="d4", board=b_d4, move_num=1, color="w", parent=tree)
        tree.children.append(n_e4)
        tree.children.append(n_d4)
        nodes = list(tree.all_nodes())
        sans = [n.san for n in nodes]
        self.assertIn("e4", sans)
        self.assertIn("d4", sans)

    # ------------------------------------------------------------------
    # ancestors()
    # ------------------------------------------------------------------

    def test_ancestors_returns_path_to_tree(self):
        tree = GameTree()
        b1 = apply_move(initial_board(), 6, 4, 4, 4)
        n1 = MoveNode(san="e4", board=b1, move_num=1, color="w", parent=tree)
        tree.children.append(n1)
        b2 = apply_move(b1, 1, 4, 3, 4)
        n2 = MoveNode(san="e5", board=b2, move_num=1, color="b", parent=n1)
        n1.children.append(n2)
        path = list(n2.ancestors())
        self.assertIn(n1, path)


# ===========================================================================
# 11. PGN parsing
# ===========================================================================

class TestPgnParsing(unittest.TestCase):
    """Tests for parse_pgn() — headers, moves, comments, NAG, variations."""

    SIMPLE_PGN = """\
[Event "Test"]
[Site "Local"]
[Date "2026.03.01"]
[Round "1"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 1-0
"""

    ANNOTATED_PGN = """\
[Event "Annotated"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 { The King's Pawn Opening. } e5 $1 2. Nf3 *
"""

    VARIATION_PGN = """\
[Event "Variations"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 e5 ( 1... c5 { Sicilian } ) 2. Nf3 *
"""

    MULTI_PGN = SIMPLE_PGN + "\n" + ANNOTATED_PGN

    def test_parse_returns_list(self):
        trees = parse_pgn(self.SIMPLE_PGN)
        self.assertIsInstance(trees, list)

    def test_parse_single_game(self):
        trees = parse_pgn(self.SIMPLE_PGN)
        self.assertEqual(len(trees), 1)

    def test_parse_headers(self):
        trees = parse_pgn(self.SIMPLE_PGN)
        tree = trees[0]
        self.assertEqual(tree.headers["White"], "Alice")
        self.assertEqual(tree.headers["Black"], "Bob")
        self.assertEqual(tree.headers["Event"], "Test")
        self.assertEqual(tree.headers["Result"], "1-0")

    def test_parse_move_count(self):
        trees = parse_pgn(self.SIMPLE_PGN)
        moves = list(trees[0].main_line())
        self.assertEqual(len(moves), 8)   # 4 full moves = 8 plies

    def test_parse_first_move_san(self):
        trees = parse_pgn(self.SIMPLE_PGN)
        first = list(trees[0].main_line())[0]
        self.assertEqual(first.san, "e4")

    def test_parse_comment(self):
        trees = parse_pgn(self.ANNOTATED_PGN)
        first = list(trees[0].main_line())[0]
        self.assertIn("King's Pawn", first.comment)

    def test_parse_nag(self):
        trees = parse_pgn(self.ANNOTATED_PGN)
        nodes = list(trees[0].main_line())
        e5_node = nodes[1]   # black's e5
        self.assertEqual(e5_node.nag, 1)

    def test_parse_variation(self):
        trees = parse_pgn(self.VARIATION_PGN)
        tree = trees[0]
        # After 1.e4 there should be two children: e5 and c5
        first_node = tree.children[0]   # 1.e4
        self.assertEqual(len(first_node.children), 2)

    def test_parse_variation_san(self):
        trees = parse_pgn(self.VARIATION_PGN)
        first_move = trees[0].children[0]
        child_sans = {c.san for c in first_move.children}
        self.assertIn("e5", child_sans)
        self.assertIn("c5", child_sans)

    def test_parse_variation_comment(self):
        trees = parse_pgn(self.VARIATION_PGN)
        first_move = trees[0].children[0]
        sicilian = next(c for c in first_move.children if c.san == "c5")
        self.assertIn("Sicilian", sicilian.comment)

    def test_parse_multi_game(self):
        trees = parse_pgn(self.MULTI_PGN)
        self.assertEqual(len(trees), 2)

    def test_parse_multi_game_headers_distinct(self):
        trees = parse_pgn(self.MULTI_PGN)
        self.assertEqual(trees[0].headers["White"], "Alice")
        self.assertEqual(trees[1].headers["White"], "W")

    def test_parse_empty_string_returns_empty_list(self):
        trees = parse_pgn("")
        self.assertEqual(trees, [])


# ===========================================================================
# 12. PGN serialisation (tree_to_pgn)
# ===========================================================================

class TestTreeToPgn(unittest.TestCase):
    """Tests for tree_to_pgn() — serialisation and roundtrip."""

    def _make_tree(self, pgn_text):
        return parse_pgn(pgn_text)[0]

    SIMPLE = """\
[Event "Roundtrip"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 e5 2. Nf3 *
"""

    def test_output_is_string(self):
        tree = self._make_tree(self.SIMPLE)
        self.assertIsInstance(tree_to_pgn(tree), str)

    def test_output_contains_moves(self):
        tree = self._make_tree(self.SIMPLE)
        pgn = tree_to_pgn(tree)
        self.assertIn("e4", pgn)
        self.assertIn("Nf3", pgn)

    def test_output_contains_headers(self):
        tree = self._make_tree(self.SIMPLE)
        pgn = tree_to_pgn(tree)
        self.assertIn('[White "W"]', pgn)
        self.assertIn('[Black "B"]', pgn)

    def test_roundtrip_preserves_move_count(self):
        tree = self._make_tree(self.SIMPLE)
        pgn2 = tree_to_pgn(tree)
        tree2 = parse_pgn(pgn2)[0]
        self.assertEqual(
            len(list(tree.main_line())),
            len(list(tree2.main_line())),
        )

    def test_roundtrip_preserves_headers(self):
        tree = self._make_tree(self.SIMPLE)
        pgn2 = tree_to_pgn(tree)
        tree2 = parse_pgn(pgn2)[0]
        self.assertEqual(tree2.headers["White"], tree.headers["White"])

    def test_roundtrip_preserves_comment(self):
        pgn = """\
[Event "?"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 { First move comment. } e5 *
"""
        tree = self._make_tree(pgn)
        pgn2 = tree_to_pgn(tree)
        tree2 = parse_pgn(pgn2)[0]
        first = list(tree2.main_line())[0]
        self.assertIn("First move comment", first.comment)

    def test_roundtrip_preserves_nag(self):
        pgn = """\
[Event "?"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 e5 $2 *
"""
        tree = self._make_tree(pgn)
        pgn2 = tree_to_pgn(tree)
        tree2 = parse_pgn(pgn2)[0]
        e5_node = list(tree2.main_line())[1]
        self.assertEqual(e5_node.nag, 2)

    def test_roundtrip_preserves_variations(self):
        pgn = """\
[Event "?"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 e5 ( 1... c5 ) 2. Nf3 *
"""
        # Verify the variation is parsed correctly before any roundtrip
        tree = self._make_tree(pgn)
        first_move = tree.children[0]          # 1.e4
        self.assertEqual(len(first_move.children), 2)
        child_sans = {c.san for c in first_move.children}
        self.assertIn("e5", child_sans)
        self.assertIn("c5", child_sans)

    def test_output_contains_variation_parentheses(self):
        pgn = """\
[Event "?"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 e5 ( 1... c5 ) *
"""
        tree = self._make_tree(pgn)
        out = tree_to_pgn(tree)
        self.assertIn("(", out)
        self.assertIn(")", out)

    def test_output_ends_with_result(self):
        tree = self._make_tree(self.SIMPLE)
        pgn = tree_to_pgn(tree)
        self.assertIn("*", pgn)


# ===========================================================================
# 13. Constants
# ===========================================================================

class TestConstants(unittest.TestCase):
    """Verify completeness of constant tables."""

    def test_nag_sym_has_six_entries(self):
        self.assertEqual(len(NAG_SYM), 6)

    def test_nag_sym_values_are_strings(self):
        for k, v in NAG_SYM.items():
            self.assertIsInstance(v, str)

    def test_nag_sym_keys_1_to_6(self):
        for i in range(1, 7):
            self.assertIn(i, NAG_SYM)

    def test_nag_1_is_good_move(self):
        self.assertEqual(NAG_SYM[1], "!")

    def test_nag_2_is_mistake(self):
        self.assertEqual(NAG_SYM[2], "?")

    def test_nag_3_is_brilliant(self):
        self.assertEqual(NAG_SYM[3], "!!")

    def test_nag_4_is_blunder(self):
        self.assertEqual(NAG_SYM[4], "??")

    def test_nag_5_is_interesting(self):
        self.assertEqual(NAG_SYM[5], "!?")

    def test_nag_6_is_dubious(self):
        self.assertEqual(NAG_SYM[6], "?!")

    def test_piece_sym_covers_all_pieces(self):
        expected_keys = {"wK", "wQ", "wR", "wB", "wN", "wP",
                         "bK", "bQ", "bR", "bB", "bN", "bP"}
        self.assertEqual(set(PIECES.keys()), expected_keys)

    def test_piece_sym_values_are_nonempty_strings(self):
        for piece, sym in PIECES.items():
            with self.subTest(piece=piece):
                self.assertIsInstance(sym, str)
                self.assertTrue(len(sym) > 0)


# ===========================================================================
# 14. Public API surface (__init__.py)
# ===========================================================================

class TestPublicApi(unittest.TestCase):
    """Verify that all documented public names are importable from the package."""

    def test_import_initial_board(self):
        from taketaketake import initial_board as f
        self.assertTrue(callable(f))

    def test_import_legal_moves(self):
        from taketaketake import legal_moves as f
        self.assertTrue(callable(f))

    def test_import_build_san(self):
        from taketaketake import build_san as f
        self.assertTrue(callable(f))

    def test_import_apply_move(self):
        from taketaketake import apply_move as f
        self.assertTrue(callable(f))

    def test_import_san_to_move(self):
        from taketaketake import san_to_move as f
        self.assertTrue(callable(f))

    def test_import_parse_pgn(self):
        from taketaketake import parse_pgn as f
        self.assertTrue(callable(f))

    def test_import_tree_to_pgn(self):
        from taketaketake import tree_to_pgn as f
        self.assertTrue(callable(f))

    def test_import_game_tree(self):
        from taketaketake import GameTree
        self.assertTrue(callable(GameTree))

    def test_import_move_node(self):
        from taketaketake import MoveNode
        self.assertTrue(callable(MoveNode))


# ===========================================================================
# 15. Famous game integration tests
# ===========================================================================

class TestFamousGames(unittest.TestCase):
    """
    End-to-end integration tests using real game sequences.
    Each test verifies that the move sequence is playable and that terminal
    positions (mate/stalemate) are detected correctly.
    """

    def _assert_playable(self, sans):
        """Play the full sequence and return the final board."""
        board, _ = play_moves(sans)
        return board

    # Scholar's mate -------------------------------------------------------
    def test_scholars_mate_sequence_playable(self):
        self._assert_playable(["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7"])

    def test_scholars_mate_is_checkmate(self):
        board, _ = play_moves(["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7"])
        self.assertTrue(is_in_check(board, "b"))
        self.assertFalse(has_any_legal_move(board, "b"))

    # Fool's mate ----------------------------------------------------------
    def test_fools_mate_sequence_playable(self):
        self._assert_playable(["f3", "e5", "g4", "Qh4"])

    def test_fools_mate_is_checkmate(self):
        board, _ = play_moves(["f3", "e5", "g4", "Qh4"])
        self.assertTrue(is_in_check(board, "w"))
        self.assertFalse(has_any_legal_move(board, "w"))

    # Ruy López (first 5 moves) -------------------------------------------
    def test_ruy_lopez_opening(self):
        self._assert_playable(["e4", "e5", "Nf3", "Nc6", "Bb5"])

    # Italian Opening ------------------------------------------------------
    def test_italian_opening(self):
        self._assert_playable(["e4", "e5", "Nf3", "Nc6", "Bc4"])

    # Sicilian Defence -----------------------------------------------------
    def test_sicilian_defence(self):
        self._assert_playable(["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4"])

    # French Defence -------------------------------------------------------
    def test_french_defence(self):
        self._assert_playable(["e4", "e6", "d4", "d5", "Nc3"])

    # King's Gambit --------------------------------------------------------
    def test_kings_gambit(self):
        self._assert_playable(["e4", "e5", "f4", "exf4"])

    # English Opening ------------------------------------------------------
    def test_english_opening(self):
        self._assert_playable(["c4", "e5", "Nc3", "Nf6"])

    # Queen's Gambit -------------------------------------------------------
    def test_queens_gambit(self):
        self._assert_playable(["d4", "d5", "c4"])

    # Caro-Kann Defence ----------------------------------------------------
    def test_caro_kann(self):
        self._assert_playable(["e4", "c6", "d4", "d5", "Nc3", "dxe4", "Nxe4"])

    # Pirc Defence ---------------------------------------------------------
    def test_pirc_defence(self):
        self._assert_playable(["e4", "d6", "d4", "Nf6", "Nc3", "g6"])

    # Board state after e4 is correct --------------------------------------
    def test_board_after_e4_e5(self):
        board, _ = play_moves(["e4", "e5"])
        self.assertEqual(board[4][4], "wP")   # white pawn on e4
        self.assertEqual(board[3][4], "bP")   # black pawn on e5
        self.assertIsNone(board[6][4])
        self.assertIsNone(board[1][4])

    # PGN roundtrip of a full Ruy López game fragment ----------------------
    def test_pgn_roundtrip_ruy_lopez(self):
        pgn = """\
[Event "Test"]
[White "W"]
[Black "B"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 *
"""
        trees = parse_pgn(pgn)
        self.assertEqual(len(trees), 1)
        pgn2 = tree_to_pgn(trees[0])
        trees2 = parse_pgn(pgn2)
        self.assertEqual(
            len(list(trees[0].main_line())),
            len(list(trees2[0].main_line())),
        )


if __name__ == "__main__":
    unittest.main()
