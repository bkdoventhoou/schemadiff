"""Generate summary reports from schema diffs and history."""

from dataclasses import dataclass, field
from typing import List, Optional
from schemadiff.differ import SchemaDiff, ChangeType


@dataclass
class ReportSummary:
    total_changes: int
    added_tables: List[str] = field(default_factory=list)
    removed_tables: List[str] = field(default_factory=list)
    modified_tables: List[str] = field(default_factory=list)
    label: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "total_changes": self.total_changes,
            "added_tables": self.added_tables,
            "removed_tables": self.removed_tables,
            "modified_tables": self.modified_tables,
        }

    @property
    def has_changes(self) -> bool:
        """Return True if the summary contains any changes."""
        return self.total_changes > 0


def build_report(diff: SchemaDiff, label: Optional[str] = None) -> ReportSummary:
    """Build a ReportSummary from a SchemaDiff."""
    added = []
    removed = []
    modified = []

    for change in diff.changes:
        if change.change_type == ChangeType.TABLE_ADDED:
            added.append(change.table_name)
        elif change.change_type == ChangeType.TABLE_REMOVED:
            removed.append(change.table_name)
        else:
            table = change.table_name
            if table not in modified:
                modified.append(table)

    return ReportSummary(
        total_changes=len(diff.changes),
        added_tables=added,
        removed_tables=removed,
        modified_tables=modified,
        label=label,
    )


def format_report(summary: ReportSummary) -> str:
    """Render a ReportSummary as a human-readable string."""
    lines = []
    header = f"Schema Report"
    if summary.label:
        header += f" [{summary.label}]"
    lines.append(header)
    lines.append("=" * len(header))
    lines.append(f"Total changes : {summary.total_changes}")
    lines.append(f"Added tables  : {len(summary.added_tables)}")
    lines.append(f"Removed tables: {len(summary.removed_tables)}")
    lines.append(f"Modified tables: {len(summary.modified_tables)}")

    if summary.added_tables:
        lines.append("\nAdded:")
        for t in summary.added_tables:
            lines.append(f"  + {t}")

    if summary.removed_tables:
        lines.append("\nRemoved:")
        for t in summary.removed_tables:
            lines.append(f"  - {t}")

    if summary.modified_tables:
        lines.append("\nModified:")
        for t in summary.modified_tables:
            lines.append(f"  ~ {t}")

    return "\n".join(lines)
