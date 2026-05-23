"""Validates schema objects for consistency and correctness."""

from dataclasses import dataclass, field
from typing import List
from schemadiff.schema import Schema, Table, Column


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)

    def __bool__(self):
        return self.valid


def _validate_column(col: Column, table_name: str) -> List[str]:
    errors = []
    if not col.name or not col.name.strip():
        errors.append(f"Table '{table_name}': column has empty name")
    if not col.col_type or not col.col_type.strip():
        errors.append(f"Table '{table_name}': column '{col.name}' has empty type")
    return errors


def _validate_table(table: Table) -> List[str]:
    errors = []
    if not table.name or not table.name.strip():
        errors.append("Schema contains a table with an empty name")
        return errors

    if not table.columns:
        errors.append(f"Table '{table.name}' has no columns")

    seen_columns = set()
    for col in table.columns:
        col_errors = _validate_column(col, table.name)
        errors.extend(col_errors)
        if col.name in seen_columns:
            errors.append(f"Table '{table.name}': duplicate column name '{col.name}'")
        seen_columns.add(col.name)

    seen_indexes = set()
    for idx in table.indexes:
        if not idx.name or not idx.name.strip():
            errors.append(f"Table '{table.name}': index has empty name")
            continue
        if idx.name in seen_indexes:
            errors.append(f"Table '{table.name}': duplicate index name '{idx.name}'")
        seen_indexes.add(idx.name)
        for col_name in idx.columns:
            if col_name not in seen_columns:
                errors.append(
                    f"Table '{table.name}': index '{idx.name}' references "
                    f"unknown column '{col_name}'"
                )

    return errors


def validate_schema(schema: Schema) -> ValidationResult:
    """Validate a Schema object and return a ValidationResult."""
    errors = []

    seen_tables = set()
    for table in schema.tables:
        if table.name in seen_tables:
            errors.append(f"Duplicate table name '{table.name}' in schema")
        seen_tables.add(table.name)
        errors.extend(_validate_table(table))

    return ValidationResult(valid=len(errors) == 0, errors=errors)
