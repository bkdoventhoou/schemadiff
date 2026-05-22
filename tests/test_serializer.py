"""Tests for schemadiff.serializer module."""

import json
import pytest

from schemadiff.schema import Column, Index, Table, Schema
from schemadiff.serializer import (
    schema_to_dict,
    schema_from_dict,
    schema_to_json,
    schema_from_json,
    column_to_dict,
    index_to_dict,
    table_to_dict,
)


def make_schema() -> Schema:
    columns = [
        Column(name="id", col_type="INTEGER", nullable=False, default=None),
        Column(name="email", col_type="VARCHAR(255)", nullable=False, default=None),
        Column(name="created_at", col_type="TIMESTAMP", nullable=True, default="NOW()"),
    ]
    indexes = [
        Index(name="idx_email", columns=["email"], unique=True),
    ]
    table = Table(name="users", columns=columns, indexes=indexes)
    return Schema(tables=[table])


def test_column_to_dict():
    col = Column(name="id", col_type="INTEGER", nullable=False, default=None)
    result = column_to_dict(col)
    assert result == {"name": "id", "col_type": "INTEGER", "nullable": False, "default": None}


def test_index_to_dict():
    idx = Index(name="idx_email", columns=["email"], unique=True)
    result = index_to_dict(idx)
    assert result == {"name": "idx_email", "columns": ["email"], "unique": True}


def test_table_to_dict_has_expected_keys():
    schema = make_schema()
    table = list(schema.tables.values())[0]
    result = table_to_dict(table)
    assert result["name"] == "users"
    assert len(result["columns"]) == 3
    assert len(result["indexes"]) == 1


def test_schema_to_dict_roundtrip():
    schema = make_schema()
    data = schema_to_dict(schema)
    restored = schema_from_dict(data)
    assert set(restored.tables.keys()) == set(schema.tables.keys())


def test_schema_to_json_is_valid_json():
    schema = make_schema()
    raw = schema_to_json(schema)
    parsed = json.loads(raw)
    assert "tables" in parsed
    assert parsed["tables"][0]["name"] == "users"


def test_schema_from_json_restores_columns():
    schema = make_schema()
    raw = schema_to_json(schema)
    restored = schema_from_json(raw)
    users = restored.tables["users"]
    col_names = [c.name for c in users.columns]
    assert "id" in col_names
    assert "email" in col_names
    assert "created_at" in col_names


def test_schema_from_json_restores_indexes():
    schema = make_schema()
    raw = schema_to_json(schema)
    restored = schema_from_json(raw)
    users = restored.tables["users"]
    assert len(users.indexes) == 1
    assert users.indexes[0].name == "idx_email"
    assert users.indexes[0].unique is True


def test_schema_from_json_column_defaults():
    schema = make_schema()
    raw = schema_to_json(schema)
    restored = schema_from_json(raw)
    users = restored.tables["users"]
    created_at = next(c for c in users.columns if c.name == "created_at")
    assert created_at.default == "NOW()"
    assert created_at.nullable is True
