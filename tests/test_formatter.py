"""Tests for schemadiff.formatter."""

import pytest

from schemadiff.schema import Column, Table, Schema
from schemadiff.differ import diff_schemas
from schemadiff.formatter import format_diff_as_string


def make_col(name: str, col_type: str = "VARCHAR(255)", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=None)


def make_schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def make_table(name: str, columns: list[Column] | None = None) -> Table:
    cols = columns or [make_col("id", "INT", False)]
    return Table(name=name, columns={c.name: c for c in cols}, indexes={})


def test_no_changes_message():
    schema = make_schema(make_table("users"))
    diff = diff_schemas(schema, schema)
    result = format_diff_as_string(diff)
    assert "No schema differences" in result


def test_table_added_message():
    old = make_schema()
    new = make_schema(make_table("orders"))
    diff = diff_schemas(old, new)
    result = format_diff_as_string(diff)
    assert "Table added" in result
    assert "orders" in result


def test_table_removed_message():
    old = make_schema(make_table("orders"))
    new = make_schema()
    diff = diff_schemas(old, new)
    result = format_diff_as_string(diff)
    assert "Table removed" in result
    assert "orders" in result


def test_column_added_message():
    old = make_schema(make_table("users", [make_col("id", "INT")]))
    new = make_schema(make_table("users", [make_col("id", "INT"), make_col("email")]))
    diff = diff_schemas(old, new)
    result = format_diff_as_string(diff)
    assert "Column added" in result
    assert "users.email" in result


def test_column_removed_message():
    old = make_schema(make_table("users", [make_col("id", "INT"), make_col("email")]))
    new = make_schema(make_table("users", [make_col("id", "INT")]))
    diff = diff_schemas(old, new)
    result = format_diff_as_string(diff)
    assert "Column removed" in result
    assert "users.email" in result


def test_change_count_in_header():
    old = make_schema()
    new = make_schema(make_table("a"), make_table("b"))
    diff = diff_schemas(old, new)
    result = format_diff_as_string(diff)
    assert "2 change(s)" in result


def test_no_ansi_codes_when_color_disabled():
    old = make_schema()
    new = make_schema(make_table("users"))
    diff = diff_schemas(old, new)
    result = format_diff_as_string(diff, use_color=False)
    assert "\033[" not in result
