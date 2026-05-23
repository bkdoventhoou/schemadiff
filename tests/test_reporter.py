"""Tests for schemadiff.reporter."""

import pytest
from schemadiff.schema import Column, Table, Schema
from schemadiff.differ import diff_schemas
from schemadiff.reporter import build_report, format_report, ReportSummary


def make_col(name: str, col_type: str = "VARCHAR") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def make_schema(*tables) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def make_table(name: str, cols=None) -> Table:
    cols = cols or [make_col("id", "INT")]
    return Table(name=name, columns={c.name: c for c in cols}, indexes={})


def test_build_report_no_changes():
    schema = make_schema(make_table("users"))
    diff = diff_schemas(schema, schema)
    report = build_report(diff)
    assert report.total_changes == 0
    assert report.added_tables == []
    assert report.removed_tables == []
    assert report.modified_tables == []


def test_build_report_added_table():
    s1 = make_schema(make_table("users"))
    s2 = make_schema(make_table("users"), make_table("orders"))
    diff = diff_schemas(s1, s2)
    report = build_report(diff, label="v1->v2")
    assert "orders" in report.added_tables
    assert report.label == "v1->v2"
    assert report.total_changes >= 1


def test_build_report_removed_table():
    s1 = make_schema(make_table("users"), make_table("orders"))
    s2 = make_schema(make_table("users"))
    diff = diff_schemas(s1, s2)
    report = build_report(diff)
    assert "orders" in report.removed_tables


def test_build_report_modified_table():
    t1 = make_table("users", [make_col("id", "INT")])
    t2 = make_table("users", [make_col("id", "INT"), make_col("email", "VARCHAR")])
    s1 = make_schema(t1)
    s2 = make_schema(t2)
    diff = diff_schemas(s1, s2)
    report = build_report(diff)
    assert "users" in report.modified_tables
    assert report.modified_tables.count("users") == 1


def test_report_as_dict_has_expected_keys():
    summary = ReportSummary(
        total_changes=2,
        added_tables=["orders"],
        removed_tables=[],
        modified_tables=["users"],
        label="test",
    )
    d = summary.as_dict()
    assert set(d.keys()) == {"label", "total_changes", "added_tables", "removed_tables", "modified_tables"}
    assert d["label"] == "test"
    assert d["total_changes"] == 2


def test_format_report_contains_table_names():
    s1 = make_schema(make_table("users"))
    s2 = make_schema(make_table("users"), make_table("orders"))
    diff = diff_schemas(s1, s2)
    report = build_report(diff, label="release-1")
    text = format_report(report)
    assert "orders" in text
    assert "release-1" in text
    assert "+" in text


def test_format_report_no_changes_shows_zero():
    schema = make_schema(make_table("users"))
    diff = diff_schemas(schema, schema)
    report = build_report(diff)
    text = format_report(report)
    assert "0" in text
