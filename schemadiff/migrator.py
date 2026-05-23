"""Generate SQL migration statements from schema diffs."""

from dataclasses import dataclass
from typing import List
from schemadiff.differ import SchemaDiff, ChangeType


@dataclass
class MigrationStatement:
    sql: str
    description: str

    def __str__(self) -> str:
        return self.sql


def _col_def(col) -> str:
    nullable = "" if col.nullable else " NOT NULL"
    default = f" DEFAULT {col.default}" if col.default is not None else ""
    return f"{col.name} {col.col_type}{nullable}{default}"


def generate_migration(diff: SchemaDiff) -> List[MigrationStatement]:
    """Return ordered SQL statements to migrate from old schema to new."""
    statements: List[MigrationStatement] = []

    for change in diff.changes:
        table = change.table_name

        if change.change_type == ChangeType.TABLE_ADDED:
            tbl = change.new_value
            col_defs = ",\n  ".join(_col_def(c) for c in tbl.columns.values())
            sql = f"CREATE TABLE {table} (\n  {col_defs}\n);"
            statements.append(MigrationStatement(sql=sql, description=f"Create table {table}"))

        elif change.change_type == ChangeType.TABLE_REMOVED:
            sql = f"DROP TABLE {table};"
            statements.append(MigrationStatement(sql=sql, description=f"Drop table {table}"))

        elif change.change_type == ChangeType.COLUMN_ADDED:
            col = change.new_value
            sql = f"ALTER TABLE {table} ADD COLUMN {_col_def(col)};"
            statements.append(MigrationStatement(sql=sql, description=f"Add column {change.column_name} to {table}"))

        elif change.change_type == ChangeType.COLUMN_REMOVED:
            sql = f"ALTER TABLE {table} DROP COLUMN {change.column_name};"
            statements.append(MigrationStatement(sql=sql, description=f"Drop column {change.column_name} from {table}"))

        elif change.change_type == ChangeType.COLUMN_MODIFIED:
            col = change.new_value
            sql = f"ALTER TABLE {table} MODIFY COLUMN {_col_def(col)};"
            statements.append(MigrationStatement(sql=sql, description=f"Modify column {change.column_name} in {table}"))

    return statements


def migration_to_sql(diff: SchemaDiff) -> str:
    """Return a single SQL string with all migration statements."""
    stmts = generate_migration(diff)
    if not stmts:
        return "-- No changes detected\n"
    lines = [f"-- {s.description}\n{s.sql}" for s in stmts]
    return "\n\n".join(lines) + "\n"
