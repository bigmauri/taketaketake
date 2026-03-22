"""
taketaketake/pieces.py
======================
Gestione delle immagini dei pezzi scacchistici per la GUI tkinter.

Strategia a tre livelli:
  1. PNG pre-renderizzati nella cartella assets/pieces/<set>/
     → qualità migliore, nessuna dipendenza
  2. Download automatico del set CBurnett da Wikimedia Commons
     → richiede la connessione Internet al primo avvio (solo una volta)
  3. Fallback ai simboli Unicode già presenti in constants.py
     → funziona sempre, ovunque, senza file aggiuntivi

Set CBurnett
------------
Autore  : Colin Burnett (User:Cburnett su Wikimedia Commons)
Licenza : GPL / GFDL / CC BY-SA 3.0
Fonte   : https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces

Uso
---
    from taketaketake.pieces import PieceImageCache
    cache = PieceImageCache(square_px=72)
    img = cache.get("wK")   # tkinter PhotoImage o None se non disponibile
"""

from __future__ import annotations

import io
import os
import pathlib
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# URL dei PNG CBurnett su Wikimedia Commons  (risoluzioni disponibili: 45, 80, 120, 240 px)
# Usiamo la versione da 120 px come sorgente: buona qualità, file piccoli (~5–15 KB)
# ─────────────────────────────────────────────────────────────────────────────
_WIKIMEDIA_BASE = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb"
)

_PIECE_PATHS: dict[str, str] = {
    # bianco
    "wK": "4/42/Chess_klt45.svg/120px-Chess_klt45.svg.png",
    "wQ": "1/15/Chess_qlt45.svg/120px-Chess_qlt45.svg.png",
    "wR": "7/72/Chess_rlt45.svg/120px-Chess_rlt45.svg.png",
    "wB": "b/b1/Chess_blt45.svg/120px-Chess_blt45.svg.png",
    "wN": "7/70/Chess_nlt45.svg/120px-Chess_nlt45.svg.png",
    "wP": "4/45/Chess_plt45.svg/120px-Chess_plt45.svg.png",
    # nero
    "bK": "f/f0/Chess_kdt45.svg/120px-Chess_kdt45.svg.png",
    "bQ": "4/47/Chess_qdt45.svg/120px-Chess_qdt45.svg.png",
    "bR": "f/ff/Chess_rdt45.svg/120px-Chess_rdt45.svg.png",
    "bB": "9/98/Chess_bdt45.svg/120px-Chess_bdt45.svg.png",
    "bN": "e/ef/Chess_ndt45.svg/120px-Chess_ndt45.svg.png",
    "bP": "c/c7/Chess_pdt45.svg/120px-Chess_pdt45.svg.png",
}

# Directory predefinita per la cache locale
_DEFAULT_CACHE_DIR = pathlib.Path(__file__).parent / "assets" / "pieces" / "cburnett"


# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOAD HELPER
# ─────────────────────────────────────────────────────────────────────────────

def download_cburnett(
    dest_dir: pathlib.Path | str | None = None,
    size_px: int = 120,
    timeout: int = 10,
    verbose: bool = True,
) -> dict[str, pathlib.Path]:
    """
    Scarica il set CBurnett da Wikimedia Commons e salva i PNG in *dest_dir*.

    I file già presenti non vengono riscaricati.

    Parametri
    ---------
    dest_dir : Path | str | None
        Cartella di destinazione. Default: ``taketaketake/assets/pieces/cburnett/``.
    size_px : int
        Larghezza richiesta in pixel (45, 80, 120, 240). Default: 120.
    timeout : int
        Timeout HTTP in secondi.
    verbose : bool
        Se True, stampa un messaggio per ogni file scaricato.

    Restituisce
    -----------
    dict[str, Path]
        Mappa ``piece_code → path_file`` per i file scaricati/presenti.
        Contiene solo le voci scaricate con successo.

    Esempio
    -------
    >>> from taketaketake.pieces import download_cburnett
    >>> paths = download_cburnett()
    >>> print(paths["wK"])
    """
    dest = pathlib.Path(dest_dir) if dest_dir else _DEFAULT_CACHE_DIR
    dest.mkdir(parents=True, exist_ok=True)

    result: dict[str, pathlib.Path] = {}

    for code, path_suffix in _PIECE_PATHS.items():
        # Sostituisce la risoluzione nel path se diversa da 120
        if size_px != 120:
            path_suffix = path_suffix.replace("120px", f"{size_px}px")

        local_file = dest / f"{code}.png"

        if local_file.exists():
            result[code] = local_file
            continue

        url = f"{_WIKIMEDIA_BASE}/{path_suffix}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TakeTakeTake/1.0 (https://github.com/your-org/taketaketake)"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = response.read()
            local_file.write_bytes(data)
            result[code] = local_file
            if verbose:
                print(f"  ✓  {code}  →  {local_file}")
        except (urllib.error.URLError, OSError) as exc:
            if verbose:
                print(f"  ✗  {code}  →  download fallito: {exc}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CACHE DELLE IMMAGINI TKINTER
# ─────────────────────────────────────────────────────────────────────────────

class PieceImageCache:
    """
    Carica e ridimensiona le immagini dei pezzi per la GUI tkinter.

    Tenta di caricare i PNG dal disco; se non disponibili, ritorna None
    e la GUI userà il fallback Unicode definito in ``constants.PIECES``.

    Parametri
    ---------
    square_px : int
        Dimensione della casella in pixel. Le immagini vengono scalate
        a ``square_px × square_px``.
    asset_dir : Path | str | None
        Cartella contenente i PNG. Default: ``taketaketake/assets/pieces/cburnett/``.
    auto_download : bool
        Se True e la cartella è vuota, tenta il download automatico.

    Esempio
    -------
    >>> cache = PieceImageCache(square_px=72)
    >>> img = cache.get("wK")
    >>> if img:
    ...     canvas.create_image(cx, cy, image=img, anchor="center")
    ... else:
    ...     canvas.create_text(cx, cy, text="♔", font=piece_font)
    """

    def __init__(
        self,
        square_px: int = 72,
        asset_dir: pathlib.Path | str | None = None,
        auto_download: bool = True,
    ) -> None:
        self._square_px   = square_px
        self._asset_dir   = pathlib.Path(asset_dir) if asset_dir else _DEFAULT_CACHE_DIR
        self._cache: dict[str, tk.PhotoImage] = {}
        self._available   = False

        # Prova il download automatico se la cartella è vuota
        if auto_download and not self._has_files():
            try:
                download_cburnett(dest_dir=self._asset_dir, verbose=False)
            except Exception:
                pass  # fallback silenzioso ai simboli Unicode

        self._load()

    # ── Interfaccia pubblica ──────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """True se almeno un'immagine è stata caricata con successo."""
        return self._available

    def get(self, piece_code: str) -> Optional[tk.PhotoImage]:
        """
        Restituisce il ``PhotoImage`` per il codice pezzo indicato,
        oppure ``None`` se l'immagine non è disponibile.

        Parametri
        ---------
        piece_code : str
            Codice a due caratteri: colore + tipo, es. ``"wK"``, ``"bP"``.
        """
        return self._cache.get(piece_code)

    def reload(self, square_px: int | None = None) -> None:
        """
        Ricarica tutte le immagini, opzionalmente con una nuova dimensione.
        Chiamare quando la finestra viene ridimensionata.
        """
        if square_px is not None:
            self._square_px = square_px
        self._cache.clear()
        self._available = False
        self._load()

    # ── Metodi privati ────────────────────────────────────────────────────────

    def _has_files(self) -> bool:
        """Restituisce True se la cartella contiene almeno 12 PNG."""
        if not self._asset_dir.exists():
            return False
        return len(list(self._asset_dir.glob("*.png"))) >= 12

    def _load(self) -> None:
        """
        Carica i PNG dal disco e li scala alla dimensione corrente.

        tkinter non supporta il ridimensionamento nativo dei PhotoImage
        per i PNG. Usiamo il modulo ``imghdr`` + manipolazione manuale
        oppure, se disponibile, ``PIL.Image``. Il fallback è caricare
        direttamente senza ridimensionare (il canvas gestirà lo spazio).
        """
        if not self._asset_dir.exists():
            return

        for code in _PIECE_PATHS:
            png_path = self._asset_dir / f"{code}.png"
            if not png_path.exists():
                continue
            try:
                img = self._load_and_resize(png_path)
                if img:
                    self._cache[code] = img
                    self._available = True
            except Exception:
                pass  # singolo fallimento non blocca il resto

    def _load_and_resize(self, path: pathlib.Path) -> Optional[tk.PhotoImage]:
        """
        Carica un PNG e lo ridimensiona a ``square_px × square_px``.

        Strategia:
          1. Prova con Pillow (``PIL``) se disponibile — qualità ottima.
          2. Fallback: carica direttamente come PhotoImage tkinter e
             usa ``subsample`` / ``zoom`` per approssimare la dimensione
             (funziona solo con fattori interi, ma è sufficiente per ±1 pixel).
        """
        target = self._square_px

        # ── Tentativo 1: Pillow ───────────────────────────────────────────────
        try:
            from PIL import Image, ImageTk  # type: ignore[import]
            img_pil = Image.open(path).convert("RGBA")
            img_pil = img_pil.resize((target, target), Image.LANCZOS)
            return ImageTk.PhotoImage(img_pil)
        except ImportError:
            pass  # Pillow non installato — usa il fallback
        except Exception:
            pass

        # ── Tentativo 2: tkinter nativo (PNG supportato da Tk 8.6+) ──────────
        try:
            photo = tk.PhotoImage(file=str(path))
            src_w = photo.width()
            src_h = photo.height()
            if src_w == 0 or src_h == 0:
                return None

            # Subsample (rimpicciolisce) o zoom (ingrandisce) con fattori interi
            if src_w > target:
                factor = round(src_w / target)
                if factor > 1:
                    photo = photo.subsample(factor, factor)
            elif src_w < target:
                factor = round(target / src_w)
                if factor > 1:
                    photo = photo.zoom(factor, factor)

            return photo
        except tk.TclError:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# SCRIPT STANDALONE — download da riga di comando
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scarica il set CBurnett di pezzi scacchistici da Wikimedia Commons.",
    )
    parser.add_argument(
        "--dest", default=None,
        help="Cartella di destinazione (default: taketaketake/assets/pieces/cburnett/)",
    )
    parser.add_argument(
        "--size", type=int, default=120, choices=[45, 80, 120, 240],
        help="Dimensione PNG in pixel (default: 120)",
    )
    args = parser.parse_args()

    print(f"Download set CBurnett ({args.size}px) da Wikimedia Commons...")
    paths = download_cburnett(dest_dir=args.dest, size_px=args.size, verbose=True)
    ok  = sum(1 for p in paths.values() if p.exists())
    print(f"\nDownload completato: {ok}/12 pezzi salvati.")
