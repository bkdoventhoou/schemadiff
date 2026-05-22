"""Tests for snapshot CLI subcommands."""

import json
import argparse
from unittest.mock import patch, MagicMock

import pytest

from schemadiff.history import SchemaHistory, save_history
from schemadiff.schema import Column, Schema, Table
from schemadiff.snapshot_cmd import cmd_snapshot, cmd_history, cmd_diff_versions


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


def make_args(**kwargs):
    defaults = {"history_file": None, "label": "", "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_snapshot_saves_entry(tmp_path):
    from schemadiff.serializer import schema_to_dict
    schema = make_schema()
    schema_file = str(tmp_path / "schema.json")
    history_file = str(tmp_path / "history.json")
    with open(schema_file, "w") as f:
        json.dump(schema_to_dict(schema), f)

    args = make_args(schema_file=schema_file, history_file=history_file, label="test-snap")
    result = cmd_snapshot(args)
    assert result == 0

    from schemadiff.history import load_history
    history = load_history(history_file)
    assert len(history.entries) == 1
    assert history.entries[0].label == "test-snap"


def test_cmd_snapshot_invalid_file(tmp_path):
    args = make_args(schema_file=str(tmp_path / "missing.json"), history_file=None)
    result = cmd_snapshot(args)
    assert result == 1


def test_cmd_history_empty(tmp_path, capsys):
    args = make_args(history_file=str(tmp_path / "history.json"))
    result = cmd_history(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "No snapshots" in captured.out


def test_cmd_history_lists_entries(tmp_path, capsys):
    history = SchemaHistory()
    schema = make_schema()
    history.add_snapshot(schema, label="release-1")
    history_file = str(tmp_path / "history.json")
    save_history(history, history_file)

    args = make_args(history_file=history_file)
    result = cmd_history(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "release-1" in captured.out


def test_cmd_diff_versions_success(tmp_path, capsys):
    history = SchemaHistory()
    schema_a = make_schema(["users"])
    schema_b = make_schema(["users", "orders"])
    history.add_snapshot(schema_a, label="v1")
    history.add_snapshot(schema_b, label="v2")
    history_file = str(tmp_path / "history.json")
    save_history(history, history_file)

    args = make_args(history_file=history_file, from_version=1, to_version=2)
    result = cmd_diff_versions(args)
    assert result == 0


def test_cmd_diff_versions_missing_version(tmp_path):
    history = SchemaHistory()
    history_file = str(tmp_path / "history.json")
    save_history(history, history_file)

    args = make_args(history_file=history_file, from_version=1, to_version=2)
    result = cmd_diff_versions(args)
    assert result == 1
