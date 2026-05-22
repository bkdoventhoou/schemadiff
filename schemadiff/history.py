"""Schema version history tracking and storage."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from schemadiff.serializer import schema_to_dict, schema_from_dict
from schemadiff.schema import Schema


@dataclass
class SnapshotEntry:
    version: int
    label: str
    timestamp: str
    schema_dict: dict

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "label": self.label,
            "timestamp": self.timestamp,
            "schema": self.schema_dict,
        }

    @staticmethod
    def from_dict(data: dict) -> "SnapshotEntry":
        return SnapshotEntry(
            version=data["version"],
            label=data["label"],
            timestamp=data["timestamp"],
            schema_dict=data["schema"],
        )

    def load_schema(self) -> Schema:
        return schema_from_dict(self.schema_dict)


@dataclass
class SchemaHistory:
    entries: List[SnapshotEntry] = field(default_factory=list)

    def add_snapshot(self, schema: Schema, label: str = "") -> SnapshotEntry:
        version = len(self.entries) + 1
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = SnapshotEntry(
            version=version,
            label=label or f"v{version}",
            timestamp=timestamp,
            schema_dict=schema_to_dict(schema),
        )
        self.entries.append(entry)
        return entry

    def get_version(self, version: int) -> Optional[SnapshotEntry]:
        for entry in self.entries:
            if entry.version == version:
                return entry
        return None

    def latest(self) -> Optional[SnapshotEntry]:
        return self.entries[-1] if self.entries else None

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    @staticmethod
    def from_dict(data: dict) -> "SchemaHistory":
        history = SchemaHistory()
        history.entries = [SnapshotEntry.from_dict(e) for e in data.get("entries", [])]
        return history


def save_history(history: SchemaHistory, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history.to_dict(), f, indent=2)


def load_history(path: str) -> SchemaHistory:
    if not os.path.exists(path):
        return SchemaHistory()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SchemaHistory.from_dict(data)
