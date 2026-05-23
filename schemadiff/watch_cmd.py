"""CLI command for the schema file watcher."""

import argparse
import sys

from schemadiff.watcher import watch_schema_file


def cmd_watch(args: argparse.Namespace) -> int:
    """Run the watch command."""
    try:
        watch_schema_file(
            path=args.schema_file,
            poll_interval=args.interval,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[watcher] Stopped.")
        return 0
    return 0


def build_watch_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the 'watch' subcommand."""
    parser = subparsers.add_parser(
        "watch",
        help="Watch a schema file and print diffs when it changes.",
    )
    parser.add_argument(
        "schema_file",
        help="Path to the schema JSON file to watch.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 2.0).",
    )
    parser.set_defaults(func=cmd_watch)
    return parser


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(prog="schemadiff-watch")
    _subs = _parser.add_subparsers()
    build_watch_parser(_subs)
    _args = _parser.parse_args()
    if hasattr(_args, "func"):
        sys.exit(_args.func(_args))
    else:
        _parser.print_help()
        sys.exit(1)
