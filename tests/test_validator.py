"""Tests for schemadiff.validator."""

import pytest
from schemadiff.schema import Schema, Table, Column, Index
from schemadiff.validator import validate_schema, ValidationResult


def col(name="id", col_type="INT", nullable=False):
    return Column(name=name, col_type=col_type, nullable=nullable)


def make_table(name="users", columns=None, indexes=None):
    return Table(
        name=name,
        columns=columns or [col()],
        indexes=indexes or [],
    )


def make_schema(*tables):
    return Schema(tables=list(tables))


def test_valid_schema_returns_no_errors():
    schema = make_schema(make_table("users", [col("id"), col("email", "VARCHAR")]))
    result = validate_schema(schema)
    assert result.valid is True
    assert result.errors == []


def test_empty_schema_is_valid():
    result = validate_schema(make_schema())
    assert result.valid is True


def test_table_with_no_columns_is_invalid():
    table = Table(name="empty_table", columns=[], indexes=[])
    result = validate_schema(make_schema(table))
    assert not result.valid
    assert any("no columns" in e for e in result.errors)


def test_column_with_empty_name_is_invalid():
    table = make_table(columns=[col(name="", col_type="INT")])
    result = validate_schema(make_schema(table))
    assert not result.valid
    assert any("empty name" in e for e in result.errors)


def test_column_with_empty_type_is_invalid():
    table = make_table(columns=[col(name="id", col_type="")])
    result = validate_schema(make_schema(table))
    assert not result.valid
    assert any("empty type" in e for e in result.errors)


def test_duplicate_column_names_are_invalid():
    table = make_table(columns=[col("id"), col("id")])
    result = validate_schema(make_schema(table))
    assert not result.valid
    assert any("duplicate column" in e.lower() for e in result.errors)


def test_duplicate_table_names_are_invalid():
    result = validate_schema(make_schema(make_table("users"), make_table("users")))
    assert not result.valid
    assert any("Duplicate table" in e for e in result.errors)


def test_index_referencing_unknown_column_is_invalid():
    idx = Index(name="idx_missing", columns=["nonexistent"], unique=False)
    table = make_table(columns=[col("id")], indexes=[idx])
    result = validate_schema(make_schema(table))
    assert not result.valid
    assert any("unknown column" in e for e in result.errors)


def test_valid_index_referencing_existing_column():
    idx = Index(name="idx_id", columns=["id"], unique=True)
    table = make_table(columns=[col("id")], indexes=[idx])
    result = validate_schema(make_schema(table))
    assert result.valid


def test_validation_result_bool_true():
    assert bool(ValidationResult(valid=True)) is True


def test_validation_result_bool_false():
    assert bool(ValidationResult(valid=False, errors=["oops"])) is False
