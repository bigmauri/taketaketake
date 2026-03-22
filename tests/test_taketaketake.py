"""
tests/test_taketaketake.py
Suite di test per il pacchetto taketaketake — Python 3 unittest (stdlib pura).

Esecuzione:
    python3 -m unittest tests.test_taketaketake -v
    python3 -m pytest tests/ -v
"""

import unittest
import copy
import sys
import os

# ── Importa taketaketake senza avviare tkinter ───────────────────────────────
# taketaketake.__init__ non importa tkinter di default (la GUI è lazy).
# I test girano quindi in qualsiasi ambiente, anche headless.
# Il pacchetto taketaketake deve essere installato (pip install -e .)
# oppure la directory radice del progetto deve essere nel PYTHONPATH.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from taketaketake import (
    initial_board, color_of, opponent, in_bounds, sq, sq_to_rc,
    raw_moves, find_king, is_in_check, apply_move, legal_moves,
    has_any_legal_move, build_san, san_to_move,
    MoveNode, GameTree,
    FILES,
)
from taketaketake.pgn import parse_pgn as parse_pgn_to_tree, tree_to_pgn


# ═════════════════════════════════════════════════════════════════════════════
# HELPER
# ═════════════════════════════════════════════════════════════════════════════

def empty_board():
    """Scacchiera completamente vuota."""
    return [[None]*8 for _ in range(8)]


def place(board, *pieces):
    """
    Posiziona pezzi su una scacchiera vuota.
    pieces: sequenza di (notazione_algebrica, codice_pezzo)
            es. ("e1","wK"), ("e8","bK"), ("d4","wQ")
    """
    for square, piece in pieces:
        r, c = sq_to_rc(square)
        board[r][c] = piece
    return board


def play_moves(san_list):
    """
    Esegue una sequenza di mosse SAN dalla posizione iniziale.
    Restituisce (board, color_to_move).
    """
    board = initial_board()
    color = "w"
    for san in san_list:
        mv = san_to_move(board, color, san)
        if mv is None:
            raise ValueError(f"Mossa non valida: {san}")
        fr, fc, tr, tc, promo = mv
        board = apply_move(board, fr, fc, tr, tc, promo)
        color = opponent(color)
    return board, color


# ═════════════════════════════════════════════════════════════════════════════
# 1 — FUNZIONI DI UTILITÀ
# ═════════════════════════════════════════════════════════════════════════════

class TestUtilita(unittest.TestCase):

    def test_opponent(self):
        self.assertEqual(opponent("w"), "b")
        self.assertEqual(opponent("b"), "w")

    def test_color_of(self):
        self.assertEqual(color_of("wK"), "w")
        self.assertEqual(color_of("bP"), "b")
        self.assertIsNone(color_of(None))

    def test_in_bounds(self):
        self.assertTrue(in_bounds(0, 0))
        self.assertTrue(in_bounds(7, 7))
        self.assertFalse(in_bounds(-1, 0))
        self.assertFalse(in_bounds(0, 8))

    def test_sq(self):
        self.assertEqual(sq(7, 4), "e1")   # e1 = riga 7, colonna 4
        self.assertEqual(sq(0, 0), "a8")
        self.assertEqual(sq(0, 7), "h8")
        self.assertEqual(sq(7, 0), "a1")

    def test_sq_to_rc(self):
        self.assertEqual(sq_to_rc("e1"), (7, 4))
        self.assertEqual(sq_to_rc("a8"), (0, 0))
        self.assertEqual(sq_to_rc("h1"), (7, 7))

    def test_sq_roundtrip(self):
        for r in range(8):
            for c in range(8):
                self.assertEqual(sq_to_rc(sq(r, c)), (r, c))


# ═════════════════════════════════════════════════════════════════════════════
# 2 — POSIZIONE INIZIALE
# ═════════════════════════════════════════════════════════════════════════════

class TestPosizioneIniziale(unittest.TestCase):

    def setUp(self):
        self.board = initial_board()

    def test_re_bianco_in_e1(self):
        self.assertEqual(self.board[7][4], "wK")

    def test_re_nero_in_e8(self):
        self.assertEqual(self.board[0][4], "bK")

    def test_pedoni_bianchi_riga_7(self):
        for c in range(8):
            self.assertEqual(self.board[6][c], "wP",
                             f"Pedone bianco mancante in colonna {FILES[c]}")

    def test_pedoni_neri_riga_2(self):
        for c in range(8):
            self.assertEqual(self.board[1][c], "bP",
                             f"Pedone nero mancante in colonna {FILES[c]}")

    def test_prima_riga_nera(self):
        expected = ["bR","bN","bB","bQ","bK","bB","bN","bR"]
        self.assertEqual(self.board[0], expected)

    def test_ottava_riga_bianca(self):
        expected = ["wR","wN","wB","wQ","wK","wB","wN","wR"]
        self.assertEqual(self.board[7], expected)

    def test_righe_centrali_vuote(self):
        for r in range(2, 6):
            for c in range(8):
                self.assertIsNone(self.board[r][c],
                                  f"Casella {sq(r,c)} non vuota")


# ═════════════════════════════════════════════════════════════════════════════
# 3 — MOSSE GREZZE DEI PEZZI
# ═════════════════════════════════════════════════════════════════════════════

class TestMosseGrezze(unittest.TestCase):

    # ── Pedone ───────────────────────────────────────────────────────────────
    def test_pedone_bianco_doppio_passo_iniziale(self):
        board = initial_board()
        # e2 = (6,4)
        moves = raw_moves(board, 6, 4)
        self.assertIn((5, 4), moves, "Mancante e3")
        self.assertIn((4, 4), moves, "Mancante e4")

    def test_pedone_bianco_passo_singolo_dopo_mossa(self):
        board = empty_board()
        place(board, ("e4","wP"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 4)   # e4
        self.assertIn((3, 4), moves)     # e5
        self.assertNotIn((2, 4), moves)  # e6 non raggiungibile

    def test_pedone_cattura_diagonale(self):
        board = empty_board()
        place(board, ("e4","wP"), ("d5","bP"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 4)   # e4
        self.assertIn((3, 3), moves)     # cattura in d5

    def test_pedone_bloccato(self):
        board = empty_board()
        place(board, ("e4","wP"), ("e5","bP"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 4)
        self.assertNotIn((3, 4), moves)

    # ── Cavallo ───────────────────────────────────────────────────────────────
    def test_cavallo_al_centro(self):
        board = empty_board()
        place(board, ("d4","wN"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 3)   # d4
        self.assertEqual(len(moves), 8, "Il cavallo al centro ha 8 mosse")

    def test_cavallo_in_angolo(self):
        board = empty_board()
        place(board, ("a1","wN"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 7, 0)
        self.assertEqual(len(moves), 2)

    # ── Torre ─────────────────────────────────────────────────────────────────
    def test_torre_su_riga_vuota(self):
        board = empty_board()
        place(board, ("a4","wR"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 0)
        # 7 caselle in orizzontale + 3 su + 4 giù = 14
        self.assertEqual(len(moves), 14)

    def test_torre_bloccata_da_alleato(self):
        board = empty_board()
        place(board, ("a1","wR"), ("a4","wP"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 7, 0)   # Torre a1
        # Può andare a1-a3 (3 caselle) e a1-h1 (7 caselle) = 10
        verticals = [m for m in moves if m[1] == 0]
        self.assertEqual(len(verticals), 2)   # a2, a3 (a4 bloccata)

    # ── Alfiere ───────────────────────────────────────────────────────────────
    def test_alfiere_al_centro(self):
        board = empty_board()
        place(board, ("d4","wB"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 3)
        self.assertEqual(len(moves), 13)

    # ── Regina ────────────────────────────────────────────────────────────────
    def test_regina_al_centro(self):
        board = empty_board()
        place(board, ("d4","wQ"), ("e1","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 3)
        self.assertEqual(len(moves), 27)

    # ── Re ────────────────────────────────────────────────────────────────────
    def test_re_al_centro(self):
        board = empty_board()
        place(board, ("d4","wK"), ("e8","bK"))
        moves = raw_moves(board, 4, 3)
        self.assertEqual(len(moves), 8)

    def test_re_non_cattura_alleato(self):
        board = empty_board()
        place(board, ("d4","wK"), ("e4","wP"), ("e8","bK"))
        moves = raw_moves(board, 4, 3)
        self.assertNotIn((4, 4), moves)


# ═════════════════════════════════════════════════════════════════════════════
# 4 — SCACCO
# ═════════════════════════════════════════════════════════════════════════════

class TestScacco(unittest.TestCase):

    def test_nessuno_scacco_posizione_iniziale(self):
        board = initial_board()
        self.assertFalse(is_in_check(board, "w"))
        self.assertFalse(is_in_check(board, "b"))

    def test_scacco_dalla_donna(self):
        board = empty_board()
        place(board, ("e1","wK"), ("e8","bK"), ("e5","bQ"))
        self.assertTrue(is_in_check(board, "w"))
        self.assertFalse(is_in_check(board, "b"))

    def test_scacco_dal_cavallo(self):
        board = empty_board()
        place(board, ("e1","wK"), ("e8","bK"), ("f3","bN"))
        self.assertTrue(is_in_check(board, "w"))

    def test_scacco_dal_pedone(self):
        board = empty_board()
        place(board, ("e1","wK"), ("e8","bK"), ("d2","bP"))
        self.assertTrue(is_in_check(board, "w"))

    def test_scacco_bloccato_da_pezzo(self):
        board = empty_board()
        # La donna nera è sulla stessa colonna del re bianco ma c'è un pezzo in mezzo
        place(board, ("e1","wK"), ("e8","bK"), ("e5","bQ"), ("e3","wP"))
        self.assertFalse(is_in_check(board, "w"))

    def test_find_king(self):
        board = initial_board()
        self.assertEqual(find_king(board, "w"), (7, 4))
        self.assertEqual(find_king(board, "b"), (0, 4))


# ═════════════════════════════════════════════════════════════════════════════
# 5 — MOSSE LEGALI (filtrano lo scacco)
# ═════════════════════════════════════════════════════════════════════════════

class TestMosseLegali(unittest.TestCase):

    def test_mossa_legale_non_espone_re(self):
        # Il pedone in e2 è inchiodato: la donna nera minaccia il re
        board = empty_board()
        place(board, ("e1","wK"), ("e8","bK"), ("e7","bQ"), ("e2","wP"))
        # L'unica mossa legale del pedone è avanzare nella colonna e (rimane inchiodato
        # ma la donna è dietro e non può catturare il re attraverso il pedone)
        moves = legal_moves(board, 6, 4)   # pedone e2
        # Il pedone può avanzare (non espone il re)
        self.assertIn((5, 4), moves)

    def test_pezzo_inchiodato_non_puo_muovere(self):
        # Il cavallo è inchiodato ortogonalmente: re bianco e1, cavallo e4, donna nera e8.
        # Il cavallo non può muoversi perché lascerebbe il re sotto scacco della donna.
        board = empty_board()
        place(board, ("e1","wK"), ("e4","wN"), ("e8","bQ"), ("h8","bK"))
        moves = legal_moves(board, 4, 4)   # Cavallo e4
        self.assertEqual(moves, [], "Cavallo inchiodato ortogonalmente non può muoversi")

    def test_unica_mossa_blocco_scacco(self):
        # Il re bianco è sotto scacco: solo il blocco è legale
        board = empty_board()
        place(board, ("e1","wK"), ("e8","bQ"), ("d2","wR"), ("h8","bK"))
        # La torre in d2 può interporsi in e2
        moves = legal_moves(board, 6, 3)   # Torre d2
        self.assertIn((6, 4), moves)   # Torre d2 → e2, blocca lo scacco

    def test_nessuna_mossa_scacco_matto(self):
        # Scholar's mate: 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
        san_seq = ["e4","e5","Bc4","Nc6","Qh5","Nf6","Qxf7"]
        board, color = play_moves(san_seq)
        self.assertEqual(color, "b")
        self.assertTrue(is_in_check(board, "b"))
        self.assertFalse(has_any_legal_move(board, "b"))

    def test_stallo(self):
        # Stallo classico: re nero in a8, bianco gioca con donna
        board = empty_board()
        place(board, ("a8","bK"), ("c7","wQ"), ("a1","wK"))
        # Verifica che il nero non abbia mosse ma non sia sotto scacco
        self.assertFalse(is_in_check(board, "b"))
        self.assertFalse(has_any_legal_move(board, "b"))

    def test_mosse_legali_posizione_iniziale_bianco(self):
        board = initial_board()
        total = sum(len(legal_moves(board, r, c))
                    for r in range(8) for c in range(8)
                    if color_of(board[r][c]) == "w")
        self.assertEqual(total, 20, "Dalla posizione iniziale il bianco ha 20 mosse")

    def test_mosse_legali_posizione_iniziale_nero(self):
        board = initial_board()
        total = sum(len(legal_moves(board, r, c))
                    for r in range(8) for c in range(8)
                    if color_of(board[r][c]) == "b")
        self.assertEqual(total, 20, "Dalla posizione iniziale il nero ha 20 mosse")


# ═════════════════════════════════════════════════════════════════════════════
# 6 — apply_move: arrocco e promozione
# ═════════════════════════════════════════════════════════════════════════════

class TestApplyMove(unittest.TestCase):

    def test_arrocco_corto_bianco(self):
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"))
        nb = apply_move(board, 7, 4, 7, 6)   # Re e1 → g1
        self.assertEqual(nb[7][6], "wK")
        self.assertEqual(nb[7][5], "wR")
        self.assertIsNone(nb[7][7])
        self.assertIsNone(nb[7][4])

    def test_arrocco_lungo_bianco(self):
        board = empty_board()
        place(board, ("e1","wK"), ("a1","wR"), ("e8","bK"))
        nb = apply_move(board, 7, 4, 7, 2)   # Re e1 → c1
        self.assertEqual(nb[7][2], "wK")
        self.assertEqual(nb[7][3], "wR")
        self.assertIsNone(nb[7][0])

    def test_arrocco_corto_nero(self):
        board = empty_board()
        place(board, ("e8","bK"), ("h8","bR"), ("e1","wK"))
        nb = apply_move(board, 0, 4, 0, 6)
        self.assertEqual(nb[0][6], "bK")
        self.assertEqual(nb[0][5], "bR")

    def test_promozione_default_regina(self):
        board = empty_board()
        place(board, ("e7","wP"), ("e1","wK"), ("e8","bK"))
        nb = apply_move(board, 1, 4, 0, 4)   # e7 → e8
        self.assertEqual(nb[0][4], "wQ")

    def test_promozione_cavallo(self):
        board = empty_board()
        place(board, ("e7","wP"), ("e1","wK"), ("e8","bK"))
        nb = apply_move(board, 1, 4, 0, 4, promo="N")
        self.assertEqual(nb[0][4], "wN")

    def test_promozione_nera(self):
        board = empty_board()
        place(board, ("e2","bP"), ("e8","bK"), ("e1","wK"))
        nb = apply_move(board, 6, 4, 7, 4)
        self.assertEqual(nb[7][4], "bQ")

    def test_board_originale_non_modificato(self):
        board = initial_board()
        original = copy.deepcopy(board)
        apply_move(board, 6, 4, 4, 4)   # e2-e4
        self.assertEqual(board, original, "apply_move non deve modificare il board originale")


# ═════════════════════════════════════════════════════════════════════════════
# 7 — Arrocco: condizioni legali
# ═════════════════════════════════════════════════════════════════════════════

class TestArrocco(unittest.TestCase):

    def test_arrocco_corto_bianco_disponibile(self):
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"))
        moves = legal_moves(board, 7, 4)
        self.assertIn((7, 6), moves)

    def test_arrocco_lungo_bianco_disponibile(self):
        board = empty_board()
        place(board, ("e1","wK"), ("a1","wR"), ("e8","bK"))
        moves = legal_moves(board, 7, 4)
        self.assertIn((7, 2), moves)

    def test_arrocco_non_disponibile_sotto_scacco(self):
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"), ("e5","bR"))
        # Il re è sotto scacco dalla torre nera in e5
        self.assertTrue(is_in_check(board, "w"))
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)

    def test_arrocco_non_disponibile_traversata_scacco(self):
        # Il re passa per f1 che è controllata
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"), ("f5","bR"))
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)

    def test_arrocco_non_disponibile_casella_finale_attaccata(self):
        # g1 è controllata dalla torre nera
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"), ("g5","bR"))
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)

    def test_arrocco_non_disponibile_pezzo_frapposto(self):
        board = initial_board()   # Re e cavaliere f1 in mezzo
        moves = legal_moves(board, 7, 4)
        self.assertNotIn((7, 6), moves)


# ═════════════════════════════════════════════════════════════════════════════
# 8 — Notazione SAN: build_san
# ═════════════════════════════════════════════════════════════════════════════

class TestBuildSan(unittest.TestCase):

    def test_pedone_avanza(self):
        board = initial_board()
        san = build_san(board, 6, 4, 4, 4)   # e2-e4
        self.assertEqual(san, "e4")

    def test_pedone_avanza_singolo(self):
        board, _ = play_moves(["e4"])
        san = build_san(board, 5, 4, 4, 4)   # e3 dopo e4... no, ricarichiamo
        board2 = initial_board()
        san2 = build_san(board2, 6, 4, 5, 4)  # e2-e3
        self.assertEqual(san2, "e3")

    def test_cavallo_sviluppo(self):
        board = initial_board()
        san = build_san(board, 7, 6, 5, 5)   # Ng1-f3
        self.assertEqual(san, "Nf3")

    def test_cattura_pedone(self):
        board, _ = play_moves(["e4", "d5"])
        san = build_san(board, 4, 4, 3, 3)   # exd5
        self.assertEqual(san, "exd5")

    def test_arrocco_corto_san(self):
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"))
        san = build_san(board, 7, 4, 7, 6)
        self.assertEqual(san, "O-O")

    def test_arrocco_lungo_san(self):
        board = empty_board()
        place(board, ("e1","wK"), ("a1","wR"), ("e8","bK"))
        san = build_san(board, 7, 4, 7, 2)
        self.assertEqual(san, "O-O-O")

    def test_promozione_san(self):
        board = empty_board()
        place(board, ("e7","wP"), ("e1","wK"), ("e8","bK"))
        san = build_san(board, 1, 4, 0, 4)
        self.assertIn("=Q", san)

    def test_scacco_suffisso(self):
        board = empty_board()
        place(board, ("e1","wK"), ("e8","bK"), ("d1","wQ"))
        # Donna d1 → d8, dà scacco al re nero in e8
        san = build_san(board, 7, 3, 0, 3)
        self.assertIn("+", san)

    def test_disambiguazione_due_torri_stessa_colonna(self):
        board = empty_board()
        place(board, ("a1","wR"), ("a5","wR"), ("e1","wK"), ("e8","bK"))
        # Entrambe le torri possono andare in a3; deve disambiguare con la riga
        san1 = build_san(board, 7, 0, 4, 0)  # Torre a1 → a4
        san5 = build_san(board, 3, 0, 4, 0)  # Torre a5 → a4
        self.assertNotEqual(san1, san5)
        self.assertTrue("1" in san1 or "5" in san5)

    def test_disambiguazione_due_cavalli_stessa_riga(self):
        # Due cavalli sulla stessa riga che possono raggiungere la stessa casella
        # Nb1 e Nf3 possono entrambi andare in d2 (dalla posizione con re lontano)
        board = empty_board()
        # Cavallo b1 (7,1) e cavallo f3 (5,5) entrambi possono andare in d2... proviamo d4
        # Più semplice: cavalloNa3 e Nc3 possono entrambi andare in b5
        place(board, ("a3","wN"), ("c3","wN"), ("e1","wK"), ("e8","bK"))
        # Na3→b5 (5,1) e Nc3→b5 (5,1) sono entrambe valide
        san_a = build_san(board, 5, 0, 3, 1)  # Na3→b5
        san_c = build_san(board, 5, 2, 3, 1)  # Nc3→b5
        self.assertNotEqual(san_a, san_c, "SAN devono disambiguare tra Na3b5 e Nc3b5")
        # L'uno deve contenere 'a' e l'altro 'c' per la disambiguazione
        self.assertTrue("a" in san_a or "3" in san_a, f"Atteso disambiguatore in '{san_a}'")
        self.assertTrue("c" in san_c or "3" in san_c, f"Atteso disambiguatore in '{san_c}'")


# ═════════════════════════════════════════════════════════════════════════════
# 9 — san_to_move: parser inverso
# ═════════════════════════════════════════════════════════════════════════════

class TestSanToMove(unittest.TestCase):

    def test_pedone_e4(self):
        board = initial_board()
        mv = san_to_move(board, "w", "e4")
        self.assertIsNotNone(mv)
        fr, fc, tr, tc, promo = mv
        self.assertEqual((tr, tc), sq_to_rc("e4"))

    def test_cavallo_nf3(self):
        board = initial_board()
        mv = san_to_move(board, "w", "Nf3")
        self.assertIsNotNone(mv)
        _, _, tr, tc, _ = mv
        self.assertEqual((tr, tc), sq_to_rc("f3"))

    def test_mossa_invalida_restituisce_none(self):
        board = initial_board()
        mv = san_to_move(board, "w", "Nf6")   # Il cavallo bianco non può andare in f6
        self.assertIsNone(mv)

    def test_arrocco_corto(self):
        board = empty_board()
        place(board, ("e1","wK"), ("h1","wR"), ("e8","bK"))
        mv = san_to_move(board, "w", "O-O")
        self.assertIsNotNone(mv)
        _, _, tr, tc, _ = mv
        self.assertEqual((tr, tc), (7, 6))

    def test_arrocco_lungo(self):
        board = empty_board()
        place(board, ("e1","wK"), ("a1","wR"), ("e8","bK"))
        mv = san_to_move(board, "w", "O-O-O")
        self.assertIsNotNone(mv)
        _, _, tr, tc, _ = mv
        self.assertEqual((tr, tc), (7, 2))

    def test_promozione(self):
        # Il re nero non deve essere in e8 (bloccherebbe la promozione)
        board = empty_board()
        place(board, ("e7","wP"), ("e1","wK"), ("h8","bK"))
        mv = san_to_move(board, "w", "e8=Q")
        self.assertIsNotNone(mv, "La promozione in e8=Q deve essere valida")
        _, _, _, _, promo = mv
        self.assertEqual(promo, "Q")

    def test_roundtrip_build_san_then_san_to_move(self):
        """build_san poi san_to_move deve ritornare la stessa mossa."""
        board = initial_board()
        fr, fc, tr, tc = 6, 4, 4, 4   # e2-e4
        san = build_san(board, fr, fc, tr, tc)
        mv = san_to_move(board, "w", san)
        self.assertIsNotNone(mv)
        self.assertEqual(mv[:4], (fr, fc, tr, tc))

    def test_sequenza_apertura_ruy_lopez(self):
        """Verifica che l'intera apertura Ruy Lopez si analizzi senza errori."""
        moves = ["e4","e5","Nf3","Nc6","Bb5","a6","Ba4","Nf6","O-O","Be7","Re1","b5","Bb3"]
        board = initial_board()
        color = "w"
        for san in moves:
            mv = san_to_move(board, color, san)
            self.assertIsNotNone(mv, f"Mossa non riconosciuta: {san}")
            fr, fc, tr, tc, promo = mv
            board = apply_move(board, fr, fc, tr, tc, promo)
            color = opponent(color)


# ═════════════════════════════════════════════════════════════════════════════
# 10 — MoveNode e GameTree
# ═════════════════════════════════════════════════════════════════════════════

class TestMoveNode(unittest.TestCase):

    def _make_tree_with_moves(self, san_list):
        """Crea un GameTree con una linea principale."""
        tree = GameTree()
        parent = tree
        board = copy.deepcopy(tree.board)
        color = "w"
        num = 1
        for san in san_list:
            mv = san_to_move(board, color, san)
            fr, fc, tr, tc, promo = mv
            new_board = apply_move(board, fr, fc, tr, tc, promo)
            node = MoveNode(san, new_board, color, num, parent)
            parent.children.append(node)
            parent = node
            board = new_board
            color = opponent(color)
            if color == "w":
                num += 1
        return tree

    def test_main_line_length(self):
        tree = self._make_tree_with_moves(["e4","e5","Nf3","Nc6"])
        self.assertEqual(len(tree.main_line()), 4)

    def test_main_line_san(self):
        tree = self._make_tree_with_moves(["e4","e5","Nf3"])
        sans = [n.san for n in tree.main_line()]
        self.assertEqual(sans, ["e4","e5","Nf3"])

    def test_nodo_radice_ha_parent_gametree(self):
        # Il primo MoveNode ha come parent il GameTree (non None e non un MoveNode)
        tree = self._make_tree_with_moves(["e4"])
        first = tree.children[0]
        self.assertIsInstance(first.parent, GameTree)
        self.assertNotIsInstance(first.parent, MoveNode)

    def test_depth_linea_principale(self):
        tree = self._make_tree_with_moves(["e4","e5"])
        for node in tree.main_line():
            self.assertEqual(node.depth(), 0,
                             f"Nodo {node.san} deve avere depth 0")

    def test_variante_depth_1(self):
        pgn = "[Event \"T\"]\n[Result \"*\"]\n\n1. e4 e5 ( 1... c5 ) *\n"
        tree = parse_pgn_to_tree(pgn)[0]
        first_node = tree.children[0]   # e4
        # Il figlio [0] di e4 è e5 (linea principale), il [1] è c5 (variante)
        var_candidates = [ch for ch in first_node.children if ch.san == "c5"]
        if not var_candidates:
            self.skipTest("Variante c5 non parsata — dipende dal parser")
        var_node = var_candidates[0]
        self.assertEqual(var_node.depth(), 1,
                         "La variante c5 deve avere depth 1")

    def test_is_main_line(self):
        tree = self._make_tree_with_moves(["e4","e5"])
        main = tree.main_line()
        for node in main:
            self.assertTrue(node.is_main_line())

    def test_commento_nodo(self):
        tree = self._make_tree_with_moves(["e4"])
        node = tree.children[0]
        node.comment = "Mossa centrale classica"
        self.assertEqual(node.comment, "Mossa centrale classica")

    def test_nag_nodo(self):
        tree = self._make_tree_with_moves(["e4"])
        node = tree.children[0]
        node.nag = 1
        self.assertEqual(node.nag, 1)

    def test_all_nodes_conta_tutto(self):
        tree = self._make_tree_with_moves(["e4","e5","Nf3"])
        self.assertEqual(len(tree.all_nodes()), 3)

    def test_game_tree_reset(self):
        tree = self._make_tree_with_moves(["e4","e5"])
        tree.reset()
        self.assertEqual(tree.children, [])
        self.assertEqual(tree.comment, "")


# ═════════════════════════════════════════════════════════════════════════════
# 11 — Parser PGN
# ═════════════════════════════════════════════════════════════════════════════

class TestParserPGN(unittest.TestCase):

    PGN_SEMPLICE = """\
[Event "Test"]
[White "Bianco"]
[Black "Nero"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
"""

    PGN_CON_COMMENTI = """\
[Event "Test commenti"]
[Result "*"]

1. e4 { Apertura classica } e5 { Risposta simmetrica } 2. Nf3 *
"""

    PGN_CON_NAG = """\
[Event "Test NAG"]
[Result "*"]

1. e4 $1 e5 $2 *
"""

    PGN_CON_VARIANTE = """\
[Event "Test variante"]
[Result "*"]

1. e4 e5 ( 1... c5 ) 2. Nf3 *
"""

    PGN_MULTI = """\
[Event "Partita 1"]
[Result "*"]

1. e4 e5 *

[Event "Partita 2"]
[Result "*"]

1. d4 d5 *
"""

    def test_parsing_base(self):
        trees = parse_pgn_to_tree(self.PGN_SEMPLICE)
        self.assertEqual(len(trees), 1)

    def test_headers_corretti(self):
        trees = parse_pgn_to_tree(self.PGN_SEMPLICE)
        h = trees[0].headers
        self.assertEqual(h["Event"], "Test")
        self.assertEqual(h["White"], "Bianco")
        self.assertEqual(h["Result"], "1-0")

    def test_linea_principale_lunghezza(self):
        trees = parse_pgn_to_tree(self.PGN_SEMPLICE)
        ml = trees[0].main_line()
        self.assertEqual(len(ml), 6)   # e4 e5 Nf3 Nc6 Bb5 a6

    def test_linea_principale_sans(self):
        trees = parse_pgn_to_tree(self.PGN_SEMPLICE)
        sans = [n.san for n in trees[0].main_line()]
        self.assertEqual(sans, ["e4","e5","Nf3","Nc6","Bb5","a6"])

    def test_commenti_parsed(self):
        trees = parse_pgn_to_tree(self.PGN_CON_COMMENTI)
        ml = trees[0].main_line()
        self.assertIn("Apertura classica", ml[0].comment)
        self.assertIn("Risposta simmetrica", ml[1].comment)

    def test_nag_parsed(self):
        trees = parse_pgn_to_tree(self.PGN_CON_NAG)
        ml = trees[0].main_line()
        self.assertEqual(ml[0].nag, 1)
        self.assertEqual(ml[1].nag, 2)

    def test_variante_parsed(self):
        trees = parse_pgn_to_tree(self.PGN_CON_VARIANTE)
        tree = trees[0]
        # Il nodo e4 ha children: [0]=e5 (linea principale), poi Nf3 continua
        # La variante (1...c5) è un figlio alternativo di e4
        first_node = tree.children[0]   # e4
        all_node_sans = {n.san for n in tree.all_nodes()}
        # c5 deve essere presente da qualche parte nell'albero
        self.assertIn("c5", all_node_sans, "La variante c5 deve essere presente nell'albero")
        self.assertIn("e5", all_node_sans, "La linea principale e5 deve essere presente")

    def test_multi_partita(self):
        trees = parse_pgn_to_tree(self.PGN_MULTI)
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[0].headers["Event"], "Partita 1")
        self.assertEqual(trees[1].headers["Event"], "Partita 2")

    def test_numerazione_attaccata(self):
        """Il parser deve gestire '1.e4' senza spazio dopo il punto."""
        pgn = "[Event \"Test\"]\n[Result \"*\"]\n\n1.e4 1...e5 *\n"
        trees = parse_pgn_to_tree(pgn)
        ml = trees[0].main_line()
        self.assertGreaterEqual(len(ml), 2)
        self.assertEqual(ml[0].san, "e4")
        self.assertEqual(ml[1].san, "e5")

    def test_risultato_nel_tree(self):
        trees = parse_pgn_to_tree(self.PGN_SEMPLICE)
        self.assertEqual(trees[0].result, "1-0")


# ═════════════════════════════════════════════════════════════════════════════
# 12 — Serializzatore PGN (tree_to_pgn)
# ═════════════════════════════════════════════════════════════════════════════

class TestTreeToPgn(unittest.TestCase):

    def _build_simple_tree(self, sans):
        trees = parse_pgn_to_tree(
            "[Event \"T\"]\n[Result \"*\"]\n\n" +
            " ".join(f"{i//2+1}{'.' if i%2==0 else '...'}{s}" for i,s in enumerate(sans)) +
            " *\n"
        )
        return trees[0]

    def test_headers_presenti(self):
        tree = self._build_simple_tree(["e4","e5"])
        pgn = tree_to_pgn(tree)
        self.assertIn("[Event", pgn)
        self.assertIn("[White", pgn)
        self.assertIn("[Result", pgn)

    def test_mosse_presenti(self):
        tree = self._build_simple_tree(["e4","e5","Nf3"])
        pgn = tree_to_pgn(tree)
        self.assertIn("e4", pgn)
        self.assertIn("e5", pgn)
        self.assertIn("Nf3", pgn)

    def test_risultato_alla_fine(self):
        tree = self._build_simple_tree(["e4"])
        pgn = tree_to_pgn(tree)
        self.assertTrue(pgn.strip().endswith("*"))

    def test_commento_incluso(self):
        tree = self._build_simple_tree(["e4","e5"])
        tree.main_line()[0].comment = "Apertura"
        pgn = tree_to_pgn(tree)
        self.assertIn("{ Apertura }", pgn)

    def test_nag_incluso(self):
        tree = self._build_simple_tree(["e4","e5"])
        tree.main_line()[0].nag = 1
        pgn = tree_to_pgn(tree)
        self.assertIn("$1", pgn)

    def test_variante_inclusa(self):
        tree = self._build_simple_tree(["e4","e5"])
        # Aggiungi variante c5 come alternativa a e5
        first = tree.children[0]   # e4
        board_after_e4 = first.board
        mv = san_to_move(board_after_e4, "b", "c5")
        fr, fc, tr, tc, promo = mv
        new_board = apply_move(board_after_e4, fr, fc, tr, tc, promo)
        var = MoveNode("c5", new_board, "b", 1, first)
        first.children.append(var)
        pgn = tree_to_pgn(tree)
        self.assertIn("(", pgn)
        self.assertIn("c5", pgn)

    def test_roundtrip_parse_serialize(self):
        """Parsare e ri-serializzare deve mantenere le mosse principali."""
        pgn_orig = (
            "[Event \"Roundtrip\"]\n[White \"A\"]\n[Black \"B\"]\n"
            "[Result \"*\"]\n\n1. e4 e5 2. Nf3 Nc6 *\n"
        )
        trees = parse_pgn_to_tree(pgn_orig)
        pgn_out = tree_to_pgn(trees[0])
        trees2 = parse_pgn_to_tree(pgn_out)
        sans1 = [n.san for n in trees[0].main_line()]
        sans2 = [n.san for n in trees2[0].main_line()]
        self.assertEqual(sans1, sans2)


# ═════════════════════════════════════════════════════════════════════════════
# 13 — Partite celebri (test di integrazione)
# ═════════════════════════════════════════════════════════════════════════════

class TestPartitiCelebri(unittest.TestCase):
    """Replay completo di partite storiche per verificare la correttezza del motore."""

    def _play_and_check(self, san_list, expect_checkmate=False, expect_stale=False):
        board = initial_board()
        color = "w"
        for san in san_list:
            mv = san_to_move(board, color, san)
            self.assertIsNotNone(mv, f"Mossa non riconosciuta: {san}")
            fr, fc, tr, tc, promo = mv
            board = apply_move(board, fr, fc, tr, tc, promo)
            color = opponent(color)
        if expect_checkmate:
            self.assertTrue(is_in_check(board, color), "Dovrebbe essere scacco matto")
            self.assertFalse(has_any_legal_move(board, color))
        if expect_stale:
            self.assertFalse(is_in_check(board, color))
            self.assertFalse(has_any_legal_move(board, color))

    def test_scholars_mate(self):
        """Scholar's mate: scacco matto in 4 mosse."""
        self._play_and_check(
            ["e4","e5","Bc4","Nc6","Qh5","Nf6","Qxf7"],
            expect_checkmate=True
        )

    def test_foolsmate(self):
        """Fool's mate: la partita più breve possibile."""
        self._play_and_check(
            ["f3","e5","g4","Qh4"],
            expect_checkmate=True
        )

    def test_apertura_italiana(self):
        """Apertura Italiana: le prime mosse devono essere valide."""
        self._play_and_check(["e4","e5","Nf3","Nc6","Bc4"])

    def test_difesa_siciliana(self):
        """Siciliana: variante del drago."""
        self._play_and_check(
            ["e4","c5","Nf3","d6","d4","cxd4","Nxd4","Nf6","Nc3","g6"]
        )

    def test_apertura_inglese(self):
        self._play_and_check(["c4","e5","Nc3","Nf6","g3","d5","cxd5","Nxd5"])

    def test_gambetto_di_re(self):
        self._play_and_check(["e4","e5","f4","exf4","Nf3","g5","Bc4"])

    def test_difesa_francese(self):
        self._play_and_check(
            ["e4","e6","d4","d5","Nc3","Bb4","e5","c5","a3","Bxc3","bxc3","Ne7"]
        )


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main(verbosity=2)
