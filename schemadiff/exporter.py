"""Export schema diffs to various output formats (JSON, Markdown)."""

import json
from typing import Any

from schemadiff.differ import SchemaDiff, ChangeType


def diff_to_dict(diff: SchemaDiff) -> dict[str, Any]:
    """Convert a SchemaDiff to a plain dictionary suitable for JSON export."""
    result: dict[str, Any] = {
        "added_tables": [],
        "removed_tables": [],
        "modified_tables": {},
    }

    for table_name in diff.added_tables:
        result["added_tables"].append(table_name)

    for table_name in diff.removed_tables:
        result["removed_tables"].append(table_name)

    for table_name, changes in diff.modified_tables.items():
        table_changes: dict[str, Any] = {
            "added_columns": [],
            "removed_columns": [],
            "modified_columns": [],
            "added_indexes": [],
            "removed_indexes": [],
        }
        for change in changes:
            if change.change_type == ChangeType.COLUMN_ADDED:
                table_changes["added_columns"].append(change.name)
            elif change.change_type == ChangeType.COLUMN_REMOVED:
                table_changes["removed_columns"].append(change.name)
            elif change.change_type == ChangeType.COLUMN_MODIFIED:
                table_changes["modified_columns"].append(change.name)
            elif change.change_type == ChangeType.INDEX_ADDED:
                table_changes["added_indexes"].append(change.name)
            elif change.change_type == ChangeType.INDEX_REMOVED:
                table_changes["removed_indexes"].append(change.name)
        result["modified_tables"][table_name] = table_changes

    return result


def export_as_json(diff: SchemaDiff, indent: int = 2) -> str:
    """Serialize a SchemaDiff to a JSON string."""
    return json.dumps(diff_to_dict(diff), indent=indent)


def export_as_markdown(diff: SchemaDiff) -> str:
    """Render a SchemaDiff as a Markdown-formatted report."""
    lines: list[str] = ["# Schema Diff Report", ""]

    if not diff.added_tables and not diff.removed_tables and not diff.modified_tables:
        lines.append("_No changes detected._")
        return "\n".join(lines)

    if diff.added_tables:
        lines.append("## Added Tables")
        for name in sorted(diff.added_tables):
            lines.append(f"- `{name}`")
        lines.append("")

    if diff.removed_tables:
        lines.append("## Removed Tables")
        for name in sorted(diff.removed_tables):
            lines.append(f"- `{name}`")
        lines.append("")

    if diff.modified_tables:
        lines.append("## Modified Tables")
        for table_name, changes in sorted(diff.modified_tables.items()):
            lines.append(f"### `{table_name}`")
            for change in changes:
                symbol = "+" if "ADDED" in change.change_type.name else ("-" if "REMOVED" in change.change_type.name else "~")
                lines.append(f"- {symbol} [{change.change_type.name}] `{change.name}`")
            lines.append("")

    return "\n".join(lines)
