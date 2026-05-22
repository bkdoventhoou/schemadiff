"""Serialization and deserialization of schema objects to/from dict/JSON."""

import json
from typing import Any

from schemadiff.schema import Column, Index, Table, Schema


def column_to_dict(col: Column) -> dict[str, Any]:
    return {
        "name": col.name,
        "col_type": col.col_type,
        "nullable": col.nullable,
        "default": col.default,
    }


def index_to_dict(idx: Index) -> dict[str, Any]:
    return {
        "name": idx.name,
        "columns": list(idx.columns),
        "unique": idx.unique,
    }


def table_to_dict(table: Table) -> dict[str, Any]:
    return {
        "name": table.name,
        "columns": [column_to_dict(c) for c in table.columns],
        "indexes": [index_to_dict(i) for i in table.indexes],
    }


def schema_to_dict(schema: Schema) -> dict[str, Any]:
    return {
        "tables": [table_to_dict(t) for t in schema.tables.values()],
    }


def column_from_dict(data: dict[str, Any]) -> Column:
    return Column(
        name=data["name"],
        col_type=data["col_type"],
        nullable=data.get("nullable", True),
        default=data.get("default"),
    )


def index_from_dict(data: dict[str, Any]) -> Index:
    return Index(
        name=data["name"],
        columns=data["columns"],
        unique=data.get("unique", False),
    )


def table_from_dict(data: dict[str, Any]) -> Table:
    return Table(
        name=data["name"],
        columns=[column_from_dict(c) for c in data.get("columns", [])],
        indexes=[index_from_dict(i) for i in data.get("indexes", [])],
    )


def schema_from_dict(data: dict[str, Any]) -> Schema:
    tables = [table_from_dict(t) for t in data.get("tables", [])]
    return Schema(tables=tables)


def schema_to_json(schema: Schema, indent: int = 2) -> str:
    return json.dumps(schema_to_dict(schema), indent=indent)


def schema_from_json(raw: str) -> Schema:
    data = json.loads(raw)
    return schema_from_dict(data)
