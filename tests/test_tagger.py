"""Tests for the tagger module."""

import pytest
from schemadiff.schema import Schema, Table, Column
from schemadiff.history import SchemaHistory
from schemadiff.tagger import SchemaTagger, TagEntry


def make_schema(table_names=None):
    tables = {}
    for name in (table_names or []):
        tables[name] = Table(name=name, columns={"id": Column("id", "int", False, None)}, indexes={})
    return Schema(tables=tables)


def make_tagger_with_snapshots(n=2):
    history = SchemaHistory()
    for i in range(n):
        history.add_snapshot(make_schema([f"table_{i}"]), label=f"snap_{i}")
    return SchemaTagger(history=history), history


def test_add_tag_assigns_latest_version_by_default():
    tagger, history = make_tagger_with_snapshots(2)
    entry = tagger.add_tag("release-1")
    assert entry.version == history.latest_version()


def test_add_tag_with_explicit_version():
    tagger, _ = make_tagger_with_snapshots(3)
    entry = tagger.add_tag("old-release", version=1)
    assert entry.version == 1


def test_add_tag_with_description():
    tagger, _ = make_tagger_with_snapshots(1)
    entry = tagger.add_tag("v1.0", description="Initial release")
    assert entry.description == "Initial release"


def test_add_duplicate_tag_raises():
    tagger, _ = make_tagger_with_snapshots(1)
    tagger.add_tag("v1")
    with pytest.raises(ValueError, match="already exists"):
        tagger.add_tag("v1")


def test_add_tag_empty_name_raises():
    tagger, _ = make_tagger_with_snapshots(1)
    with pytest.raises(ValueError, match="must not be empty"):
        tagger.add_tag("")


def test_add_tag_invalid_version_raises():
    tagger, _ = make_tagger_with_snapshots(1)
    with pytest.raises(ValueError, match="does not exist"):
        tagger.add_tag("bad", version=999)


def test_add_tag_no_snapshots_raises():
    history = SchemaHistory()
    tagger = SchemaTagger(history=history)
    with pytest.raises(ValueError, match="No snapshots"):
        tagger.add_tag("empty")


def test_get_tag_returns_entry():
    tagger, _ = make_tagger_with_snapshots(1)
    tagger.add_tag("v1")
    entry = tagger.get_tag("v1")
    assert entry is not None
    assert entry.tag == "v1"


def test_get_tag_missing_returns_none():
    tagger, _ = make_tagger_with_snapshots(1)
    assert tagger.get_tag("nonexistent") is None


def test_remove_tag_returns_true():
    tagger, _ = make_tagger_with_snapshots(1)
    tagger.add_tag("v1")
    assert tagger.remove_tag("v1") is True
    assert tagger.get_tag("v1") is None


def test_remove_missing_tag_returns_false():
    tagger, _ = make_tagger_with_snapshots(1)
    assert tagger.remove_tag("ghost") is False


def test_list_tags_sorted_by_version():
    tagger, _ = make_tagger_with_snapshots(3)
    tagger.add_tag("v3", version=3)
    tagger.add_tag("v1", version=1)
    tagger.add_tag("v2", version=2)
    tags = tagger.list_tags()
    assert [t.tag for t in tags] == ["v1", "v2", "v3"]


def test_resolve_snapshot_returns_correct_entry():
    tagger, history = make_tagger_with_snapshots(2)
    tagger.add_tag("first", version=1)
    snap = tagger.resolve_snapshot("first")
    assert snap is not None
    assert snap.version == 1


def test_tags_roundtrip_serialization():
    tagger, history = make_tagger_with_snapshots(2)
    tagger.add_tag("v1", version=1, description="first")
    tagger.add_tag("v2", version=2, description="second")
    data = tagger.tags_as_dict()
    restored = SchemaTagger.tags_from_dict(history, data)
    assert restored.get_tag("v1").version == 1
    assert restored.get_tag("v2").description == "second"
