"""Diff engine for comparing two Schema objects and producing structured differences."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from schemadiff.schema import Schema


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


@dataclass
class SchemaDiff:
    added_tables: List[str] = field(default_factory=list)
    removed_tables: List[str] = field(default_factory=list)
    modified_tables: List[dict] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_tables or self.removed_tables or self.modified_tables)


def diff_schemas(source: Schema, target: Schema) -> SchemaDiff:
    """Compare source schema to target schema and return a SchemaDiff."""
    result = SchemaDiff()

    source_tables = set(source.tables.keys())
    target_tables = set(target.tables.keys())

    result.added_tables = sorted(target_tables - source_tables)
    result.removed_tables = sorted(source_tables - target_tables)

    for table_name in sorted(source_tables & target_tables):
        table_diff = _diff_tables(
            table_name,
            source.tables[table_name],
            target.tables[table_name],
        )
        if table_diff:
            result.modified_tables.append(table_diff)

    return result


def _diff_tables(name: str, source_table, target_table) -> dict:
    changes = {"table": name, "columns": [], "indexes": []}

    src_cols = source_table.columns
    tgt_cols = target_table.columns

    for col in sorted(set(tgt_cols) - set(src_cols)):
        changes["columns"].append({"change": ChangeType.ADDED, "column": col})
    for col in sorted(set(src_cols) - set(tgt_cols)):
        changes["columns"].append({"change": ChangeType.REMOVED, "column": col})
    for col in sorted(set(src_cols) & set(tgt_cols)):
        if src_cols[col] != tgt_cols[col]:
            changes["columns"].append(
                {"change": ChangeType.MODIFIED, "column": col,
                 "from": src_cols[col], "to": tgt_cols[col]}
            )

    src_idx = source_table.indexes
    tgt_idx = target_table.indexes

    for idx in sorted(set(tgt_idx) - set(src_idx)):
        changes["indexes"].append({"change": ChangeType.ADDED, "index": idx})
    for idx in sorted(set(src_idx) - set(tgt_idx)):
        changes["indexes"].append({"change": ChangeType.REMOVED, "index": idx})

    if changes["columns"] or changes["indexes"]:
        return changes
    return {}
