"""Tests for schemadiff.watcher."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from schemadiff.schema import Schema, Table, Column
from schemadiff.serializer import schema_to_dict
from schemadiff.watcher import watch_schema_file


def make_col(name: str, col_type: str = "VARCHAR") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def make_schema(*table_names: str) -> Schema:
    tables = {
        name: Table(name=name, columns={"id": make_col("id", "INT")}, indexes={})
        for name in table_names
    }
    return Schema(tables=tables)


def write_schema(path: str, schema: Schema) -> None:
    with open(path, "w") as f:
        json.dump(schema_to_dict(schema), f)


def test_watch_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        watch_schema_file("/nonexistent/path/schema.json", max_iterations=1)


def test_watch_no_change_emits_nothing():
    schema = make_schema("users")
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(schema_to_dict(schema), f)
        tmp_path = f.name

    try:
        collected = []
        with patch("schemadiff.watcher.time.sleep"):
            watch_schema_file(
                tmp_path,
                on_change=collected.append,
                poll_interval=0,
                max_iterations=3,
            )
        assert collected == []
    finally:
        os.unlink(tmp_path)


def test_watch_detects_added_table():
    schema_v1 = make_schema("users")
    schema_v2 = make_schema("users", "orders")

    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(schema_to_dict(schema_v1), f)
        tmp_path = f.name

    collected = []
    call_count = 0

    def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            write_schema(tmp_path, schema_v2)
            mtime = os.path.getmtime(tmp_path) + 1
            os.utime(tmp_path, (mtime, mtime))

    try:
        with patch("schemadiff.watcher.time.sleep", side_effect=fake_sleep):
            watch_schema_file(
                tmp_path,
                on_change=collected.append,
                poll_interval=0,
                max_iterations=2,
            )
        assert len(collected) == 1
        assert "orders" in collected[0]
    finally:
        os.unlink(tmp_path)


def test_watch_handles_corrupt_file_gracefully():
    schema = make_schema("users")
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(schema_to_dict(schema), f)
        tmp_path = f.name

    call_count = 0

    def fake_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            with open(tmp_path, "w") as fh:
                fh.write("not valid json{{")
            mtime = os.path.getmtime(tmp_path) + 1
            os.utime(tmp_path, (mtime, mtime))

    collected = []
    try:
        with patch("schemadiff.watcher.time.sleep", side_effect=fake_sleep):
            watch_schema_file(
                tmp_path,
                on_change=collected.append,
                poll_interval=0,
                max_iterations=2,
            )
        assert collected == []
    finally:
        os.unlink(tmp_path)
