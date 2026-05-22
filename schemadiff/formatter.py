"""Human-readable formatting for schema diffs."""

from typing import IO
import sys

from schemadiff.differ import SchemaDiff, ChangeType


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_diff(
    diff: SchemaDiff,
    output: IO[str] = sys.stdout,
    use_color: bool = True,
    verbose: bool = False,
) -> None:
    """Write a human-readable representation of *diff* to *output*."""
    if not diff.has_changes:
        output.write("No schema differences detected.\n")
        return

    output.write(
        _colorize(f"Schema diff ({len(diff.changes)} change(s)):\n", ANSI_BOLD, use_color)
    )

    for change in diff.changes:
        if change.change_type == ChangeType.TABLE_ADDED:
            prefix = _colorize("+", ANSI_GREEN, use_color)
            line = f"{prefix} Table added:   {change.table_name}"
        elif change.change_type == ChangeType.TABLE_REMOVED:
            prefix = _colorize("-", ANSI_RED, use_color)
            line = f"{prefix} Table removed: {change.table_name}"
        elif change.change_type == ChangeType.COLUMN_ADDED:
            prefix = _colorize("+", ANSI_GREEN, use_color)
            line = f"{prefix} Column added:  {change.table_name}.{change.object_name}"
        elif change.change_type == ChangeType.COLUMN_REMOVED:
            prefix = _colorize("-", ANSI_RED, use_color)
            line = f"{prefix} Column removed:{change.table_name}.{change.object_name}"
        elif change.change_type == ChangeType.COLUMN_MODIFIED:
            prefix = _colorize("~", ANSI_YELLOW, use_color)
            line = f"{prefix} Column changed:{change.table_name}.{change.object_name}"
        else:
            prefix = _colorize("~", ANSI_YELLOW, use_color)
            line = f"{prefix} {change.change_type.value}: {change.table_name}"

        output.write(line + "\n")

        if verbose and change.detail:
            for detail_line in change.detail.splitlines():
                output.write(f"    {detail_line}\n")


def format_diff_as_string(
    diff: SchemaDiff,
    use_color: bool = False,
    verbose: bool = False,
) -> str:
    """Return the formatted diff as a plain string."""
    import io
    buf = io.StringIO()
    format_diff(diff, output=buf, use_color=use_color, verbose=verbose)
    return buf.getvalue()
