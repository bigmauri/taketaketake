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
11. [Questions](#questions)

---

## Code of Conduct

This project follows a simple rule: **be respectful.**
Constructive criticism of code is always welcome; personal attacks are not.
We are committed to providing a welcoming and inclusive environment for everyone,
regardless of experience level, background, or identity.

---

## Getting Started

### Prerequisites

| Tool    | Minimum version | Notes                                        |
|---------|-----------------|----------------------------------------------|
| Python  | 3.10            | 3.12 recommended                             |
| tkinter | bundled         | `sudo apt install python3-tk` on Debian/Ubuntu |
| git     | any recent      | —                                            |

No third-party Python packages are required to run the application.
`pytest` and `pyflakes` are only needed for development work.

### Local setup

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/taketaketake.git
cd taketaketake

# 2. Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode and dev tools
pip install -e .
pip install pytest pyflakes

# 4. Run the test suite to confirm everything works
python -m pytest tests/ -v

# 5. Launch the application
python -m taketaketake
```

---

## How to Report a Bug

1. Search the [existing issues](https://github.com/bigmauri/taketaketake/issues)
   to avoid duplicates.
2. Open a new issue using the **Bug Report** template and include:
   - Operating system and Python version (`python --version`)
   - Steps to reproduce the problem, as minimal as possible
   - Expected behaviour vs. actual behaviour
   - Any relevant PGN file or move sequence that triggers the bug
   - Full traceback if an exception was raised

The more detail you provide, the faster the issue can be resolved.

---

## How to Request a Feature

1. Check the [existing issues](https://github.com/bigmauri/taketaketake/issues)
   and [open pull requests](https://github.com/bigmauri/taketaketake/pulls) to
   avoid duplicates.
2. Open a new issue using the **Feature Request** template.
3. Describe the **use case**, not just the implementation.

   > *"I want to be able to export the current position as a FEN string"*
   > is more useful than *"add a `to_fen()` method"*.

Features that keep the project dependency-free and stay within the scope of a
desktop chess viewer/editor are most likely to be accepted.

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
# 1. Start from a fresh develop
git checkout develop
git pull origin develop

# 2. Create your branch
git checkout -b feature/en-passant-support

# 3. Make your changes, commit often
git add -p
git commit -m "feat(engine): add en-passant capture logic"

# 4. Keep your branch up to date with develop
git fetch origin
git rebase origin/develop

# 5. Push and open a PR
git push origin feature/en-passant-support
```

---

## Commit Message Convention

We use a simplified version of [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body — wrap at 72 characters]

[optional footer: Closes #<issue-number>]
```

### Types

| Type       | When to use                                             |
|------------|---------------------------------------------------------|
| `feat`     | A new feature visible to the user                       |
| `fix`      | A bug fix                                               |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test`     | Adding or updating tests                                |
| `docs`     | Documentation only                                      |
| `chore`    | Build scripts, CI configuration, dependency bumps       |
| `perf`     | Performance improvement                                 |
| `style`    | Formatting or whitespace — no logic change              |

### Scopes

Use the sub-module name as the scope: `engine`, `tree`, `pgn`, `app`,
`constants`, `tests`, `ci`, `docs`.

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

- All existing tests pass: `python -m pytest tests/ -v`
- New behaviour is covered by at least one new test
- `pyflakes` reports no errors on changed files
- The branch is rebased on the latest `develop`
- The PR description explains *what* changed and *why*

### PR title

Follow the same Conventional Commits format used for commit messages:

```
feat(pgn): support FEN SetUp header on import
```

### Review process

1. A maintainer will review within a few days.
2. Requested changes must be addressed before merging.
3. Squash-merge is preferred to keep `develop` history clean.

### Merging policy

| Branch target | Strategy                    | Who can merge     |
|---------------|-----------------------------|-------------------|
| `develop`     | Squash merge                | Maintainers       |
| `main`        | Merge commit (tagged release) | Maintainers only |

---

## Code Style

TakeTakeTake has no external linter configuration beyond `pyflakes`. We ask
contributors to follow the guidelines below.

### General principles

- **Python 3.10+ syntax only.** Do not use features introduced in 3.11 or
  later unless the minimum supported version is bumped accordingly.
- Prefer **clarity over brevity.** One-liners are fine when the intent is
  obvious; complex logic should be broken into named steps with clear variable
  names.
- **No external dependencies.** The entire package must run with the Python
  standard library only. Do not add third-party imports, even as optional
  dependencies.

### Naming conventions

| Entity            | Convention    | Example                  |
|-------------------|---------------|--------------------------|
| Module            | `snake_case`  | `pgn.py`                 |
| Class             | `PascalCase`  | `MoveNode`               |
| Function / method | `snake_case`  | `build_san()`            |
| Private helper    | `_snake_case` | `_tokenize_pgn_body()`   |
| Constant          | `UPPER_SNAKE` | `NAG_SYM`                |

### Type hints

- All **public functions** must have complete type annotations.
- Private helpers should have annotations wherever they aid readability.
- Use `from __future__ import annotations` in files that contain forward
  references.

### Docstrings

Public modules, classes, and functions must have a docstring.
Use the condensed NumPy style:

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

1. Standard library modules
2. *(blank line)*
3. Relative imports from the package (`from .module import …`)

---

## Testing

### Running the suite

```bash
# All tests, verbose output
python -m pytest tests/ -v

# A single test class
python -m pytest tests/test_taketaketake.py::TestArrocco -v

# With a coverage report (requires pytest-cov)
python -m pytest tests/ --cov=taketaketake --cov-report=term-missing
```

### Writing new tests

- Place all tests in `tests/test_taketaketake.py`.
- Every test class must inherit from `unittest.TestCase`.
- Test method names must be descriptive:
  `test_castling_not_allowed_through_check` rather than `test_castle`.
- Use the `play_moves()` and `place()` helper functions already defined in
  the file to set up board positions concisely.
- **GUI code** (`app.py`) is excluded from the test requirement — tkinter
  cannot run headlessly without a display server.

### Test classes overview

| Class                  | What it covers                                              |
|------------------------|-------------------------------------------------------------|
| `TestUtilita`          | Pure utility functions (`sq`, `opponent`, `in_bounds`, …)  |
| `TestPosizioneIniziale`| Correctness of the starting board layout                    |
| `TestMosseGrezze`      | `raw_moves` output for every piece type                     |
| `TestScacco`           | `is_in_check` and `find_king`                               |
| `TestMosseLegali`      | Pins, check filtering, checkmate, stalemate                 |
| `TestApplyMove`        | Board mutation, castling, pawn promotion, immutability      |
| `TestArrocco`          | All castling legality conditions                            |
| `TestBuildSan`         | SAN generation, disambiguation, check/mate suffixes         |
| `TestSanToMove`        | Inverse SAN parsing and full roundtrip                      |
| `TestMoveNode`         | Tree node structure, `depth()`, `main_line()`               |
| `TestParserPGN`        | PGN parsing: headers, comments, NAG, nested variations      |
| `TestTreeToPgn`        | PGN serialisation and parse→serialize roundtrip             |
| `TestPartitiCelebri`   | Integration tests: Scholar's mate, Fool's mate, openings    |

---

## Project Structure

```
taketaketake/                    Python package (stdlib only)
├── __init__.py                  Public API + lazy GUI import
├── __main__.py                  CLI entry point: python -m taketaketake
├── constants.py                 Colour palette, piece symbols, NAG map
├── engine.py                    Pure chess logic (moves, SAN, check detection…)
├── tree.py                      MoveNode / GameTree data structures
├── pgn.py                       PGN parser and serialiser
└── app.py                       tkinter GUI (ChessApp)

tests/
└── test_taketaketake.py         103 unit tests across 13 classes (stdlib unittest)

.github/
└── workflows/
    └── ci.yml                   CI pipeline: lint → test matrix → syntax check

pyproject.toml                   Package metadata, pytest / coverage config
README.md                        User-facing documentation
CONTRIBUTING.md                  This file
CHANGELOG.md                     Version history
.gitignore
```

---

## Questions?

Open a [GitHub Discussion](https://github.com/bigmauri/taketaketake/discussions)
or tag a maintainer in a relevant issue. We are happy to help!
