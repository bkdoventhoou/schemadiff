"""Command-line interface for schemadiff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemadiff.schema import Schema, Table, Column, Index
from schemadiff.differ import diff_schemas
from schemadiff.formatter import format_diff


def _load_schema_from_file(path: Path) -> Schema:
    """Load a Schema from a JSON file produced by schemadiff export."""
    data = json.loads(path.read_text())
    tables: dict[str, Table] = {}
    for table_name, table_data in data.get("tables", {}).items():
        columns = {
            col_name: Column(
                name=col_name,
                col_type=col["type"],
                nullable=col.get("nullable", True),
                default=col.get("default"),
            )
            for col_name, col in table_data.get("columns", {}).items()
        }
        indexes = {
            idx_name: Index(
                name=idx_name,
                columns=idx["columns"],
                unique=idx.get("unique", False),
            )
            for idx_name, idx in table_data.get("indexes", {}).items()
        }
        tables[table_name] = Table(name=table_name, columns=columns, indexes=indexes)
    return Schema(tables=tables)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemadiff",
        description="Compare database schemas and show human-readable diffs.",
    )
    parser.add_argument("old", type=Path, help="Path to the old schema JSON file.")
    parser.add_argument("new", type=Path, help="Path to the new schema JSON file.")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color output."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed change information."
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if differences are found.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        old_schema = _load_schema_from_file(args.old)
        new_schema = _load_schema_from_file(args.new)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error loading schema file: {exc}", file=sys.stderr)
        return 2

    diff = diff_schemas(old_schema, new_schema)
    format_diff(diff, use_color=not args.no_color, verbose=args.verbose)

    if args.exit_code and diff.has_changes:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
