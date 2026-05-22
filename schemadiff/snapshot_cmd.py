"""CLI subcommands for snapshot and history management."""

import argparse
import sys

from schemadiff.differ import diff_schemas
from schemadiff.formatter import format_diff_as_string
from schemadiff.history import load_history, save_history
from schemadiff.serializer import schema_from_dict
from schemadiff.cli import _load_schema_from_file

DEFAULT_HISTORY_FILE = ".schemadiff_history.json"


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Save a schema snapshot to history."""
    schema = _load_schema_from_file(args.schema_file)
    if schema is None:
        print(f"Error: could not load schema from {args.schema_file}", file=sys.stderr)
        return 1

    history_path = args.history_file or DEFAULT_HISTORY_FILE
    history = load_history(history_path)
    entry = history.add_snapshot(schema, label=args.label or "")
    save_history(history, history_path)
    print(f"Snapshot saved: version={entry.version}, label={entry.label}, time={entry.timestamp}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """List all snapshots in history."""
    history_path = args.history_file or DEFAULT_HISTORY_FILE
    history = load_history(history_path)

    if not history.entries:
        print("No snapshots recorded yet.")
        return 0

    for entry in history.entries:
        table_count = len(entry.schema_dict.get("tables", {}))
        print(f"  v{entry.version:>3}  [{entry.label:<20}]  {entry.timestamp}  ({table_count} tables)")
    return 0


def cmd_diff_versions(args: argparse.Namespace) -> int:
    """Diff two historical schema versions."""
    history_path = args.history_file or DEFAULT_HISTORY_FILE
    history = load_history(history_path)

    from_entry = history.get_version(args.from_version)
    to_entry = history.get_version(args.to_version)

    if from_entry is None:
        print(f"Error: version {args.from_version} not found.", file=sys.stderr)
        return 1
    if to_entry is None:
        print(f"Error: version {args.to_version} not found.", file=sys.stderr)
        return 1

    schema_a = from_entry.load_schema()
    schema_b = to_entry.load_schema()
    diff = diff_schemas(schema_a, schema_b)
    print(format_diff_as_string(diff, use_color=not args.no_color))
    return 0


def build_snapshot_parser(subparsers):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--history-file", default=None, help="Path to history JSON file")

    snap = subparsers.add_parser("snapshot", parents=[common], help="Save a schema snapshot")
    snap.add_argument("schema_file", help="Schema JSON file to snapshot")
    snap.add_argument("--label", default="", help="Human-readable label for this snapshot")
    snap.set_defaults(func=cmd_snapshot)

    hist = subparsers.add_parser("history", parents=[common], help="List schema snapshots")
    hist.set_defaults(func=cmd_history)

    diffv = subparsers.add_parser("diff-versions", parents=[common], help="Diff two historical versions")
    diffv.add_argument("from_version", type=int, help="Source version number")
    diffv.add_argument("to_version", type=int, help="Target version number")
    diffv.add_argument("--no-color", action="store_true", help="Disable color output")
    diffv.set_defaults(func=cmd_diff_versions)
