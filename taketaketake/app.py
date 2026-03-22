"""
taketaketake.app
================
tkinter desktop application: main window ``ChessApp``.

Depends on all other sub-modules of the package and on tkinter (stdlib).
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import font as tkfont, filedialog, messagebox

# All constants are accessed via the _c module alias (live references)
import taketaketake.constants as _c

from .engine import (
    apply_move, build_san, color_of, has_any_legal_move,
    is_in_check, legal_moves, opponent, san_to_move,
)
from .tree import GameTree, MoveNode
from .pgn      import parse_pgn, tree_to_pgn
from .pieces   import PieceImageCache
from .training import load_training_config
from .theme    import load_theme as _load_app_theme


class ChessApp(tk.Tk):
    """
    Main window of the TakeTakeTake application.

    Opens maximised, computes board sizing from screen resolution, and
    builds the three-column layout:

    - Left   : loaded game list + variant list
    - Centre : board + navigation controls
    - Right  : PGN panel + comment box + NAG buttons
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("TakeTakeTake — Python 3.14")
        self.configure(bg=_c.BG)
        self.resizable(True, True)

        # Maximised window (compatible with Windows, macOS, and most Linux DEs)
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.attributes("-fullscreen", False)
        self.update_idletasks()

        # ── Game state ────────────────────────────────────────────────────────
        self.tree:         GameTree              = GameTree()
        self.current_node: GameTree | MoveNode  = self.tree

        self.selected:    tuple[int, int] | None = None
        self.highlights:  list[tuple[int, int]]  = []
        self.game_over:   bool = False
        self.flipped:     bool = False
        self.replay_mode: bool = False

        # Database of games loaded from file
        self.loaded_games: list[GameTree] = []

        self._variant_mode:   bool = False
        self._training_btn:   tk.Button | None = None
        self._training_panel: tk.Frame  | None = None
        self._comment_updating: bool = False
        self._pgn_click_map:  list  = []   # [(start_idx, end_idx, MoveNode)]

        # Load theme so font/colour values are available in _build_ui
        self._theme, _ = _load_app_theme()
        self._build_ui()
        # Initialise the image cache after _build_ui (which sets _c.SQUARE)
        self._piece_cache = PieceImageCache(
            square_px=_c.SQUARE,
            auto_download=True,
        )
        self._refresh_board()
        self._update_pgn_panel()
        self._update_status()

        # Keyboard shortcuts
        self.bind("<Left>",  lambda e: self._nav_prev())
        self.bind("<Right>", lambda e: self._nav_next())
        self.bind("<Home>",  lambda e: self._nav_start())
        self.bind("<End>",   lambda e: self._nav_end())
        self.bind("<Up>",    lambda e: self._nav_prev_variant())
        self.bind("<Down>",  lambda e: self._nav_next_variant())

    # ═══════════════════════════════════════════════════════════════════════
    # UI
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """Build the UI, adapting sizes to the screen resolution."""
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        reserved_v = 40 + 36 + 50 + 36 + 20
        avail_h = sh - reserved_v

        # Fixed square size: 72 px
        sq  = _c.SQUARE
        off = _c.SQUARE // 2

        # Update the global sizing constants in the constants module
        _c.SQUARE = sq
        _c.OFFSET = off

        board_px = sq * 8 + off * 2
        side_w   = max(200, min(380, (sw - board_px - 80) // 2))

        pgn_h  = max(10, (avail_h - 200) // 18)
        list_h = max(6,  (avail_h // 2)  // 18)
        var_h  = max(4,  (avail_h // 4)  // 18)
        cmt_h  = max(3,  min(6, avail_h // 120))

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=_c.BG, pady=4)
        hdr.pack(fill="x")
        tk.Label(hdr, text="♟  TAKETAKETAKE", bg=_c.BG, fg=_c.STATUS_FG,
                 font=(self._theme.font_serif, max(self._theme.font_header_size, sq // 5), "bold")).pack()

        # ── Three-column body ─────────────────────────────────────────────────
        body = tk.Frame(self, bg=_c.BG)
        body.pack(fill="both", expand=True, padx=10)
        body.grid_columnconfigure(0, minsize=side_w)
        body.grid_columnconfigure(1, weight=0)
        body.grid_columnconfigure(2, minsize=side_w)
        body.grid_rowconfigure(0, weight=1)

        # ── Left column ───────────────────────────────────────────────────────
        left = tk.Frame(body, bg=_c.LIST_BG, bd=0, width=side_w)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_propagate(False)
        left.grid_rowconfigure(2, weight=2)
        left.grid_rowconfigure(7, weight=1)
        left.grid_columnconfigure(0, weight=1)

        tk.Label(left, text="📂  Partite", bg=_c.LIST_BG, fg=_c.LIST_HEAD,
                 font=(self._theme.font_serif, self._theme.font_label_size, "bold"), pady=4
                 ).grid(row=0, column=0, sticky="ew")
        tk.Button(left, text="⊕  Load PGN file", command=self._load_pgn_file, bd=0,
                  bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT,
                  activeforeground=_c.STATUS_FG, relief="flat",
                  font=(self._theme.font_serif, self._theme.font_btn_size), pady=4, cursor="hand2"
                  ).grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 2))

        lf = tk.Frame(left, bg=_c.LIST_BG)
        lf.grid(row=2, column=0, sticky="nsew", padx=4)
        lsb = tk.Scrollbar(lf, bg=_c.BTN_BG, troughcolor=_c.LIST_BG, relief="flat", width=8)
        lsb.pack(side="right", fill="y")
        self.game_listbox = tk.Listbox(
            lf, bg=_c.LIST_BG, fg=_c.LIST_FG,
            selectbackground=_c.LIST_SEL, selectforeground=self._theme.status_fg, bd=0, highlightthickness=1,
            font=(self._theme.font_mono, self._theme.font_mono_small), relief="flat", activestyle="none",
            yscrollcommand=lsb.set, width=0, height=list_h
        )
        self.game_listbox.pack(side="left", fill="both", expand=True)
        lsb.config(command=self.game_listbox.yview)
        self.game_listbox.bind("<<ListboxSelect>>", self._on_game_select)
        self.game_listbox.bind("<Double-Button-1>", self._on_game_load)

        tk.Button(left, text="▶  Load game", command=self._on_game_load,
                  bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT, bd=0,
                  activeforeground=_c.STATUS_FG, relief="flat",
                  font=(self._theme.font_serif, self._theme.font_btn_size), pady=4, cursor="hand2"
                  ).grid(row=3, column=0, sticky="ew", padx=6, pady=(2, 2))

        self._training_btn = tk.Button(
            left, text="🎯  Training", command=self._training_position,
            bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT, bd=0,
            activeforeground=self._theme.label_fg, relief="flat",
            font=(self._theme.font_serif, self._theme.font_btn_size, "bold"), pady=4, cursor="hand2",
            state="disabled",
        )
        self._training_btn.grid(row=4, column=0, sticky="ew", padx=6, pady=(0, 2))

        self.list_info = tk.Label(left, text="", bg=_c.LIST_BG, fg=_c.PGN_NUM_FG,
                                  font=(self._theme.font_serif, self._theme.font_tiny_size), wraplength=side_w - 20,
                                  justify="left")
        self.list_info.grid(row=5, column=0, sticky="ew", padx=6, pady=(0, 2))

        tk.Frame(left, bg=_c.BORDER_CLR, height=1
                 ).grid(row=6, column=0, sticky="ew", padx=6, pady=4)
        tk.Label(left, text="🌿  Varianti", bg=_c.LIST_BG, fg=_c.LIST_HEAD,
                 font=(self._theme.font_serif, self._theme.font_label_size, "bold"), pady=2
                 ).grid(row=6, column=0, sticky="ew", pady=(6, 2))

        vf = tk.Frame(left, bg=_c.LIST_BG)
        vf.grid(row=7, column=0, sticky="nsew", padx=4)
        vsb = tk.Scrollbar(vf, bg=_c.BTN_BG, bd=0, troughcolor=_c.LIST_BG, relief="flat", width=8)
        vsb.pack(side="right", fill="y")
        self.var_listbox = tk.Listbox(
            vf, bg=_c.VAR_BG, fg=_c.VAR_FG,
            selectbackground=_c.LIST_SEL, selectforeground=self._theme.status_fg, bd=0, highlightthickness=1,
            font=(self._theme.font_mono, self._theme.font_mono_small), relief="flat", activestyle="none",
            yscrollcommand=vsb.set, width=0, height=var_h,
        )
        self.var_listbox.pack(side="left", fill="both", expand=True)
        vsb.config(command=self.var_listbox.yview)
        self.var_listbox.bind("<Double-Button-1>", self._on_variant_select)

        vbf = tk.Frame(left, bg=_c.LIST_BG)
        vbf.grid(row=8, column=0, sticky="ew", padx=4, pady=4)
        tk.Button(vbf, text="↩ Enter variation", command=self._on_variant_select,
                  bg=_c.BTN_BG, fg=_c.VAR_FG, activebackground=_c.BTN_ACT, bd=0,
                  relief="flat", font=(self._theme.font_serif, self._theme.font_small_size), pady=6, cursor="hand2"
                  ).pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(vbf, text="✕ Delete", command=self._delete_variant,
                  bg=_c.BTN_BG, fg="#EE6666", activebackground=_c.BTN_ACT,  bd=0,
                  relief="flat", font=(self._theme.font_serif, self._theme.font_small_size), pady=6, cursor="hand2"
                  ).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # ── Centre column ─────────────────────────────────────────────────
        mid = tk.Frame(body, bg=_c.BG)
        mid.grid(row=0, column=1, sticky="ns")

        self.canvas = tk.Canvas(mid, width=board_px, height=board_px,
                                bg=_c.BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        nav = tk.Frame(mid, bg=_c.BG)
        nav.pack(pady=6)
        self.nav_buttons: list[tk.Button] = []
        nav_font_size = max(12, sq // 5)
        nav_defs = [
            ("⏮", self._nav_start,        "Start  [Home]"),
            ("◀",  self._nav_prev,         "Back  [←]"),
            ("▶",  self._nav_next,         "Forward  [→]"),
            ("⏭", self._nav_end,           "End  [End]"),
            ("↑",  self._nav_prev_variant, "Prev. variation  [↑]"),
            ("↓",  self._nav_next_variant, "Next variation  [↓]"),
        ]
        # self._nav_tooltip = tk.Label(nav, text="", bg=_c.BG, fg=_c.PGN_NUM_FG,
        #                              font=(self._theme.font_serif, self._theme.font_tiny_size, "italic"))
        # self._nav_tooltip.pack(side="right", padx=8)
        for sym, cmd, tip in nav_defs:
            b = tk.Button(nav, text=sym, command=cmd, bg=_c.BTN_BG, fg=_c.NAV_FG,
                          activebackground=_c.BTN_ACT, bd=0, relief="flat",
                          font=(self._theme.font_serif, nav_font_size, "bold"),
                          width=3, pady=4, cursor="hand2")
            b.pack(side="left", padx=4)
            # b.bind("<Enter>", lambda e, t=tip: self._nav_tooltip.config(text=t))
            # b.bind("<Leave>", lambda e: self._nav_tooltip.config(text=""))
            self.nav_buttons.append(b)

        btn_row = tk.Frame(mid, bg=_c.BG)
        btn_row.pack(fill="x", padx=6, pady=2)
        tk.Button(btn_row, text="✕  New game", command=self._new_game,
                  bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT, bd=0, relief="flat",
                  font=(self._theme.font_serif, self._theme.font_label_size), pady=5, cursor="hand2"
                  ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(btn_row, text="⇅  Flip", command=self._flip,
                  bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT, bd=0, relief="flat",
                  font=(self._theme.font_serif, self._theme.font_label_size), pady=5, cursor="hand2"
                  ).pack(side="left", fill="x", expand=True, padx=(4, 0))


        # ── Right column ──────────────────────────────────────────────────────
        right = tk.Frame(body, bg=_c.PGN_BG, bd=0, width=side_w)
        right.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        right.grid_propagate(False)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        tk.Label(right, text="📋  Moves (PGN)", bg=_c.PGN_BG, fg=_c.PGN_HEAD,
                 font=(self._theme.font_serif, self._theme.font_label_size, "bold"), pady=4
                 ).grid(row=0, column=0, sticky="ew")

        pf = tk.Frame(right, bg=_c.PGN_BG)
        pf.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 2))
        pf.grid_rowconfigure(0, weight=1)
        pf.grid_columnconfigure(0, weight=1)
        psb = tk.Scrollbar(pf, bg=_c.BTN_BG, troughcolor=_c.PGN_BG, relief="flat", width=8)
        psb.grid(row=0, column=1, sticky="ns")
        self.pgn_text = tk.Text(
            pf, width=0, height=pgn_h, bg=_c.PGN_BG, fg=_c.PGN_FG, bd=0, highlightthickness=1,
            font=(self._theme.font_mono, self._theme.font_mono_size), relief="flat", state="disabled",
            wrap="word", cursor="arrow", yscrollcommand=psb.set,
            selectbackground=_c.BORDER_CLR, padx=6, pady=4,
        )
        self.pgn_text.grid(row=0, column=0, sticky="nsew")
        psb.config(command=self.pgn_text.yview)

        self.pgn_text.tag_configure("num",     foreground=_c.PGN_NUM_FG, font=(self._theme.font_mono, self._theme.font_mono_size, "bold"))
        self.pgn_text.tag_configure("move",    foreground=_c.PGN_FG)
        self.pgn_text.tag_configure("cur",     foreground=self._theme.cur_move_fg, background=_c.LIST_SEL,
                                               font=(self._theme.font_mono, self._theme.font_mono_size, "bold"))
        self.pgn_text.tag_configure("result",  foreground=_c.STATUS_FG, font=(self._theme.font_mono, self._theme.font_mono_size, "bold"))
        self.pgn_text.tag_configure("comment", foreground=self._theme.comment_fg, font=(self._theme.font_mono, self._theme.font_mono_small, "italic"))
        self.pgn_text.tag_configure("nag",     foreground=self._theme.nag_inline_fg, font=(self._theme.font_mono, self._theme.font_mono_size, "bold"))
        self.pgn_text.tag_configure("var",     foreground=_c.VAR_FG,    font=(self._theme.font_mono, self._theme.font_mono_small))
        self.pgn_text.tag_configure("var_cur", foreground=self._theme.status_fg, background=self._theme.list_sel,
                                               font=(self._theme.font_mono, self._theme.font_mono_small, "bold"))
        self.pgn_text.bind("<Button-1>", self._on_pgn_click)

        tk.Button(right, text="⎘  Copy PGN", command=self._copy_pgn,
                  bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT, bd=0, relief="flat",
                  font=(self._theme.font_serif, self._theme.font_btn_size), pady=4, cursor="hand2"
                  ).grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 4))

        # Comment box
        tk.Frame(right, bg=_c.BORDER_CLR, height=1
                 ).grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 2))
        self.comment_label = tk.Label(right, text="💬  Comment", bg=_c.PGN_BG,
                                      fg=_c.PGN_HEAD, font=(self._theme.font_serif, self._theme.font_btn_size, "bold"), pady=2)
        self.comment_label.grid(row=4, column=0, sticky="ew")
        cf = tk.Frame(right, bg=_c.PGN_BG, bd=0)
        cf.grid(row=5, column=0, sticky="ew", padx=6, pady=(0, 2))
        cf.grid_columnconfigure(0, weight=1)
        csb = tk.Scrollbar(cf, bg=_c.BTN_BG, troughcolor=_c.PGN_BG, relief="flat", width=8)
        csb.grid(row=0, column=1, sticky="ns")
        self.comment_text = tk.Text(
            cf, width=0, height=cmt_h,
            bg=self._theme.comment_box_bg, fg=self._theme.comment_box_fg, bd=0, highlightthickness=1,
            font=(self._theme.font_serif, self._theme.font_btn_size), relief="flat", wrap="word",
            yscrollcommand=csb.set, insertbackground=self._theme.status_fg,
            selectbackground=_c.LIST_SEL, padx=6, pady=4,
        )
        self.comment_text.grid(row=0, column=0, sticky="ew")
        csb.config(command=self.comment_text.yview)
        self.comment_text.bind("<<Modified>>", self._on_comment_modified)

        tk.Button(right, text="💾  Save comment", command=self._save_comment,
                  bg=_c.BTN_BG, fg=_c.BTN_FG, activebackground=_c.BTN_ACT, bd=0, relief="flat",
                  font=(self._theme.font_serif, self._theme.font_btn_size), cursor="hand2", pady=4,
                  ).grid(row=6, column=0, sticky="ew", padx=6, pady=(0, 2))

        # NAG buttons
        tk.Frame(right, bg=_c.BORDER_CLR, height=1
                 ).grid(row=7, column=0, sticky="ew", padx=6, pady=(0, 2))
        tk.Label(right, text="NAG", bg=_c.PGN_BG, fg=_c.PGN_NUM_FG,
                 font=(self._theme.font_serif, self._theme.font_small_size, "bold")
                 ).grid(row=8, column=0, sticky="w", padx=8)
        nag_outer = tk.Frame(right, bg=_c.PGN_BG)
        nag_outer.grid(row=9, column=0, sticky="ew", padx=6, pady=(0, 2))
        self.nag_buttons: dict[int, tk.Button] = {}
        for row_items in [[1, 2, 3], [4, 5, 6]]:
            row_f = tk.Frame(nag_outer, bg=_c.PGN_BG)
            row_f.pack(fill="x", pady=1)
            for nag_n in row_items:
                sym, desc, clr = _c.NAG_INFO[nag_n]
                b = tk.Button(row_f, text=sym,
                              command=lambda n=nag_n: self._toggle_nag(n),
                              bg=_c.BTN_BG, fg=clr, activebackground=_c.BTN_ACT, bd=0, 
                              relief="flat", font=(self._theme.font_serif, self._theme.font_nag_size, "bold"),
                              width=3, pady=2, cursor="hand2")
                b.pack(side="left", padx=2)
                b.bind("<Enter>", lambda e, d=desc, s=sym:
                       self._nag_hint_lbl.config(text=f"{s} — {d}"))
                b.bind("<Leave>", lambda e: self._nag_hint_lbl.config(text=""))
                self.nag_buttons[nag_n] = b
        self._nag_hint_lbl = tk.Label(right, text="", bg=_c.PGN_BG, fg=_c.PGN_NUM_FG,
                                      font=(self._theme.font_serif, self._theme.font_tiny_size, "italic"))
        self._nag_hint_lbl.grid(row=10, column=0, sticky="w", padx=8, pady=(0, 4))

        # ── Training overlay (hidden by default, raised in training mode) ──
        self._training_panel = tk.Frame(body, bg=self._theme.list_bg, bd=0, width=side_w)
        self._training_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        self._training_panel.grid_propagate(False)
        self._training_panel.grid_rowconfigure(1, weight=1)
        self._training_panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            self._training_panel, text="🧠  Training Mode",
            bg=self._theme.list_bg, fg=self._theme.status_fg,
            font=(self._theme.font_serif, self._theme.font_label_size, "bold"), pady=6,
        ).grid(row=0, column=0, sticky="ew")

        _tp_canvas = tk.Canvas(self._training_panel, bg=self._theme.list_bg, highlightthickness=0)
        _tp_canvas.grid(row=1, column=0, sticky="nsew")
        _tp_sb = tk.Scrollbar(
            self._training_panel, orient="vertical", command=_tp_canvas.yview,
            bg=self._theme.list_bg, troughcolor=self._theme.list_bg, relief="flat", width=8,
        )
        _tp_sb.grid(row=1, column=1, sticky="ns")
        _tp_canvas.configure(yscrollcommand=_tp_sb.set)

        _tp_inner = tk.Frame(_tp_canvas, bg=self._theme.list_bg)
        _tp_win = _tp_canvas.create_window((0, 0), window=_tp_inner, anchor="nw")

        def _on_inner_cfg(event):
            _tp_canvas.configure(scrollregion=_tp_canvas.bbox("all"))
        def _on_canvas_cfg(event):
            _tp_canvas.itemconfig(_tp_win, width=event.width)
        def _on_wheel(event):
            _tp_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        _tp_inner.bind("<Configure>", _on_inner_cfg)
        _tp_canvas.bind("<Configure>", _on_canvas_cfg)
        _tp_canvas.bind("<MouseWheel>", _on_wheel)

        self._build_training_questions(_tp_inner, side_w)

        _tp_btn_row = tk.Frame(self._training_panel, bg=self._theme.list_bg)
        _tp_btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        tk.Button(
            _tp_btn_row, text="🎯  Next position",
            command=self._training_position,
            bg=self._theme.btn_bg, fg=self._theme.status_fg, activebackground=self._theme.btn_act, bd=0, 
            activeforeground=self._theme.label_fg, relief="flat", 
            font=(self._theme.font_serif, self._theme.font_btn_size), pady=4, cursor="hand2",
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        tk.Button(
            _tp_btn_row, text="✕  Exit training",
            command=self._exit_training,
            bg=self._theme.btn_bg, fg=_c.NAG_INFO[2][2], activebackground=self._theme.btn_act, bd=0, 
            activeforeground=self._theme.label_fg, relief="flat",
            font=(self._theme.font_serif, self._theme.font_btn_size), pady=4, cursor="hand2",
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))

        self._training_panel.lower()

        # Footer status bar
        footer = tk.Frame(self, bg=_c.BG, pady=4)
        footer.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar()
        tk.Label(footer, textvariable=self.status_var, bg=_c.BG, fg=_c.STATUS_FG,
                 font=(self._theme.font_serif, max(12, self._theme.font_label_size), "italic")).pack()

    # ═══════════════════════════════════════════════════════════════════════
    # CURRENT STATE
    # ═══════════════════════════════════════════════════════════════════════

    def _current_board(self) -> list:
        return self.current_node.board

    def _current_color(self) -> str:
        if isinstance(self.current_node, GameTree):
            return "w"
        return opponent(self.current_node.color)

    def _current_move_num(self) -> int:
        if isinstance(self.current_node, GameTree):
            return 1
        col = self.current_node.color
        num = self.current_node.move_num
        return num + 1 if col == "b" else num

    # ═══════════════════════════════════════════════════════════════════════
    # PGN LOADING
    # ═══════════════════════════════════════════════════════════════════════

    def _load_pgn_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Apri file PGN",
            filetypes=[("File PGN", "*.pgn"), ("Tutti i file", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file:\n{e}")
            return

        games = parse_pgn(text)
        if not games:
            messagebox.showwarning("Warning", "No games found in the file.")
            return
        self.loaded_games = games
        self._populate_game_list()
        self.list_info.config(
            text=f"{len(games)} game(s) from\n{path.split('/')[-1]}"
        )
        self._update_training_btn()

    def _populate_game_list(self) -> None:
        self.game_listbox.delete(0, "end")
        for i, g in enumerate(self.loaded_games):
            h = g.headers
            w = h.get("White", "?")[:14]
            b = h.get("Black", "?")[:14]
            self.game_listbox.insert("end", f"{i+1:>3}. {w} - {b}  {g.result}")

    def _on_game_select(self, event: tk.Event) -> None:
        sel = self.game_listbox.curselection()
        if not sel:
            return
        g = self.loaded_games[sel[0]]
        h = g.headers
        ml = g.main_line()
        self.list_info.config(
            text=(f"{h.get('White','?')} vs {h.get('Black','?')}\n"
                  f"{h.get('Event','?')} — {h.get('Date','?')}\n"
                  f"{len(ml)} moves  •  {g.result}")
        )

    def _on_game_load(self, event: tk.Event | None = None) -> None:
        sel = self.game_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Please select a game first.")
            return
        g = self.loaded_games[sel[0]]
        self.tree         = g
        self.current_node = g
        self.replay_mode  = True
        self.selected     = None
        self.highlights   = []
        self.game_over    = False
        self._refresh_board()
        self._update_pgn_panel()
        self._update_variant_list()
        self._update_status()

    # ═══════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════════════

    def _nav_start(self) -> None:
        self.current_node = self.tree
        self._post_nav()

    def _nav_end(self) -> None:
        node = self.current_node
        while node.children:
            node = node.children[0]
        self.current_node = node
        self._post_nav()

    def _nav_prev(self) -> None:
        if isinstance(self.current_node, MoveNode) and self.current_node.parent:
            self.current_node = self.current_node.parent
        self._post_nav()

    def _nav_next(self) -> None:
        if self.current_node.children:
            self.current_node = self.current_node.children[0]
        self._post_nav()

    def _nav_prev_variant(self) -> None:
        """Switch to the previous sibling variation (↑ key)."""
        node = self.current_node
        if not isinstance(node, MoveNode) or not node.parent:
            return
        siblings = node.parent.children
        idx = siblings.index(node)
        if idx > 0:
            self.current_node = siblings[idx - 1]
            self._post_nav()

    def _nav_next_variant(self) -> None:
        """Switch to the next sibling variation (↓ key)."""
        node = self.current_node
        if not isinstance(node, MoveNode) or not node.parent:
            return
        siblings = node.parent.children
        idx = siblings.index(node)
        if idx < len(siblings) - 1:
            self.current_node = siblings[idx + 1]
            self._post_nav()

    def _post_nav(self) -> None:
        self.selected  = None
        self.highlights = []
        self._refresh_board()
        self._update_pgn_panel()
        self._update_variant_list()
        self._update_status()
        self._load_comment_box()
        self._update_nag_buttons()

    # ═══════════════════════════════════════════════════════════════════════
    # VARIANTS
    # ═══════════════════════════════════════════════════════════════════════

    def _update_variant_list(self) -> None:
        self.var_listbox.delete(0, "end")
        node = self.current_node
        parent = node.parent if isinstance(node, MoveNode) else node
        children = parent.children if parent else []
        for i, child in enumerate(children):
            prefix = "★" if i == 0 else f"⑊{i}"
            num_str = f"{child.move_num}." if child.color == "w" else f"{child.move_num}..."
            label = f"{prefix} {num_str}{child.san}"
            if child.nag:
                label += _c.NAG_SYM.get(child.nag, "")
            self.var_listbox.insert("end", label)
        if isinstance(node, MoveNode) and node.parent:
            try:
                idx = node.parent.children.index(node)
                self.var_listbox.selection_set(idx)
                self.var_listbox.see(idx)
            except ValueError:
                pass

    def _on_variant_select(self, event: tk.Event | None = None) -> None:
        sel = self.var_listbox.curselection()
        if not sel:
            return
        node   = self.current_node
        parent = node.parent if isinstance(node, MoveNode) else node
        if not parent:
            return
        children = parent.children
        if sel[0] < len(children):
            self.current_node = children[sel[0]]
            self._post_nav()

    def _delete_variant(self) -> None:
        sel = self.var_listbox.curselection()
        if not sel:
            return
        idx    = sel[0]
        node   = self.current_node
        parent = node.parent if isinstance(node, MoveNode) else node
        if not parent:
            return
        if idx == 0:
            messagebox.showinfo("Info", "The main line cannot be deleted.")
            return
        children = parent.children
        if idx < len(children):
            children.pop(idx)
            if isinstance(self.current_node, MoveNode):
                if self.current_node not in children:
                    self.current_node = parent
            self._post_nav()

    # ═══════════════════════════════════════════════════════════════════════
    # DRAWING
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_board(self) -> None:
        self._draw_board()
        self._draw_pieces()

    def _square_coords(self, r: int, c: int) -> tuple[int, int, int, int]:
        sq_size = _c.SQUARE
        off     = _c.OFFSET
        dc, dr  = (7 - c, 7 - r) if self.flipped else (c, r)
        x0 = off + dc * sq_size
        y0 = off + dr * sq_size
        return x0, y0, x0 + sq_size, y0 + sq_size

    def _draw_board(self) -> None:
        sq_size = _c.SQUARE
        off     = _c.OFFSET
        self.canvas.delete("board", "label")
        total = sq_size * 8 + off * 2
        bd = self._current_board()

        self.canvas.create_rectangle(
            off - 4, off - 4, total - off + 4, total - off + 4,
            outline=_c.BORDER_CLR, width=4, tags="board",
        )
        files_lbl = "abcdefgh" if not self.flipped else "hgfedcba"
        ranks_lbl = "87654321" if not self.flipped else "12345678"

        for r in range(8):
            for c in range(8):
                x0, y0, x1, y1 = self._square_coords(r, c)
                lr, lc = (r, c) if not self.flipped else (7 - r, 7 - c)
                col = _c.LIGHT_SQ if (lr + lc) % 2 == 0 else _c.DARK_SQ
                if self.selected == (r, c):
                    col = _c.SELECT_CLR
                elif (r, c) in self.highlights:
                    col = _c.MOVE_CLR
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="", tags="board")
                piece = bd[r][c]
                if piece and piece[1] == "K" and is_in_check(bd, piece[0]):
                    self.canvas.create_rectangle(x0 + 2, y0 + 2, x1 - 2, y1 - 2,
                                                 fill=_c.CHECK_CLR, outline="", tags="board")

        for i in range(8):
            x = off + i * sq_size + sq_size // 2
            for y in [off // 2, total - off // 2]:
                self.canvas.create_text(x, y, text=files_lbl[i], fill=_c.LABEL_FG,
                                        font=(self._theme.font_serif, self._theme.font_small_size), tags="label")
        for i in range(8):
            y = off + i * sq_size + sq_size // 2
            for x in [off // 2, total - off // 2]:
                self.canvas.create_text(x, y, text=ranks_lbl[i], fill=_c.LABEL_FG,
                                        font=(self._theme.font_serif, self._theme.font_small_size), tags="label")

    def _draw_pieces(self) -> None:
        sq_size = _c.SQUARE
        self.canvas.delete("piece")
        bd  = self._current_board()
        use_images = hasattr(self, '_piece_cache') and self._piece_cache.available

        # Unicode font — fallback when piece images are not available
        try:
            pf = tkfont.Font(family=self._theme.font_piece_family, size=int(sq_size * 0.60))
        except Exception:
            pf = tkfont.Font(size=int(sq_size * 0.60))

        for r in range(8):
            for c in range(8):
                piece = bd[r][c]
                if not piece:
                    continue
                x0, y0, x1, y1 = self._square_coords(r, c)
                cx, cy = (x0 + x1) // 2, (y0 + y1) // 2

                if use_images:
                    img = self._piece_cache.get(piece)
                    if img:
                        # # Subtle shadow: 2 px offset down-right
                        # self.canvas.create_image(
                        #     cx + 2, cy + 2, image=img, anchor="center",
                        #     tags="piece",
                        # )
                        self.canvas.create_image(
                            cx, cy, image=img, anchor="center",
                            tags="piece",
                        )
                        continue   # image rendered — skip the Unicode fallback

                # Unicode fallback
                fg = self._theme.label_fg if piece[0] == "w" else "#111111"
                # self.canvas.create_text(
                #     cx + 2, cy + 2, text=_c.PIECES[piece],
                #     font=pf, fill="#00000055", tags="piece",
                # )
                self.canvas.create_text(
                    cx, cy, text=_c.PIECES[piece],
                    font=pf, fill=fg, tags="piece",
                )

    # ═══════════════════════════════════════════════════════════════════════
    # PGN PANEL
    # ═══════════════════════════════════════════════════════════════════════

    def _update_pgn_panel(self) -> None:
        self._pgn_click_map = []
        self.pgn_text.config(state="normal")
        self.pgn_text.delete("1.0", "end")

        if self.tree.comment:
            self.pgn_text.insert("end", f"{{ {self.tree.comment} }}\n", "comment")
        if self.tree.children:
            self._render_variation(self.tree.children[0], depth=0, force_num=True)

        res = self.tree.result
        if res and res != "*":
            self.pgn_text.insert("end", f"\n{res}", "result")

        self.pgn_text.config(state="disabled")

        for start, end, node in self._pgn_click_map:
            if node is self.current_node:
                self.pgn_text.see(start)
                break

    def _render_variation(self, start_node: MoveNode, depth: int, force_num: bool = False) -> None:
        node = start_node
        prev_color = None
        indent = "  " * depth

        while node:
            is_white = node.color == "w"
            show_num = force_num or is_white or prev_color is None

            if show_num:
                num_text = f"{indent}{node.move_num}. " if is_white else f"{indent}{node.move_num}... "
                self.pgn_text.insert("end", num_text, "num")
                force_num = False

            is_cur = node is self.current_node
            tag = ("cur" if is_cur else "move") if depth == 0 else ("var_cur" if is_cur else "var")

            start_idx = self.pgn_text.index("end")
            self.pgn_text.insert("end", node.san, tag)
            end_idx = self.pgn_text.index("end")
            self._pgn_click_map.append((start_idx, end_idx, node))

            if node.nag:
                self.pgn_text.insert("end", _c.NAG_SYM.get(node.nag, ""), "nag")

            for var_child in node.children[1:]:
                self.pgn_text.insert("end", "\n")
                self.pgn_text.insert("end", f"{indent}  ( ", "var")
                self._render_variation(var_child, depth=depth + 1, force_num=True)
                self.pgn_text.insert("end", " )", "var")
                self.pgn_text.insert("end", "\n")
                force_num = True

            if node.comment:
                self.pgn_text.insert("end", f" {{ {node.comment} }}", "comment")

            self.pgn_text.insert("end", " ")
            prev_color = node.color

            node = node.children[0] if node.children else None

    # ═══════════════════════════════════════════════════════════════════════
    # PGN PANEL CLICK
    # ═══════════════════════════════════════════════════════════════════════

    def _on_pgn_click(self, event: tk.Event) -> None:
        idx = self.pgn_text.index(f"@{event.x},{event.y}")
        for start, end, node in self._pgn_click_map:
            if (self.pgn_text.compare(start, "<=", idx)
                    and self.pgn_text.compare(idx, "<=", end)):
                self.current_node = node
                self._post_nav()
                return

    # ═══════════════════════════════════════════════════════════════════════
    # BOARD INTERACTION
    # ═══════════════════════════════════════════════════════════════════════

    def _canvas_to_square(self, x: int, y: int) -> tuple[int | None, int | None]:
        sq_size = _c.SQUARE
        off     = _c.OFFSET
        c = (x - off) // sq_size
        r = (y - off) // sq_size
        if 0 <= r < 8 and 0 <= c < 8:
            if self.flipped:
                return 7 - r, 7 - c
            return r, c
        return None, None

    def _on_click(self, event: tk.Event) -> None:
        if self.game_over:
            return
        r, c = self._canvas_to_square(event.x, event.y)
        if r is None:
            return
        bd    = self._current_board()
        color = self._current_color()
        piece = bd[r][c]

        if self.selected is None:
            if piece and color_of(piece) == color:
                self.selected   = (r, c)
                self.highlights = legal_moves(bd, r, c)
        else:
            sr, sc = self.selected
            if (r, c) in self.highlights:
                san       = build_san(bd, sr, sc, r, c)
                new_board = apply_move(bd, sr, sc, r, c)
                move_num  = self._current_move_num()

                # Reuse existing node if this move is already in the tree
                existing = next(
                    (ch for ch in self.current_node.children if ch.san == san), None
                )
                if existing:
                    self.current_node = existing
                else:
                    node = MoveNode(san, new_board, color, move_num, self.current_node)
                    self.current_node.children.append(node)
                    self.current_node = node

                self.selected   = None
                self.highlights = []

                if not has_any_legal_move(new_board, opponent(color)):
                    if is_in_check(new_board, opponent(color)):
                        self.game_over    = True
                        self.tree.result  = "1-0" if color == "w" else "0-1"

                self._refresh_board()
                self._update_pgn_panel()
                self._update_variant_list()
                self._update_status()
                self._load_comment_box()
                self._update_nag_buttons()

            elif piece and color_of(piece) == color:
                self.selected   = (r, c)
                self.highlights = legal_moves(bd, r, c)
            else:
                self.selected   = None
                self.highlights = []

        if self.selected is not None:
            self._refresh_board()

    # ═══════════════════════════════════════════════════════════════════════
    # COMMENT
    # ═══════════════════════════════════════════════════════════════════════

    def _load_comment_box(self) -> None:
        if self._comment_updating:
            return
        self._comment_updating = True
        node = self.current_node
        cmt  = node.comment if hasattr(node, "comment") else ""
        self.comment_text.delete("1.0", "end")
        if cmt:
            self.comment_text.insert("1.0", cmt)
        if isinstance(node, MoveNode):
            num = f"{node.move_num}." if node.color == "w" else f"{node.move_num}..."
            self.comment_label.config(text=f"💬  {num}{node.san}")
        else:
            self.comment_label.config(text="💬  Pre-game comment")
        self.comment_text.edit_modified(False)
        self._comment_updating = False

    def _on_comment_modified(self, event: tk.Event | None = None) -> None:
        if self._comment_updating:
            return
        if not self.comment_text.edit_modified():
            return
        self._save_comment()
        self.comment_text.edit_modified(False)

    def _save_comment(self) -> None:
        txt  = self.comment_text.get("1.0", "end").strip()
        node = self.current_node
        if hasattr(node, "comment"):
            node.comment = txt
        self._comment_updating = True
        yv = self.pgn_text.yview()
        self._update_pgn_panel()
        self.pgn_text.yview_moveto(yv[0])
        self._comment_updating = False

    # ═══════════════════════════════════════════════════════════════════════
    # NAG
    # ═══════════════════════════════════════════════════════════════════════

    def _update_nag_buttons(self) -> None:
        node   = self.current_node
        active = node.nag if isinstance(node, MoveNode) else None
        for nag_n, btn in self.nag_buttons.items():
            btn.config(
                bg=_c.LIST_SEL if nag_n == active else _c.BTN_BG,
                relief="solid" if nag_n == active else "flat",
            )

    def _toggle_nag(self, nag_n: int) -> None:
        node = self.current_node
        if not isinstance(node, MoveNode):
            return
        node.nag = None if node.nag == nag_n else nag_n
        self._update_nag_buttons()
        yv = self.pgn_text.yview()
        self._update_pgn_panel()
        self.pgn_text.yview_moveto(yv[0])

    # ═══════════════════════════════════════════════════════════════════════
    # STATUS BAR
    # ═══════════════════════════════════════════════════════════════════════

    def _update_status(self) -> None:
        node  = self.current_node
        color = self._current_color()
        h     = self.tree.headers
        if self.game_over:
            winner = "White" if color == "b" else "Black"
            self.status_var.set(f"♛ Checkmate! {winner} wins.")
            return
        if self.replay_mode:
            w = h.get("White", "White")
            b = h.get("Black", "Black")
            if isinstance(node, MoveNode):
                depth_lbl = f"  [variation lvl {node.depth()}]" if node.depth() else ""
                col_name  = "White" if node.color == "w" else "Black"
                self.status_var.set(
                    f"▶ {w} vs {b}  —  dopo {node.move_num}.{'..' if col_name == 'Black' else ''} {node.san} ({col_name}){depth_lbl}"
                )
            else:
                self.status_var.set(f"▶ {w} vs {b}  —  Starting position")
        else:
            col_name  = "White ♙" if color == "w" else "Black ♟"
            chk       = " — ⚠ Check!" if is_in_check(self._current_board(), color) else ""
            is_var    = isinstance(node, MoveNode) and node.depth() > 0
            var_label = "  [variation]" if is_var else ""
            self.status_var.set(f"Turn: {col_name}{chk}{var_label}")

    # ═══════════════════════════════════════════════════════════════════════
    # TRAINING
    # ═══════════════════════════════════════════════════════════════════════

    def _update_training_btn(self) -> None:
        """Enable or disable the Training button based on loaded games."""
        if self._training_btn is None:
            return
        state = "normal" if self.loaded_games else "disabled"
        self._training_btn.config(state=state)

    def _build_training_questions(self, parent: tk.Frame, side_w: int) -> None:
        """
        Populate the training panel by loading sections and questions from
        ``taketaketake.json``.  Falls back to built-in defaults if the file
        is absent or malformed (a warning is printed to stderr in that case).
        """
        sections, config_path = load_training_config()

        pad = 10
        for title, colour, questions in sections:
            tk.Label(
                parent, text=title,
                bg=self._theme.list_bg, fg=colour,
                font=(self._theme.font_serif, self._theme.font_small_size, "bold"),
                wraplength=side_w - 24, justify="left", anchor="w",
                padx=pad, pady=5,
            ).pack(fill="x")
            tk.Frame(parent, bg=colour, height=1).pack(fill="x", padx=pad, pady=(0, 3))
            for q in questions:
                row = tk.Frame(parent, bg=self._theme.list_bg)
                row.pack(fill="x", padx=pad, pady=2)
                tk.Label(
                    row, text="\u2022", bg=self._theme.list_bg, fg=colour,
                    font=(self._theme.font_serif, self._theme.font_btn_size, "bold"), width=2, anchor="nw",
                ).pack(side="left", anchor="nw", pady=1)
                tk.Label(
                    row, text=q,
                    bg=self._theme.list_bg, fg=self._theme.pgn_fg,
                    font=(self._theme.font_serif, self._theme.font_small_size),
                    wraplength=side_w - 48, justify="left", anchor="nw",
                ).pack(side="left", fill="x", expand=True)
            tk.Frame(parent, bg=self._theme.list_bg, height=6).pack(fill="x")

        # Footer: show which config file is active
        tk.Frame(parent, bg=self._theme.btn_bg, height=1).pack(fill="x", padx=pad, pady=(4, 0))
        if config_path:
            cfg_label  = f"\u2713  {config_path.name}"
            cfg_colour = self._theme.pgn_num_fg
        else:
            cfg_label  = "\u26a0  built-in defaults (taketaketake.json not found)"
            cfg_colour = _c.NAG_INFO[6][2]
        tk.Label(
            parent, text=cfg_label,
            bg=self._theme.list_bg, fg=cfg_colour,
            font=(self._theme.font_mono, self._theme.font_tiny_size), anchor="w",
            padx=pad, pady=4,
        ).pack(fill="x")
    def _show_training_panel(self) -> None:
        """Raise the training overlay above the PGN panel."""
        if self._training_panel:
            self._training_panel.lift()

    def _hide_training_panel(self) -> None:
        """Lower the training overlay behind the PGN panel."""
        if self._training_panel:
            self._training_panel.lower()

    def _exit_training(self) -> None:
        """Exit training mode and restore the normal PGN panel."""
        self._hide_training_panel()
        self.replay_mode = False
        self._update_status()

    def _training_position(self) -> None:
        """
        Load the full PGN of a randomly selected game and navigate to a
        random position in the midgame-to-endgame range (moves 10 to
        len(main_line) - 5, inclusive).  The PGN panel shows the complete
        game with the chosen position highlighted; the game summary in
        list_info is updated as usual.
        """
        if not self.loaded_games:
            return

        # Pick a random game
        g = random.choice(self.loaded_games)
        main = g.main_line()

        # Midgame-to-endgame window: skip the first 9 half-moves (opening)
        # and the last 4, so the position is neither trivial opening theory
        # nor the very end of the game.
        SKIP_START = 9    # first eligible index (0-based) = move 10
        SKIP_END   = 4    # exclude last N half-moves

        lo = SKIP_START
        hi = len(main) - 1 - SKIP_END

        if hi < lo:
            # Game too short — fall back to the second half
            hi = len(main) - 1
            lo = max(0, hi // 2)

        if not main or hi < 0:
            messagebox.showwarning(
                "Training",
                "The selected game has no moves to train on.",
            )
            return

        chosen_node = main[random.randint(lo, hi)]

        # Load the full game tree so the PGN panel shows all moves
        self.tree         = g
        self.current_node = chosen_node
        self.replay_mode  = True
        self.selected     = None
        self.highlights   = []
        self.game_over    = False

        # Update the game summary label
        h  = g.headers
        ml = g.main_line()
        white  = h.get("White", "?")
        black  = h.get("Black", "?")
        event  = h.get("Event", "?")
        date   = h.get("Date", "?")
        self.list_info.config(
            text=(
                f"{white} vs {black}\n"
                f"{event} — {date}\n"
                f"{len(ml)} moves  •  {g.result}  [training]"
            )
        )

        # Highlight the chosen game in the listbox
        try:
            idx = self.loaded_games.index(g)
            self.game_listbox.selection_clear(0, "end")
            self.game_listbox.selection_set(idx)
            self.game_listbox.see(idx)
        except ValueError:
            pass

        self._refresh_board()
        self._update_pgn_panel()
        self._update_variant_list()
        self._update_status()
        self._load_comment_box()
        self._update_nag_buttons()
        self._show_training_panel()

    # ═══════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════


    def _copy_pgn(self) -> None:
        pgn = tree_to_pgn(self.tree)
        self.clipboard_clear()
        self.clipboard_append(pgn)
        orig = self.title()
        self.title("✓ PGN copied to clipboard!")
        self.after(1500, lambda: self.title(orig))

    def _new_game(self) -> None:
        self.tree         = GameTree()
        self.current_node = self.tree
        self.selected     = None
        self.highlights   = []
        self.game_over    = False
        self.replay_mode  = False
        self._refresh_board()
        self._update_pgn_panel()
        self._update_variant_list()
        self._update_status()
        self._load_comment_box()
        self._update_nag_buttons()

    def _flip(self) -> None:
        self.flipped = not self.flipped
        self._refresh_board()

    def _on_resize(self, event: tk.Event | None = None) -> None:
        """Reload the image cache when the square size changes."""
        if hasattr(self, '_piece_cache'):
            self._piece_cache.reload(square_px=_c.SQUARE)
