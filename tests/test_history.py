"""Tests for schema version history tracking."""

import json
import os
import tempfile

import pytest

from schemadiff.history import (
    SchemaHistory,
    SnapshotEntry,
    load_history,
    save_history,
)
from schemadiff.schema import Column, Schema, Table


def make_schema(table_names=None):
    tables = {}
    for name in (table_names or ["users"]):
        tables[name] = Table(
            name=name,
            columns={"id": Column(name="id", col_type="INT", nullable=False, default=None)},
            indexes={},
            primary_key=["id"],
        )
    return Schema(tables=tables)


def test_add_snapshot_increments_version():
    history = SchemaHistory()
    schema = make_schema()
    entry1 = history.add_snapshot(schema, label="initial")
    entry2 = history.add_snapshot(schema, label="second")
    assert entry1.version == 1
    assert entry2.version == 2


def test_add_snapshot_uses_label():
    history = SchemaHistory()
    schema = make_schema()
    entry = history.add_snapshot(schema, label="release-1.0")
    assert entry.label == "release-1.0"


def test_add_snapshot_auto_label():
    history = SchemaHistory()
    schema = make_schema()
    entry = history.add_snapshot(schema)
    assert entry.label == "v1"


def test_get_version_returns_correct_entry():
    history = SchemaHistory()
    schema = make_schema()
    history.add_snapshot(schema, label="first")
    history.add_snapshot(schema, label="second")
    entry = history.get_version(1)
    assert entry is not None
    assert entry.label == "first"


def test_get_version_missing_returns_none():
    history = SchemaHistory()
    assert history.get_version(99) is None


def test_latest_returns_last_entry():
    history = SchemaHistory()
    schema = make_schema()
    history.add_snapshot(schema, label="a")
    history.add_snapshot(schema, label="b")
    assert history.latest().label == "b"


def test_latest_empty_history_returns_none():
    history = SchemaHistory()
    assert history.latest() is None


def test_snapshot_load_schema_roundtrip():
    history = SchemaHistory()
    schema = make_schema(["orders", "users"])
    entry = history.add_snapshot(schema)
    loaded = entry.load_schema()
    assert set(loaded.tables.keys()) == {"orders", "users"}


def test_save_and_load_history(tmp_path):
    path = str(tmp_path / "history.json")
    history = SchemaHistory()
    schema = make_schema()
    history.add_snapshot(schema, label="v1")
    save_history(history, path)
    loaded = load_history(path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].label == "v1"


def test_load_history_missing_file(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    history = load_history(path)
    assert len(history.entries) == 0
