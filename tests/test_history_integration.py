"""Integration tests for history: snapshot -> diff across versions."""

import json
import pytest

from schemadiff.differ import diff_schemas
from schemadiff.history import SchemaHistory, save_history, load_history
from schemadiff.schema import Column, Index, Schema, Table


def col(name, col_type="VARCHAR(255)"):
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def make_table(name, col_names):
    return Table(
        name=name,
        columns={c: col(c) for c in col_names},
        indexes={},
        primary_key=[col_names[0]] if col_names else [],
    )


def make_schema(tables: dict) -> Schema:
    return Schema(tables={n: make_table(n, cols) for n, cols in tables.items()})


def test_history_records_multiple_snapshots():
    history = SchemaHistory()
    s1 = make_schema({"users": ["id", "name"]})
    s2 = make_schema({"users": ["id", "name", "email"]})
    s3 = make_schema({"users": ["id", "name", "email"], "orders": ["id", "user_id"]})

    history.add_snapshot(s1, "initial")
    history.add_snapshot(s2, "add-email")
    history.add_snapshot(s3, "add-orders")

    assert len(history.entries) == 3
    assert history.get_version(2).label == "add-email"


def test_diff_between_history_versions_detects_new_table():
    history = SchemaHistory()
    s1 = make_schema({"users": ["id"]})
    s2 = make_schema({"users": ["id"], "products": ["id", "name"]})
    history.add_snapshot(s1)
    history.add_snapshot(s2)

    schema_a = history.get_version(1).load_schema()
    schema_b = history.get_version(2).load_schema()
    diff = diff_schemas(schema_a, schema_b)

    assert "products" in diff.added_tables


def test_history_persisted_and_reloaded(tmp_path):
    path = str(tmp_path / "h.json")
    history = SchemaHistory()
    s1 = make_schema({"users": ["id", "name"]})
    s2 = make_schema({"users": ["id", "name"], "logs": ["id"]})
    history.add_snapshot(s1, "base")
    history.add_snapshot(s2, "with-logs")
    save_history(history, path)

    reloaded = load_history(path)
    assert len(reloaded.entries) == 2
    schema_b = reloaded.get_version(2).load_schema()
    assert "logs" in schema_b.tables


def test_diff_between_reloaded_versions_detects_removed_table(tmp_path):
    path = str(tmp_path / "h.json")
    history = SchemaHistory()
    s1 = make_schema({"users": ["id"], "temp": ["id"]})
    s2 = make_schema({"users": ["id"]})
    history.add_snapshot(s1, "with-temp")
    history.add_snapshot(s2, "without-temp")
    save_history(history, path)

    reloaded = load_history(path)
    a = reloaded.get_version(1).load_schema()
    b = reloaded.get_version(2).load_schema()
    diff = diff_schemas(a, b)
    assert "temp" in diff.removed_tables
