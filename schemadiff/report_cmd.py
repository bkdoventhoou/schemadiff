"""CLI sub-command: generate a report from two schema files or history versions."""

import argparse
import json
import sys
from schemadiff.serializer import schema_from_dict
from schemadiff.differ import diff_schemas
from schemadiff.reporter import build_report, format_report
from schemadiff.history import SchemaHistory


def _load_schema(path: str):
    try:
        with open(path) as f:
            data = json.load(f)
        return schema_from_dict(data)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"Error loading schema from '{path}': {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_report_files(args: argparse.Namespace) -> None:
    """Compare two schema JSON files and print a report."""
    schema_a = _load_schema(args.schema_a)
    schema_b = _load_schema(args.schema_b)
    diff = diff_schemas(schema_a, schema_b)
    label = args.label or f"{args.schema_a} -> {args.schema_b}"
    report = build_report(diff, label=label)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(format_report(report))


def cmd_report_versions(args: argparse.Namespace) -> None:
    """Compare two history versions and print a report."""
    try:
        history = SchemaHistory.load(args.history_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error loading history: {exc}", file=sys.stderr)
        sys.exit(1)

    entry_a = history.get_version(args.version_a)
    entry_b = history.get_version(args.version_b)

    if entry_a is None:
        print(f"Version {args.version_a} not found.", file=sys.stderr)
        sys.exit(1)
    if entry_b is None:
        print(f"Version {args.version_b} not found.", file=sys.stderr)
        sys.exit(1)

    diff = diff_schemas(entry_a.schema, entry_b.schema)
    label = f"v{args.version_a} -> v{args.version_b}"
    report = build_report(diff, label=label)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(format_report(report))


def build_report_parser(subparsers) -> None:
    """Register 'report' sub-commands."""
    report_p = subparsers.add_parser("report", help="Generate a schema diff report")
    report_sub = report_p.add_subparsers(dest="report_cmd")

    # report files
    files_p = report_sub.add_parser("files", help="Report from two schema JSON files")
    files_p.add_argument("schema_a", help="Path to first schema JSON")
    files_p.add_argument("schema_b", help="Path to second schema JSON")
    files_p.add_argument("--label", default=None, help="Optional report label")
    files_p.add_argument("--json", action="store_true", help="Output as JSON")
    files_p.set_defaults(func=cmd_report_files)

    # report versions
    ver_p = report_sub.add_parser("versions", help="Report from two history versions")
    ver_p.add_argument("history_file", help="Path to history JSON file")
    ver_p.add_argument("version_a", type=int, help="First version number")
    ver_p.add_argument("version_b", type=int, help="Second version number")
    ver_p.add_argument("--json", action="store_true", help="Output as JSON")
    ver_p.set_defaults(func=cmd_report_versions)
