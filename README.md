# ♟ TakeTakeTake

A desktop chess application written in **pure Python 3** — no external dependencies, stdlib only.

[![Python](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/bigmauri/taketaketake/actions/workflows/release.yml/badge.svg)](https://github.com/bigmauri/taketaketake/actions/workflows/release.yml)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Usage as a Library](#usage-as-a-library)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

---

## Overview

**TakeTakeTake** is a self-contained chess desktop application built entirely with the Python standard library. It features a fully functional chess engine, a tkinter-based GUI, PGN file loading, a complete variation tree, move annotations, and a 103-test unit suite — all without requiring a single third-party package.

Whether you want to replay classic games, study openings, annotate positions, or simply play a game, TakeTakeTake gives you a clean, keyboard-friendly interface that runs anywhere Python 3.10+ is installed.

---

## Features

### Board & Game Logic

- Free play for both White and Black
- Legal move highlighting on piece selection
- Automatic detection of check, checkmate, and stalemate
- Castling (both kingside and queenside), with all legality conditions enforced
- Pawn promotion
- Board flip / rotation

### Navigation

- Step through moves forward and backward using the arrow keys
- Jump to the start or end of the game instantly
- Navigate up and down between variations in the move tree

### PGN Support

- Load `.pgn` files containing one or more games
- Interactive move list panel — click any move to jump to that position
- Copy the current game's PGN to the clipboard

### Variation Tree

- Full variation tree: add a new variation by simply playing a different move from any position
- Navigate between sibling variations with `↑` / `↓`
- Delete individual variations

### Annotations

- Per-node text comments using standard PGN `{ }` syntax
- NAG support (Numeric Annotation Glyphs) for moves 1–6: `!`, `?`, `!!`, `??`, `!?`, `?!`

### Layout

- Maximised window on launch
- Board and panel sizes scale dynamically to the screen resolution

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or newer (3.12 recommended) |
| tkinter | bundled with Python (see note below) |

> **Linux users:** tkinter ships with the standard library but may be packaged separately by your distribution. Install it with:
> ```bash
> # Debian / Ubuntu
> sudo apt install python3-tk
>
> # Fedora
> sudo dnf install python3-tkinter
>
> # Arch Linux
> sudo pacman -S tk
> ```

No third-party Python packages are required to **run** the application. `pytest` and `pyflakes` are only needed for development.

---

## Installation

### Option 1 — Run directly from source (no install)

```bash
git clone https://github.com/bigmauri/taketaketake.git
cd taketaketake
python -m taketaketake
```

### Option 2 — Install with pip

```bash
git clone https://github.com/bigmauri/taketaketake.git
cd taketaketake
pip install .
taketaketake          # launch the GUI from anywhere
```

### Option 3 — Editable install (for development)

```bash
git clone https://github.com/bigmauri/taketaketake.git
cd taketaketake

# Optional but recommended: use a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
pip install pytest pyflakes      # dev tools
```

---

## Running the Application

```bash
# If installed via pip
taketaketake

# If running from source
python -m taketaketake
```

The application opens maximised. To load a PGN file, use the file menu or drag-and-drop (if supported by your OS).

---

## Usage as a Library

The `taketaketake` package exposes a clean public API that can be used independently of the GUI, for example to build analysis scripts or integrate the chess engine into other tools.

### Chess engine

```python
from taketaketake import initial_board, legal_moves, build_san, apply_move

# Set up the starting position
board = initial_board()

# Get all legal destinations for the pawn on e2 (row 6, col 4)
moves = legal_moves(board, 6, 4)

# Build the SAN string for moving that pawn to e4
san = build_san(board, 6, 4, 4, 4)   # returns "e4"

# Apply the move and get the new board state (non-destructive)
board = apply_move(board, 6, 4, 4, 4)
```

### PGN parsing and serialisation

```python
from taketaketake import parse_pgn, tree_to_pgn

# Parse a PGN string or file — returns a list of GameTree objects
with open("games.pgn") as f:
    trees = parse_pgn(f.read())

tree = trees[0]
print(tree.headers["White"], "vs", tree.headers["Black"])

# Walk the main line
for node in tree.main_line():
    print(node.move_num, node.san, node.comment or "")

# Serialise back to PGN text
pgn_text = tree_to_pgn(tree)
print(pgn_text)
```

### Working with the move tree

```python
from taketaketake import GameTree, MoveNode

tree = GameTree()

# Add moves to the main line
node1 = tree.add_move(tree.root, board_after_e4, "e4", move_num=1, color="white")
node2 = tree.add_move(node1, board_after_e5, "e5", move_num=1, color="black")

# Annotate a move
node1.comment = "The most common opening move."
node1.nag = 1   # NAG 1 = "!"

# Navigate
print(node2.depth())           # 2
for n in tree.main_line():
    print(n.san)
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `←` | Go to the previous move |
| `→` | Go to the next move (main line) |
| `Home` | Jump to the starting position |
| `End` | Jump to the last move |
| `↑` | Switch to the previous variation |
| `↓` | Switch to the next variation |

---

## Project Structure

```
taketaketake/                    Python package (stdlib only)
├── __init__.py                  Public API exports
├── __main__.py                  Entry point: python -m taketaketake
├── constants.py                 Color palette, piece Unicode symbols, NAG map
├── engine.py                    Pure chess logic: move generation, SAN, check detection
├── tree.py                      MoveNode / GameTree — the variation tree data structure
├── pgn.py                       PGN parser (GameTree) and serialiser (GameTree → PGN)
└── app.py                       tkinter GUI — ChessApp main class

tests/
└── test_taketaketake.py         103 unit tests across 13 test classes (stdlib unittest)

.github/
└── workflows/
    └── ci.yml                   GitHub Actions CI pipeline

pyproject.toml                   Package metadata, pytest and coverage configuration
taketaketake.template.json       Default game configuration template
taketaketake-theme.template.json UI theme template
README.md                        This file
CONTRIBUTING.md                  Contribution guidelines
CHANGELOG.md                     Version history
LICENSE                          MIT License
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `constants.py` | Static data: colour definitions, Unicode piece symbols, NAG symbol map |
| `engine.py` | All chess rules: `initial_board`, `raw_moves`, `legal_moves`, `is_in_check`, `apply_move`, `build_san`, `san_to_move` |
| `tree.py` | `MoveNode` (a single node in the game tree) and `GameTree` (the full variation tree with headers) |
| `pgn.py` | Tokeniser, parser (PGN text → `GameTree`), and serialiser (`GameTree` → PGN text); supports headers, comments, NAG, and nested variations |
| `app.py` | The `ChessApp` tkinter class: board rendering, event handling, move input, PGN panel, variation navigation |

---

## Testing

The test suite contains **103 unit tests** across **13 test classes**, all using the standard library's `unittest` module.

### Running the tests

```bash
# With unittest (no extra packages required)
python -m unittest tests/test_taketaketake.py -v

# With pytest (if installed)
python -m pytest tests/ -v

# With coverage report (requires pytest-cov)
python -m pytest tests/ --cov=taketaketake --cov-report=term-missing
```

### Test classes

| Class | What it covers |
|---|---|
| `TestUtilita` | Pure utility functions: `sq`, `opponent`, `in_bounds`, etc. |
| `TestPosizioneIniziale` | Correctness of the starting board layout |
| `TestMosseGrezze` | `raw_moves` output for every piece type |
| `TestScacco` | `is_in_check` and `find_king` |
| `TestMosseLegali` | Pins, check filtering, checkmate, stalemate |
| `TestApplyMove` | Board mutation, castling, pawn promotion, immutability |
| `TestArrocco` | All castling legality conditions (through attacked squares, previously moved pieces, etc.) |
| `TestBuildSan` | SAN generation, file/rank disambiguation, check/mate suffixes |
| `TestSanToMove` | Inverse SAN parsing, full roundtrip |
| `TestMoveNode` | Tree node structure, `depth()`, `main_line()` |
| `TestParserPGN` | PGN parsing: headers, inline comments, NAG, nested variations, multi-game files |
| `TestTreeToPgn` | PGN serialisation and parse→serialize roundtrip |
| `TestPartitiCelebri` | Integration tests: Scholar's mate, Fool's mate, classic opening lines |

> **Note:** `app.py` (the tkinter GUI) is intentionally excluded from the test suite, as tkinter requires a display server to run.

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically on every **push** to `main` or `develop` and on every **pull request** targeting those branches.

The pipeline consists of four sequential jobs:

1. **Lint** — runs `pyflakes` on all source files to catch undefined names and unused imports.
2. **Test** — runs the full test suite on a matrix of Python **3.10**, **3.11**, and **3.12**, producing JUnit XML reports.
3. **Syntax** — runs `ast.parse` on every `.py` file to ensure there are no syntax errors.
4. **CI OK** — a sentinel job that succeeds only when all previous jobs pass; used for branch protection rules.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for full details on the development workflow, branch naming conventions, commit message format, code style requirements, and pull request guidelines.

### Quick summary

- Branch off `develop`, not `main`
- Use the branch prefix that matches your change: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`
- Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- Ensure all existing tests pass and add new tests for any new behaviour
- Run `pyflakes` on changed files before opening a PR

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
