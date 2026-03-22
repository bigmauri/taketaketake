# Contributing to TakeTakeTake

Thank you for taking the time to contribute! This document explains how to
report bugs, propose features, and submit code changes.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Report a Bug](#how-to-report-a-bug)
4. [How to Request a Feature](#how-to-request-a-feature)
5. [Development Workflow](#development-workflow)
6. [Commit Message Convention](#commit-message-convention)
7. [Pull Request Guidelines](#pull-request-guidelines)
8. [Code Style](#code-style)
9. [Testing](#testing)
10. [Project Structure](#project-structure)

---

## Code of Conduct

This project follows a simple rule: **be respectful**.  
Constructive criticism of code is welcome; personal attacks are not.

---

## Getting Started

### Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.10 | 3.12 recommended |
| tkinter | bundled with Python | `sudo apt install python3-tk` on Debian/Ubuntu |
| git | any recent | — |

No third-party Python packages are required to run the application.  
`pytest` and `pyflakes` are only needed for development.

### Local setup

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/taketaketake.git
cd taketaketake

# 2. Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode + dev tools
pip install -e .
pip install pytest pyflakes

# 4. Run the test suite to confirm everything works
python -m pytest tests/ -v

# 5. Launch the application
python -m taketaketake
```

---

## How to Report a Bug

1. Search the [existing issues](https://github.com/your-org/taketaketake/issues)
   to avoid duplicates.
2. Open a new issue using the **Bug Report** template and include:
   - Operating system and Python version (`python --version`)
   - Steps to reproduce the problem
   - Expected behaviour vs. actual behaviour
   - Any relevant PGN file or move sequence that triggers the bug
   - Full traceback if an exception was raised

---

## How to Request a Feature

1. Check the [existing issues](https://github.com/your-org/taketaketake/issues)
   and [open pull requests](https://github.com/your-org/taketaketake/pulls).
2. Open a new issue using the **Feature Request** template.
3. Describe the use case, not just the implementation.  
   *"I want to be able to export the current position as a FEN string"*  
   is more useful than *"add a `to_fen()` method"*.

---

## Development Workflow

We follow a **feature-branch** workflow:

```
main        ← stable releases only
develop     ← integration branch (default target for PRs)
feature/*   ← new features
fix/*       ← bug fixes
docs/*      ← documentation changes only
refactor/*  ← code refactoring without behaviour changes
test/*      ← test-only additions or changes
```

### Step-by-step

```bash
# Start from a fresh develop
git checkout develop
git pull origin develop

# Create your branch
git checkout -b feature/en-passant-support

# Make your changes, commit often
git add -p
git commit -m "feat(engine): add en-passant capture logic"

# Keep your branch up to date
git fetch origin
git rebase origin/develop

# Push and open a PR
git push origin feature/en-passant-support
```

---

## Commit Message Convention

We use a simplified version of
[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body — wrap at 72 characters]

[optional footer: Closes #<issue-number>]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | A new feature visible to the user |
| `fix` | A bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `chore` | Build scripts, CI, dependency bumps |
| `perf` | Performance improvement |
| `style` | Formatting, whitespace — no logic change |

### Scopes

Use the sub-module name as scope: `engine`, `tree`, `pgn`, `app`, `constants`,
`tests`, `ci`, `docs`.

### Examples

```
feat(pgn): support FEN SetUp header on import
fix(engine): castling incorrectly allowed through attacked square
refactor(tree): extract ancestors() into a standalone generator
test(engine): add Scholar's mate regression test
docs(README): add badge for PyPI version
chore(ci): add Python 3.13 to test matrix
```

---

## Pull Request Guidelines

### Before opening a PR

- [ ] All existing tests pass: `python -m pytest tests/ -v`
- [ ] New behaviour is covered by at least one test
- [ ] `pyflakes` reports no errors on changed files
- [ ] The branch is rebased on the latest `develop`
- [ ] The PR description explains *what* changed and *why*

### PR title

Follow the same convention as commit messages:

```
feat(pgn): support FEN SetUp header on import
```

### Review process

1. A maintainer will review within a few days.
2. Requested changes must be addressed before merging.
3. Squash-merge is preferred to keep `develop` history clean.

### Merging policy

| Branch target | Strategy | Who can merge |
|--------------|----------|--------------|
| `develop` | Squash merge | Maintainers |
| `main` | Merge commit (tagged release) | Maintainers only |

---

## Code Style

TakeTakeTake has no external linter configuration beyond `pyflakes`. We ask
for the following:

### General

- **Python 3.10+** syntax only. Do not use features introduced in 3.11+
  unless the minimum version is bumped accordingly.
- Prefer **clarity over brevity**. One-liners are fine when obvious;
  complex logic should be broken into named steps.
- **No external dependencies.** The entire package must run with the
  Python standard library only.

### Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Module | `snake_case` | `pgn.py` |
| Class | `PascalCase` | `MoveNode` |
| Function / method | `snake_case` | `build_san()` |
| Private helper | `_snake_case` | `_tokenize_pgn_body()` |
| Constant | `UPPER_SNAKE` | `NAG_SYM` |

### Type hints

- All **public functions** must have complete type annotations.
- Private helpers should have annotations where it aids readability.
- Use `from __future__ import annotations` in files with forward references.

### Docstrings

Public modules, classes, and functions must have a docstring.  
Format (NumPy-style condensed):

```python
def legal_moves(board: list, r: int, c: int) -> list[tuple[int, int]]:
    """
    Return all legal destination squares for the piece at (r, c).

    Parameters
    ----------
    board : list
        8×8 board state.
    r, c : int
        Row and column of the piece (0-based, row 0 = rank 8).

    Returns
    -------
    list[tuple[int, int]]
        Legal (row, col) destinations, including castling when available.
    """
```

### Import order (within each file)

1. Standard library
2. Blank line
3. Relative imports from the package (`from .module import …`)

---

## Testing

### Running the suite

```bash
# All tests, verbose
python -m pytest tests/ -v

# Single test class
python -m pytest tests/test_taketaketake.py::TestArrocco -v

# With coverage (requires pip install pytest-cov)
python -m pytest tests/ --cov=taketaketake --cov-report=term-missing
```

### Writing new tests

- Place all tests in `tests/test_taketaketake.py`.
- Every test class inherits from `unittest.TestCase`.
- Test names must be descriptive: `test_castling_not_allowed_through_check`.
- Use the `play_moves()` and `place()` helpers already defined in the file.
- **GUI code** (`app.py`) is excluded from the test requirement — tkinter
  cannot run headlessly without a display server.

### Test categories

| Class | Covers |
|-------|--------|
| `TestUtilita` | Pure utility functions |
| `TestPosizioneIniziale` | Starting board setup |
| `TestMosseGrezze` | `raw_moves` for all piece types |
| `TestScacco` | Check detection |
| `TestMosseLegali` | Legal move filtering, pins, stalemate |
| `TestApplyMove` | Board mutation, castling, promotion |
| `TestArrocco` | All castling legality conditions |
| `TestBuildSan` | SAN generation and disambiguation |
| `TestSanToMove` | SAN parsing roundtrip |
| `TestMoveNode` | Tree structure and navigation |
| `TestParserPGN` | PGN parsing (headers, comments, NAG, variants) |
| `TestTreeToPgn` | PGN serialisation and roundtrip |
| `TestPartitiCelebri` | Integration: famous game openings and mates |

---

## Project Structure

```
taketaketake/               Python package (stdlib only)
├── __init__.py             Public API + lazy GUI import
├── __main__.py             CLI entry point (python -m taketaketake)
├── constants.py            Colours, piece symbols, NAG definitions
├── engine.py               Pure chess logic (moves, SAN, check…)
├── tree.py                 MoveNode / GameTree data structures
├── pgn.py                  PGN parser and serialiser
└── app.py                  tkinter GUI (ChessApp)

tests/
└── test_taketaketake.py    103 unit tests (stdlib unittest)

.github/
└── workflows/
    └── ci.yml              CI pipeline (lint → test → syntax → import → build)

pyproject.toml              Package metadata, pytest / coverage config
README.md                   User-facing documentation
CONTRIBUTING.md             This file
CHANGELOG.md                Version history
.gitignore
```

---

## Questions?

Open a [GitHub Discussion](https://github.com/your-org/taketaketake/discussions)
or tag a maintainer in an issue. We are happy to help!
