"""CLI commands for schema snapshot tagging."""

import argparse
import json
import os
from schemadiff.history import SchemaHistory
from schemadiff.tagger import SchemaTagger
from schemadiff.differ import diff_schemas
from schemadiff.formatter import format_diff_as_string


def _load_tagger(history_file: str) -> tuple:
    if not os.path.exists(history_file):
        history = SchemaHistory()
        tagger = SchemaTagger(history=history)
        return history, tagger
    with open(history_file, "r") as f:
        data = json.load(f)
    history = SchemaHistory.from_dict(data.get("history", {"snapshots": []}))
    tagger = SchemaTagger.tags_from_dict(history, data.get("tags", {}))
    return history, tagger


def _save_tagger(history_file: str, history: SchemaHistory, tagger: SchemaTagger) -> None:
    data = {
        "history": history.to_dict(),
        "tags": tagger.tags_as_dict(),
    }
    with open(history_file, "w") as f:
        json.dump(data, f, indent=2)


def cmd_tag_add(args: argparse.Namespace) -> int:
    history, tagger = _load_tagger(args.history_file)
    try:
        version = int(args.version) if args.version else None
        entry = tagger.add_tag(args.tag, version=version, description=args.description or "")
        _save_tagger(args.history_file, history, tagger)
        print(f"Tagged version {entry.version} as '{entry.tag}'")
        return 0
    except ValueError as e:
        print(f"Error: {e}")
        return 1


def cmd_tag_list(args: argparse.Namespace) -> int:
    history, tagger = _load_tagger(args.history_file)
    tags = tagger.list_tags()
    if not tags:
        print("No tags defined.")
        return 0
    for t in tags:
        desc = f" — {t.description}" if t.description else ""
        print(f"  {t.tag:<20} -> v{t.version}{desc}")
    return 0


def cmd_tag_diff(args: argparse.Namespace) -> int:
    history, tagger = _load_tagger(args.history_file)
    snap_a = tagger.resolve_snapshot(args.tag_a)
    snap_b = tagger.resolve_snapshot(args.tag_b)
    if snap_a is None:
        print(f"Error: tag '{args.tag_a}' not found")
        return 1
    if snap_b is None:
        print(f"Error: tag '{args.tag_b}' not found")
        return 1
    diff = diff_schemas(snap_a.schema, snap_b.schema)
    print(format_diff_as_string(diff, use_color=False))
    return 0


def build_tag_parser(subparsers: argparse._SubParsersAction) -> None:
    tag_p = subparsers.add_parser("tag", help="Manage schema snapshot tags")
    tag_sub = tag_p.add_subparsers(dest="tag_cmd")

    add_p = tag_sub.add_parser("add", help="Add a tag to a snapshot version")
    add_p.add_argument("tag", help="Tag name")
    add_p.add_argument("--version", default=None, help="Version to tag (default: latest)")
    add_p.add_argument("--description", default="", help="Optional tag description")
    add_p.add_argument("--history-file", default="schema_history.json")
    add_p.set_defaults(func=cmd_tag_add)

    list_p = tag_sub.add_parser("list", help="List all tags")
    list_p.add_argument("--history-file", default="schema_history.json")
    list_p.set_defaults(func=cmd_tag_list)

    diff_p = tag_sub.add_parser("diff", help="Diff two tagged snapshots")
    diff_p.add_argument("tag_a", help="First tag")
    diff_p.add_argument("tag_b", help="Second tag")
    diff_p.add_argument("--history-file", default="schema_history.json")
    diff_p.set_defaults(func=cmd_tag_diff)
