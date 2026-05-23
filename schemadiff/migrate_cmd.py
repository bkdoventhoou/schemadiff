"""CLI command for generating SQL migration scripts from schema diffs."""

import argparse
import sys
from schemadiff.serializer import schema_from_dict
from schemadiff.differ import diff_schemas
from schemadiff.migrator import migration_to_sql
from schemadiff.history import SchemaHistory


def _load_schema(path: str):
    import json
    try:
        with open(path) as f:
            data = json.load(f)
        return schema_from_dict(data)
    except (OSError, ValueError) as exc:
        print(f"Error loading schema from {path!r}: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_migrate_files(args) -> None:
    """Generate migration SQL between two schema JSON files."""
    old_schema = _load_schema(args.old)
    new_schema = _load_schema(args.new)
    diff = diff_schemas(old_schema, new_schema)
    sql = migration_to_sql(diff)
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(sql)
            print(f"Migration written to {args.output}")
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(sql, end="")


def cmd_migrate_versions(args) -> None:
    """Generate migration SQL between two history snapshot versions."""
    try:
        history = SchemaHistory.load(args.history_file)
    except (OSError, ValueError) as exc:
        print(f"Error loading history: {exc}", file=sys.stderr)
        sys.exit(1)

    old_entry = history.get_version(args.from_version)
    new_entry = history.get_version(args.to_version)

    if old_entry is None:
        print(f"Version {args.from_version} not found.", file=sys.stderr)
        sys.exit(1)
    if new_entry is None:
        print(f"Version {args.to_version} not found.", file=sys.stderr)
        sys.exit(1)

    diff = diff_schemas(old_entry.schema, new_entry.schema)
    sql = migration_to_sql(diff)
    print(sql, end="")


def build_migrate_parser(subparsers=None) -> argparse.ArgumentParser:
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Generate SQL migration from schema diffs")
        sub = parser.add_subparsers(dest="migrate_cmd")
    else:
        parser = subparsers.add_parser("migrate", help="Generate SQL migration scripts")
        sub = parser.add_subparsers(dest="migrate_cmd")

    files_p = sub.add_parser("files", help="Diff two schema JSON files")
    files_p.add_argument("old", help="Path to old schema JSON")
    files_p.add_argument("new", help="Path to new schema JSON")
    files_p.add_argument("-o", "--output", help="Write SQL to file instead of stdout")
    files_p.set_defaults(func=cmd_migrate_files)

    ver_p = sub.add_parser("versions", help="Diff two history snapshot versions")
    ver_p.add_argument("history_file", help="Path to history JSON file")
    ver_p.add_argument("from_version", type=int, help="Source version number")
    ver_p.add_argument("to_version", type=int, help="Target version number")
    ver_p.set_defaults(func=cmd_migrate_versions)

    return parser
