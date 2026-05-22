"""Tests for schemadiff.exporter — JSON and Markdown export of diffs."""

import json

import pytest

from schemadiff.schema import Column, Table, Schema
from schemadiff.differ import diff_schemas
from schemadiff.exporter import diff_to_dict, export_as_json, export_as_markdown


def make_col(name: str, col_type: str = "VARCHAR", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=None)


def make_schema(tables: dict) -> Schema:
    return Schema(tables=tables)


def test_diff_to_dict_no_changes():
    schema = make_schema({"users": Table(name="users", columns={"id": make_col("id", "INT")}, indexes={})})
    diff = diff_schemas(schema, schema)
    result = diff_to_dict(diff)
    assert result["added_tables"] == []
    assert result["removed_tables"] == []
    assert result["modified_tables"] == {}


def test_diff_to_dict_added_table():
    old = make_schema({})
    new = make_schema({"orders": Table(name="orders", columns={"id": make_col("id", "INT")}, indexes={})})
    diff = diff_schemas(old, new)
    result = diff_to_dict(diff)
    assert "orders" in result["added_tables"]
    assert result["removed_tables"] == []


def test_diff_to_dict_removed_table():
    old = make_schema({"orders": Table(name="orders", columns={"id": make_col("id", "INT")}, indexes={})})
    new = make_schema({})
    diff = diff_schemas(old, new)
    result = diff_to_dict(diff)
    assert "orders" in result["removed_tables"]


def test_diff_to_dict_modified_columns():
    old_table = Table(name="users", columns={"id": make_col("id", "INT"), "name": make_col("name")}, indexes={})
    new_table = Table(name="users", columns={"id": make_col("id", "INT"), "email": make_col("email")}, indexes={})
    old = make_schema({"users": old_table})
    new = make_schema({"users": new_table})
    diff = diff_schemas(old, new)
    result = diff_to_dict(diff)
    assert "users" in result["modified_tables"]
    assert "name" in result["modified_tables"]["users"]["removed_columns"]
    assert "email" in result["modified_tables"]["users"]["added_columns"]


def test_export_as_json_is_valid_json():
    old = make_schema({})
    new = make_schema({"logs": Table(name="logs", columns={"id": make_col("id", "INT")}, indexes={})})
    diff = diff_schemas(old, new)
    output = export_as_json(diff)
    parsed = json.loads(output)
    assert "added_tables" in parsed
    assert "logs" in parsed["added_tables"]


def test_export_as_markdown_no_changes():
    schema = make_schema({"users": Table(name="users", columns={"id": make_col("id", "INT")}, indexes={})})
    diff = diff_schemas(schema, schema)
    md = export_as_markdown(diff)
    assert "No changes detected" in md


def test_export_as_markdown_added_table():
    old = make_schema({})
    new = make_schema({"events": Table(name="events", columns={"id": make_col("id", "INT")}, indexes={})})
    diff = diff_schemas(old, new)
    md = export_as_markdown(diff)
    assert "## Added Tables" in md
    assert "`events`" in md


def test_export_as_markdown_modified_table():
    old_table = Table(name="users", columns={"id": make_col("id", "INT"), "age": make_col("age", "INT")}, indexes={})
    new_table = Table(name="users", columns={"id": make_col("id", "INT"), "score": make_col("score", "FLOAT")}, indexes={})
    old = make_schema({"users": old_table})
    new = make_schema({"users": new_table})
    diff = diff_schemas(old, new)
    md = export_as_markdown(diff)
    assert "## Modified Tables" in md
    assert "`users`" in md
    assert "`age`" in md
    assert "`score`" in md
