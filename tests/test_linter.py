"""Tests for schemadiff.linter."""

import pytest
from schemadiff.schema import Column, Index, Table, Schema
from schemadiff.linter import lint_schema, LintResult


def col(name: str, col_type: str = "VARCHAR(255)", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, default=None)


def make_index(columns, primary=False):
    return Index(columns=columns, unique=primary, primary=primary)


def make_table(name, columns, indexes=None):
    return Table(name=name, columns=columns, indexes=indexes or [])


def make_schema(*tables):
    return Schema(tables=list(tables))


def test_valid_schema_passes_lint():
    table = make_table("users", [col("id"), col("email")], [make_index(["id"], primary=True)])
    result = lint_schema(make_schema(table))
    assert bool(result) is True
    assert result.issues == []


def test_uppercase_table_name_warns():
    table = make_table("Users", [col("id")], [make_index(["id"], primary=True)])
    result = lint_schema(make_schema(table))
    warnings = [i for i in result.warnings if "Table name should be lowercase" in i.message]
    assert len(warnings) == 1


def test_table_name_with_spaces_errors():
    table = make_table("user accounts", [col("id")], [make_index(["id"], primary=True)])
    result = lint_schema(make_schema(table))
    errors = [i for i in result.errors if "spaces" in i.message]
    assert len(errors) == 1


def test_missing_primary_key_warns():
    table = make_table("orders", [col("id"), col("total")], [])
    result = lint_schema(make_schema(table))
    warnings = [i for i in result.warnings if "primary key" in i.message]
    assert len(warnings) == 1


def test_uppercase_column_name_warns():
    table = make_table("items", [col("ID"), col("name")], [make_index(["ID"], primary=True)])
    result = lint_schema(make_schema(table))
    warnings = [i for i in result.warnings if "Column name should be lowercase" in i.message]
    assert len(warnings) == 1


def test_column_name_with_spaces_errors():
    table = make_table("items", [col("item name")], [make_index(["item name"], primary=True)])
    result = lint_schema(make_schema(table))
    errors = [i for i in result.errors if "spaces" in i.message and "Column" in i.message]
    assert len(errors) == 1


def test_duplicate_column_names_errors():
    table = make_table("dupes", [col("id"), col("id")], [make_index(["id"], primary=True)])
    result = lint_schema(make_schema(table))
    errors = [i for i in result.errors if "Duplicate" in i.message]
    assert len(errors) == 1


def test_lint_result_bool_false_when_issues():
    table = make_table("Orders", [col("id")], [])
    result = lint_schema(make_schema(table))
    assert bool(result) is False


def test_lint_issue_str_format():
    table = make_table("Users", [col("id")], [make_index(["id"], primary=True)])
    result = lint_schema(make_schema(table))
    issue_strs = [str(i) for i in result.issues]
    assert any("[WARNING]" in s and "Users" in s for s in issue_strs)


def test_empty_schema_passes_lint():
    result = lint_schema(make_schema())
    assert bool(result) is True
