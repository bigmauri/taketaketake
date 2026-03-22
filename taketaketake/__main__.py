"""
taketaketake.__main__
=====================
Entry point for running the package directly::

    python -m taketaketake              # launch the GUI
    python -m taketaketake --version    # print version and exit
    python -m taketaketake --help       # show help
    python -m taketaketake --no-gui     # import-only check (headless)
"""

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taketaketake",
        description="TakeTakeTake — desktop chess application (Python 3, stdlib only).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m taketaketake                 Launch the GUI
  python -m taketaketake --version       Print the version

Keyboard shortcuts inside the application:
  ← / →        Previous / next move
  Home / End   Start / end of game
  ↑ / ↓        Previous / next variation
""",
    )
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Print the version number and exit.",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Load the package without launching the GUI (useful for testing).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point.

    Parameters
    ----------
    argv : list[str] | None
        Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code (0 = success).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from taketaketake import __version__
        print(f"TakeTakeTake v{__version__}")
        return 0

    if args.no_gui:
        from taketaketake import __version__
        print(f"TakeTakeTake v{__version__} — package loaded successfully.")
        return 0

    # Launch the GUI
    try:
        from taketaketake import run
        run()
    except ImportError as exc:
        print(
            f"Error: could not launch the GUI.\n"
            f"Make sure tkinter is installed (python3-tk).\n"
            f"Detail: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
