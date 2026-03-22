# ♟ TakeTakeTake

Applicazione desktop per scacchi scritta in **Python 3 puro** — nessuna dipendenza esterna, solo stdlib.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![CI](https://github.com/your-org/taketaketake/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/taketaketake/actions/workflows/ci.yml)

---

## Funzionalità

| Area | Funzionalità |
|------|-------------|
| **Scacchiera** | Partita libera bianco/nero, mosse legali evidenziate, scacco/matto/stallo rilevati automaticamente, arrocco, promozione pedone, rotazione scacchiera |
| **Navigazione** | ⏮ ◀ ▶ ⏭ con tasti freccia, scorciatoie tastiera (`←` `→` `Home` `End` `↑` `↓`) |
| **PGN** | Caricamento file `.pgn` multi-partita, pannello mosse interattivo con click, copia PGN negli appunti |
| **Varianti** | Albero varianti completo: aggiunta variante giocando dalla posizione corrente, navigazione `↑/↓`, eliminazione variante |
| **Annotazioni** | Commenti `{ }` per nodo, NAG 1–6 (`!` `?` `!!` `??` `!?` `?!`) |
| **Layout** | Finestra massimizzata, dimensioni dinamiche adattate alla risoluzione dello schermo |

---

## Struttura del pacchetto

```
taketaketake/
├── __init__.py     API pubblica del pacchetto
├── __main__.py     Entry point: python -m taketaketake
├── constants.py    Palette colori, simboli pezzi, NAG
├── engine.py       Logica scacchistica pura (mosse, SAN, scacco…)
├── tree.py         MoveNode / GameTree — struttura dati ad albero
├── pgn.py          Parser PGN → GameTree, serializer GameTree → PGN
└── app.py          GUI tkinter (ChessApp)

tests/
└── test_taketaketake.py   103 test unitari (stdlib unittest)

.github/
└── workflows/
    └── ci.yml      GitHub Actions CI (lint + test matrix + syntax check)
```

---

## Installazione

### Esecuzione diretta (senza installazione)

```bash
git clone https://github.com/your-org/taketaketake
cd taketaketake
python -m taketaketake
```

### Installazione con pip

```bash
pip install .
taketaketake          # avvia la GUI
```

### Dipendenza di sistema (tkinter)

tkinter è incluso nella stdlib, ma alcune distribuzioni Linux lo separano:

```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

---

## Utilizzo come libreria

```python
from taketaketake import initial_board, legal_moves, build_san, apply_move
from taketaketake import parse_pgn, tree_to_pgn
from taketaketake import GameTree, MoveNode

# Logica di gioco
board = initial_board()
moves = legal_moves(board, 6, 4)       # mosse legali dal pedone e2
san   = build_san(board, 6, 4, 4, 4)  # "e4"
board = apply_move(board, 6, 4, 4, 4)

# Lettura PGN
with open("partita.pgn") as f:
    trees = parse_pgn(f.read())

tree = trees[0]
print(tree.headers["White"], "vs", tree.headers["Black"])
for node in tree.main_line():
    print(node.move_num, node.san, node.comment or "")

# Scrittura PGN
pgn_text = tree_to_pgn(tree)
print(pgn_text)
```

---

## Scorciatoie da tastiera

| Tasto | Azione |
|-------|--------|
| `←`   | Mossa precedente |
| `→`   | Mossa successiva (linea principale) |
| `Home`| Torna alla posizione iniziale |
| `End` | Vai all'ultima mossa |
| `↑`   | Variante precedente |
| `↓`   | Variante successiva |

---

## Test

```bash
# Con unittest (stdlib)
python -m unittest tests/test_taketaketake.py -v

# Con pytest (se disponibile)
python -m pytest tests/ -v
```

La suite copre 103 test distribuiti in 13 classi:

- `TestUtilita` — funzioni di base (`sq`, `opponent`, `in_bounds`, …)
- `TestPosizioneIniziale` — struttura scacchiera iniziale
- `TestMosseGrezze` — `raw_moves` per tutti i tipi di pezzo
- `TestScacco` — `is_in_check`, `find_king`
- `TestMosseLegali` — inchiodamenti, filtro scacco, scacco matto, stallo
- `TestApplyMove` — arrocco corto/lungo, promozione, immutabilità
- `TestArrocco` — tutte le condizioni di validità
- `TestBuildSan` — generazione SAN, disambiguazione, suffissi
- `TestSanToMove` — parser SAN inverso, roundtrip
- `TestMoveNode` — struttura albero, `depth()`, `main_line()`
- `TestParserPGN` — header, commenti, NAG, varianti, multi-partita
- `TestTreeToPgn` — serializzazione, roundtrip parse→serialize
- `TestPartitiCelebri` — Scholar's mate, Fool's mate, aperture classiche

---

## CI/CD

Il workflow `.github/workflows/ci.yml` si attiva su ogni **push** verso `main`/`develop`
e su ogni **pull request** verso quegli stessi branch.

Pipeline:

1. **Lint** — `pyflakes` su tutto il codice
2. **Test** — matrix Python 3.10 / 3.11 / 3.12 con report JUnit XML
3. **Syntax** — `ast.parse` su tutti i file `.py`
4. **CI OK** — job sentinella per le branch protection rules

---

## Licenza

MIT — vedi `LICENSE`.
