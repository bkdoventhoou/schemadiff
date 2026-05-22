"""Tests for the schema diffing engine."""

import pytest

from schemadiff.schema import Column, Index, Schema, Table
from schemadiff.differ import ChangeType, diff_schemas


def make_schema(name: str, tables: list) -> Schema:
    schema = Schema(name=name)
    for table in tables:
        schema.add_table(table)
    return schema


def test_no_changes_returns_empty_diff():
    table = Table(name="users")
    table.add_column(Column(name="id", data_type="integer", primary_key=True))
    source = make_schema("db", [table])
    target = make_schema("db", [table])
    result = diff_schemas(source, target)
    assert not result.has_changes


def test_added_table_detected():
    source = make_schema("db", [])
    new_table = Table(name="orders")
    target = make_schema("db", [new_table])
    result = diff_schemas(source, target)
    assert "orders" in result.added_tables
    assert not result.removed_tables


def test_removed_table_detected():
    old_table = Table(name="legacy")
    source = make_schema("db", [old_table])
    target = make_schema("db", [])
    result = diff_schemas(source, target)
    assert "legacy" in result.removed_tables
    assert not result.added_tables


def test_added_column_detected():
    t1 = Table(name="users")
    t1.add_column(Column(name="id", data_type="integer"))

    t2 = Table(name="users")
    t2.add_column(Column(name="id", data_type="integer"))
    t2.add_column(Column(name="email", data_type="varchar"))

    result = diff_schemas(make_schema("db", [t1]), make_schema("db", [t2]))
    assert result.has_changes
    col_changes = result.modified_tables[0]["columns"]
    added = [c for c in col_changes if c["change"] == ChangeType.ADDED]
    assert any(c["column"] == "email" for c in added)


def test_modified_column_detected():
    t1 = Table(name="products")
    t1.add_column(Column(name="price", data_type="integer"))

    t2 = Table(name="products")
    t2.add_column(Column(name="price", data_type="numeric"))

    result = diff_schemas(make_schema("db", [t1]), make_schema("db", [t2]))
    col_changes = result.modified_tables[0]["columns"]
    modified = [c for c in col_changes if c["change"] == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0]["column"] == "price"


def test_added_index_detected():
    t1 = Table(name="users")
    t2 = Table(name="users")
    t2.add_index(Index(name="idx_email", columns=["email"], unique=True))

    result = diff_schemas(make_schema("db", [t1]), make_schema("db", [t2]))
    idx_changes = result.modified_tables[0]["indexes"]
    assert any(c["change"] == ChangeType.ADDED and c["index"] == "idx_email" for c in idx_changes)


def test_schema_from_dict():
    data = {
        "name": "mydb",
        "tables": [
            {
                "name": "users",
                "columns": [{"name": "id", "data_type": "integer", "primary_key": True}],
                "indexes": [],
            }
        ],
    }
    schema = Schema.from_dict(data)
    assert "users" in schema.tables
    assert "id" in schema.tables["users"].columns
