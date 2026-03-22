# Changelog

All notable changes to TakeTakeTake are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Legend**
> - `Added` — new features
> - `Changed` — changes to existing functionality
> - `Deprecated` — features that will be removed in a future release
> - `Removed` — features removed in this release
> - `Fixed` — bug fixes
> - `Security` — vulnerability fixes

---

## [Unreleased]

### Added
- Nothing yet.

---

## [1.0.0] — 2026-03-19

### Added

#### Package structure
- Restructured the project as a proper Python package named `taketaketake`,
  installable via `pip install -e .` or `pip install .`.
- `taketaketake/__init__.py` — public API surface; GUI import is lazy so the
  package can be used in headless environments (CI, servers, scripts).
- `taketaketake/__main__.py` — CLI entry point with `argparse`;
  supports `--version` and `--no-gui` flags.
  Run with `python -m taketaketake`.
- `taketaketake/constants.py` — all colour palette values, board sizing
  constants (`SQUARE`, `OFFSET`), Unicode piece symbols, and NAG definitions
  extracted into a single dependency-free module.
- `taketaketake/engine.py` — pure chess logic with no GUI dependency:
  `initial_board`, `raw_moves`, `legal_moves`, `is_in_check`, `apply_move`,
  `has_any_legal_move`, `build_san`, `san_to_move`.
- `taketaketake/tree.py` — `MoveNode` and `GameTree` data structures with
  `depth()`, `is_main_line()`, `main_line()`, `all_nodes()`,
  `find_by_san_path()`, `ancestors()`, and `root()` helpers.
- `taketaketake/pgn.py` — PGN parser and serialiser:
  `parse_pgn()`, `parse_pgn_file()`, `tree_to_pgn()`, `tree_to_pgn_file()`.
- `taketaketake/app.py` — tkinter GUI (`ChessApp`); only imported when the
  application is actually launched.
- `pyproject.toml` — build metadata, `[project.scripts]` entry point,
  pytest and coverage configuration.
- `CONTRIBUTING.md` — contribution guidelines, commit convention,
  branch strategy, code style rules.
- `CHANGELOG.md` — this file.

#### Chess engine
- Complete legal-move generation for all piece types including en-passant-free
  pawn logic, knight, bishop, rook, queen, and king.
- Castling (kingside and queenside) with all legality checks: king not in
  check, king does not pass through attacked square, no pieces in between.
- Pawn promotion — defaults to queen; arbitrary promotion piece via `promo`
  parameter.
- `is_in_check` and `has_any_legal_move` used to detect checkmate and
  stalemate automatically.
- Standard Algebraic Notation (SAN) builder (`build_san`) with full
  disambiguation, castling notation (`O-O` / `O-O-O`), promotion (`=Q`),
  check (`+`), and checkmate (`#`) suffixes.
- SAN parser (`san_to_move`) with support for all the above, including
  alternative castling notation (`0-0` / `0-0-0`).

#### PGN support
- Multi-game PGN file parsing via an iterative stack-based parser that handles
  nested variations to arbitrary depth without recursion.
- Tokeniser emits `(` and `)` as separate tokens, enabling correct nesting.
- Comment extraction and assignment per node (`{ text }`).
- NAG parsing and assignment for values 1–6 (`$1`–`$6`).
- Attached move-number notation (e.g., `1.e4` without a space) handled
  correctly.
- PGN serialiser writes standard-compliant output with 80-column wrapping,
  nested variation parentheses, comments, and NAG annotations.
- `parse_pgn_file()` and `tree_to_pgn_file()` convenience functions for
  direct file I/O.

#### GUI (tkinter, stdlib only)
- Three-column fullscreen layout: game list + variants panel | chessboard |
  PGN panel + comment box + NAG buttons.
- Dynamic board sizing: `SQUARE` and `OFFSET` computed at runtime from screen
  resolution (range 64–112 px per square).
- Board highlights: selected square (yellow), legal-move destinations
  (green-yellow), king in check (red).
- Unicode piece rendering with drop shadow; supports `Segoe UI Symbol` on
  Windows and falls back gracefully on other platforms.
- Board flip (`⇅`) toggle.

#### Navigation
- Navigation buttons: `⏮` `◀` `▶` `⏭` always active (play mode and
  replay mode).
- Variant navigation buttons: `↑` (previous sibling) and `↓` (next sibling).
- Full keyboard shortcut support: `←` `→` `Home` `End` `↑` `↓`.
- Tooltip label shows action name and keyboard shortcut on hover.
- Click on any move token in the PGN panel to jump directly to that position.

#### Variant tree
- Moving from any intermediate position automatically creates a new variation
  node as a child of the current node.
- Duplicate moves reuse the existing child node instead of creating a branch.
- Variant list panel shows all siblings of the current node; `★` marks the
  main line, `⑊N` marks alternatives.
- "Enter variant" and "Delete variant" buttons; the main line is protected
  from deletion.

#### Annotations
- Per-node comment text box with auto-save on modification.
- NAG buttons 1–6 with colour coding, toggle behaviour, and hover hints.
- Both comments and NAG values are included in the copied/exported PGN.

#### CI/CD
- GitHub Actions workflow (`.github/workflows/ci.yml`) triggered on push and
  pull request to `main` and `develop`.
- Six jobs: **lint** (pyflakes), **test** (Python 3.10 / 3.11 / 3.12 matrix
  with JUnit XML reports), **syntax** (AST check of all `.py` files),
  **importcheck** (smoke test without display), **build** (wheel + sdist
  verification), **ci-ok** (sentinel for branch protection rules).
- `concurrency` group cancels stale runs on the same branch.

#### Tests
- 103 unit tests across 13 `TestCase` subclasses, all passing.
- Test file updated to import from `taketaketake` package; no tkinter mock
  required thanks to the lazy GUI import in `__init__.py`.
- Famous game integration tests: Scholar's mate, Fool's mate, Ruy López,
  Italian Opening, Sicilian Defence, French Defence, King's Gambit,
  English Opening.

### Fixed
- PGN tokeniser was grouping the entire content of `(...)` into a single
  token, preventing the stack parser from handling nested variations.
  Fixed by emitting `(` and `)` as individual tokens.
- `MoveNode.depth()` raised `AttributeError` when the parent was a
  `GameTree` instance (which has no `.parent` attribute).
  Fixed by stopping the traversal when the parent is no longer a `MoveNode`.

---

## [0.4.0] — 2026-02-14  *(pre-package, single-file era)*

### Added
- Navigation buttons `⏮ ◀ ▶ ⏭` always enabled regardless of replay mode.
- Variant navigation buttons `↑` / `↓` for moving between sibling nodes.
- Keyboard shortcuts: `←` `→` `Home` `End` `↑` `↓`.
- Tooltip label on nav buttons showing action and key binding.
- `_nav_prev_variant()` and `_nav_next_variant()` methods.

### Changed
- Removed `_set_nav_state()` — buttons are now unconditionally active.

---

## [0.3.0] — 2026-01-28  *(pre-package, single-file era)*

### Added
- Full move-tree architecture (`MoveNode` / `GameTree`) replacing the flat
  `move_list` approach.
- Iterative stack-based PGN parser supporting nested variations.
- PGN serialiser (`tree_to_pgn`) with variation parentheses.
- Variant list panel (left column) with enter / delete controls.
- Fullscreen layout with dynamic `SQUARE` / `OFFSET` computation.
- `python -m taketaketake` entry point (single-file version).

### Changed
- Board sizing is now computed from screen resolution at startup rather than
  being hardcoded.
- Layout switched from `pack` to `grid` for the lateral panels to enable
  proper vertical stretching.

### Fixed
- PGN move numbers attached to SAN tokens (e.g., `1.e4`) were not stripped
  before move parsing.

---

## [0.2.0] — 2026-01-10  *(pre-package, single-file era)*

### Added
- NAG buttons 1–6 (`!` `?` `!!` `??` `!?` `?!`) with colour coding and
  toggle behaviour.
- NAG values parsed from and written to PGN (`$1`–`$6`).
- Per-move comment text box with auto-save.
- Comments parsed from `{ }` blocks in PGN files.
- Inline comment and NAG display in the PGN panel.
- Multi-game PGN file loading with scrollable game list.
- "Copy PGN" button places the full annotated PGN text in the clipboard.

### Changed
- PGN panel now renders comments in italic teal and NAG symbols in bold gold.
- Game list shows White vs Black and result for each game.

---

## [0.1.0] — 2025-12-20  *(initial single-file release)*

### Added
- Native desktop chess board built with tkinter (stdlib only).
- Full legal-move generation including castling and pawn promotion
  (auto-promotes to queen).
- Move highlights: selected square, legal destinations, king in check.
- Alternating turns with check / checkmate / stalemate detection.
- Board flip toggle.
- SAN move notation panel (right column) with move-number display.
- Navigation buttons `⏮ ◀ ▶ ⏭` for replay mode.
- PGN file loading (single-file parser, no variant support yet).
- "New game" button resets the board and clears the move list.

---

[Unreleased]: https://github.com/your-org/taketaketake/compare/v1.0.0...HEAD
[1.0.0]:      https://github.com/your-org/taketaketake/compare/v0.4.0...v1.0.0
[0.4.0]:      https://github.com/your-org/taketaketake/compare/v0.3.0...v0.4.0
[0.3.0]:      https://github.com/your-org/taketaketake/compare/v0.2.0...v0.3.0
[0.2.0]:      https://github.com/your-org/taketaketake/compare/v0.1.0...v0.2.0
[0.1.0]:      https://github.com/your-org/taketaketake/releases/tag/v0.1.0
