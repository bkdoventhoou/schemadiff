"""Tests for schemadiff.migrator."""

import pytest
from schemadiff.schema import Column, Table, Schema
from schemadiff.differ import diff_schemas
from schemadiff.migrator import generate_migration, migration_to_sql, MigrationStatement


def make_col(name, col_type="VARCHAR(255)", nullable=True, default=None):
    return Column(name=name, col_type=col_type, nullable=nullable, default=default)


def make_table(name, cols):
    return Table(name=name, columns={c.name: c for c in cols}, indexes={})


def make_schema(tables):
    return Schema(tables={t.name: t for t in tables})


def test_no_changes_produces_no_statements():
    s = make_schema([make_table("users", [make_col("id", "INT")])])
    diff = diff_schemas(s, s)
    stmts = generate_migration(diff)
    assert stmts == []


def test_no_changes_sql_is_comment():
    s = make_schema([])
    diff = diff_schemas(s, s)
    sql = migration_to_sql(diff)
    assert sql.startswith("-- No changes")


def test_added_table_generates_create():
    old = make_schema([])
    new = make_schema([make_table("orders", [make_col("id", "INT", nullable=False)])])
    diff = diff_schemas(old, new)
    stmts = generate_migration(diff)
    assert len(stmts) == 1
    assert "CREATE TABLE orders" in stmts[0].sql
    assert "id INT NOT NULL" in stmts[0].sql


def test_removed_table_generates_drop():
    old = make_schema([make_table("orders", [make_col("id", "INT")])])
    new = make_schema([])
    diff = diff_schemas(old, new)
    stmts = generate_migration(diff)
    assert len(stmts) == 1
    assert stmts[0].sql == "DROP TABLE orders;"


def test_added_column_generates_alter_add():
    old = make_schema([make_table("users", [make_col("id", "INT")])])
    new = make_schema([make_table("users", [make_col("id", "INT"), make_col("email", "TEXT")])])
    diff = diff_schemas(old, new)
    stmts = generate_migration(diff)
    assert any("ADD COLUMN email" in s.sql for s in stmts)


def test_removed_column_generates_alter_drop():
    old = make_schema([make_table("users", [make_col("id", "INT"), make_col("email", "TEXT")])])
    new = make_schema([make_table("users", [make_col("id", "INT")])])
    diff = diff_schemas(old, new)
    stmts = generate_migration(diff)
    assert any("DROP COLUMN email" in s.sql for s in stmts)


def test_migration_statement_str():
    stmt = MigrationStatement(sql="DROP TABLE x;", description="Drop x")
    assert str(stmt) == "DROP TABLE x;"


def test_migration_to_sql_includes_comments():
    old = make_schema([])
    new = make_schema([make_table("logs", [make_col("id", "INT")])])
    diff = diff_schemas(old, new)
    sql = migration_to_sql(diff)
    assert "-- Create table logs" in sql
    assert "CREATE TABLE logs" in sql
