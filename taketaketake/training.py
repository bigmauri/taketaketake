"""
taketaketake/training.py
========================
Loader for the training-flow configuration file ``taketaketake.json``.

The file is searched in this order:
  1. The directory passed explicitly (e.g. the script's working directory)
  2. The parent directory of this module (i.e. the package root → project root)
  3. The current working directory at runtime

If the file cannot be found or parsed, a built-in fallback is returned so
the application always starts cleanly.  A warning is printed to stderr when
the fallback is used.

JSON schema (``taketaketake.json``)
------------------------------------
.. code-block:: json

    {
      "_comment": "optional free-text note",
      "_version": "1.0",
      "sections": [
        {
          "title":     "Section heading shown in the UI",
          "colour":    "#RRGGBB",
          "questions": ["Question 1", "Question 2"]
        }
      ]
    }

Each section must have ``title`` (str), ``colour`` (hex string), and
``questions`` (non-empty list of strings).  Extra keys are ignored.

Public API
----------
``load_training_config(search_dir=None)``
    Return a list of ``(title, colour, questions)`` tuples ready for the UI.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CONFIG_FILENAME = "taketaketake.json"

# Built-in fallback used when the JSON file is absent or invalid.
_FALLBACK: list[tuple[str, str, list[str]]] = [
    (
        "1 — Safety first  (Heisman CCT + LPDO)", "#C84B31",
        [
            "Is my king safe? Any immediate mating threats?",
            "Does my opponent have Checks, Captures or Threats (CCT) "
            "I must answer right now?",
            "Are any of my pieces loose (undefended)? "
            "Loose Pieces Drop Off — LPDO.",
            "Was my opponent's last move a mistake? "
            "Can I exploit it with a CCT of my own?",
            "After my candidate move, what are my opponent's CCT replies? "
            "Is my move safe?",
        ],
    ),
    (
        "2 — Read the imbalances  (Silman)", "#7090C8",
        [
            "Material balance: who is ahead and by how much?",
            "Pawn structure: passed pawns, isolanis, doubled pawns, "
            "pawn majorities — who benefits?",
            "Space: who controls more of the board? "
            "Which sector matters most right now?",
            "Piece activity: which piece is worst placed? "
            "How can it be improved or exchanged?",
            "Open files & diagonals: who benefits from the open lines?",
            "Weak squares & outposts: squares that cannot be guarded by "
            "pawns — can a piece be planted there?",
            "King safety: is either king exposed? "
            "Is a kingside or queenside attack feasible?",
            "Bishop pair: does one side own both bishops? "
            "Is the position open (favours bishops) or closed (knights)?",
        ],
    ),
    (
        "3 — Aagaard's three questions", "#50A878",
        [
            "What are the weaknesses in the position "
            "(mine and my opponent's)?",
            "What is my worst placed piece, and how can I improve it?",
            "What is my opponent's plan? "
            "What are they trying to achieve in the next few moves?",
        ],
    ),
    (
        "4 — Form a plan  (Silman → Kotov)", "#A89850",
        [
            "Which imbalance gives me the best winning chances? "
            "Build your plan around your strongest imbalance.",
            "What is the key area of the board right now — "
            "kingside attack, queenside expansion, or central control?",
            "Short-term goal: what do I want to achieve in the next 2–3 moves?",
            "Long-term goal: pawn break, piece re-routing, endgame structure?",
            "Does my opponent have a plan I must prevent "
            "or prepare a counter to?",
        ],
    ),
    (
        "5 — Calculate candidates  (Kotov tree)", "#8CAEC8",
        [
            "List 3–5 candidate moves. Do NOT fall in love with "
            "the first idea — look for alternatives.",
            "For each candidate, calculate at least one full reply: "
            "your move → opponent's best → your response.",
            "Analyse forcing lines (CCT) first; calculate until a "
            "quiescent (quiet) position is reached.",
            "Evaluate the resulting position: who stands better and why? "
            "(+/−, =, ∞ …)",
            "Falsify your favourite move: actively look for a refutation. "
            "Can your opponent do better than you thought?",
            "Play the move with the best evaluation after a final safety check.",
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _candidate_paths(search_dir: pathlib.Path | str | None) -> list[pathlib.Path]:
    """
    Return an ordered list of paths to try when looking for the config file.

    Parameters
    ----------
    search_dir : Path | str | None
        Optional explicit directory to check first.
    """
    candidates: list[pathlib.Path] = []

    if search_dir is not None:
        candidates.append(pathlib.Path(search_dir) / CONFIG_FILENAME)

    # Parent of this file's directory = project root (taketaketake/../)
    pkg_parent = pathlib.Path(__file__).parent.parent
    candidates.append(pkg_parent / CONFIG_FILENAME)

    # Current working directory
    candidates.append(pathlib.Path.cwd() / CONFIG_FILENAME)

    return candidates


def find_config_file(search_dir: pathlib.Path | str | None = None) -> pathlib.Path | None:
    """
    Search for ``taketaketake.json`` and return its path, or ``None`` if not found.

    Parameters
    ----------
    search_dir : Path | str | None
        Optional directory to search first.
    """
    for path in _candidate_paths(search_dir):
        if path.is_file():
            return path
    return None


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class ConfigError(ValueError):
    """Raised when the JSON file exists but has an invalid structure."""


def _validate(data: Any) -> list[tuple[str, str, list[str]]]:
    """
    Validate the parsed JSON and return a clean list of sections.

    Parameters
    ----------
    data : Any
        Raw Python object obtained from ``json.load``.

    Returns
    -------
    list[tuple[str, str, list[str]]]
        List of ``(title, colour, questions)`` tuples.

    Raises
    ------
    ConfigError
        If the data does not conform to the expected schema.
    """
    if not isinstance(data, dict):
        raise ConfigError("Top-level JSON value must be an object.")

    raw_sections = data.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ConfigError(
            'The JSON file must contain a non-empty "sections" array.'
        )

    result: list[tuple[str, str, list[str]]] = []

    for idx, sec in enumerate(raw_sections):
        if not isinstance(sec, dict):
            raise ConfigError(f"sections[{idx}] must be an object.")

        title = sec.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ConfigError(
                f'sections[{idx}]["title"] must be a non-empty string.'
            )

        colour = sec.get("colour", "#8CAEC8")
        if not isinstance(colour, str):
            raise ConfigError(
                f'sections[{idx}]["colour"] must be a hex colour string.'
            )
        # Normalise: accept "color" as well
        if not colour:
            colour = sec.get("color", "#8CAEC8")

        questions = sec.get("questions")
        if not isinstance(questions, list) or not questions:
            raise ConfigError(
                f'sections[{idx}]["questions"] must be a non-empty array.'
            )
        for qi, q in enumerate(questions):
            if not isinstance(q, str) or not q.strip():
                raise ConfigError(
                    f'sections[{idx}]["questions"][{qi}] must be a non-empty string.'
                )

        result.append((title.strip(), colour.strip(), [q.strip() for q in questions]))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def load_training_config(
    search_dir: pathlib.Path | str | None = None,
) -> tuple[list[tuple[str, str, list[str]]], pathlib.Path | None]:
    """
    Load the training-flow configuration from ``taketaketake.json``.

    Searches for the file, parses it, validates the schema, and returns the
    section data ready for the UI.  Falls back to the built-in defaults if
    the file is missing or malformed, printing a warning to stderr.

    Parameters
    ----------
    search_dir : Path | str | None
        Optional extra directory to check before the standard locations.

    Returns
    -------
    sections : list[tuple[str, str, list[str]]]
        Each entry is ``(title, colour, questions_list)``.
    config_path : Path | None
        The path of the file that was loaded, or ``None`` if the fallback
        was used.

    Examples
    --------
    >>> sections, path = load_training_config()
    >>> print(path)
    /home/user/projects/taketaketake/taketaketake.json
    >>> for title, colour, questions in sections:
    ...     print(title, f"({len(questions)} questions)")
    """
    config_path = find_config_file(search_dir)

    if config_path is None:
        print(
            f"[taketaketake] Warning: '{CONFIG_FILENAME}' not found. "
            "Using built-in training defaults.",
            file=sys.stderr,
        )
        return _FALLBACK.copy(), None

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        sections = _validate(raw)
        return sections, config_path
    except json.JSONDecodeError as exc:
        print(
            f"[taketaketake] Warning: '{config_path}' is not valid JSON "
            f"({exc}). Using built-in training defaults.",
            file=sys.stderr,
        )
        return _FALLBACK.copy(), None
    except ConfigError as exc:
        print(
            f"[taketaketake] Warning: '{config_path}' has an invalid structure "
            f"({exc}). Using built-in training defaults.",
            file=sys.stderr,
        )
        return _FALLBACK.copy(), None
