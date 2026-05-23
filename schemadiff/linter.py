"""Schema linting: opinionated style and convention checks beyond validation."""

from dataclasses import dataclass, field
from typing import List
from schemadiff.schema import Schema, Table, Column


@dataclass
class LintIssue:
    table: str
    column: str  # empty string if issue is table-level
    message: str
    severity: str  # 'warning' or 'error'

    def __str__(self) -> str:
        loc = self.table if not self.column else f"{self.table}.{self.column}"
        return f"[{self.severity.upper()}] {loc}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    def __bool__(self) -> bool:
        """True when there are no issues."""
        return len(self.issues) == 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def _lint_column(table_name: str, col: Column) -> List[LintIssue]:
    issues: List[LintIssue] = []
    name = col.name

    if name != name.lower():
        issues.append(LintIssue(table_name, name, "Column name should be lowercase", "warning"))

    if " " in name:
        issues.append(LintIssue(table_name, name, "Column name contains spaces", "error"))

    if col.col_type.upper() in ("TEXT", "BLOB") and col.nullable is False:
        issues.append(LintIssue(table_name, name, f"{col.col_type} column marked NOT NULL; consider VARCHAR with length", "warning"))

    return issues


def _lint_table(table: Table) -> List[LintIssue]:
    issues: List[LintIssue] = []
    name = table.name

    if name != name.lower():
        issues.append(LintIssue(name, "", "Table name should be lowercase", "warning"))

    if " " in name:
        issues.append(LintIssue(name, "", "Table name contains spaces", "error"))

    has_primary = any(idx.primary for idx in table.indexes)
    if not has_primary:
        issues.append(LintIssue(name, "", "Table has no primary key index", "warning"))

    col_names = [c.name for c in table.columns]
    if len(col_names) != len(set(col_names)):
        issues.append(LintIssue(name, "", "Duplicate column names detected", "error"))

    for col in table.columns:
        issues.extend(_lint_column(name, col))

    return issues


def lint_schema(schema: Schema) -> LintResult:
    """Run all lint checks on a schema and return a LintResult."""
    issues: List[LintIssue] = []
    for table in schema.tables:
        issues.extend(_lint_table(table))
    return LintResult(issues=issues)
