"""Tag-based schema snapshot management for schemadiff."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from schemadiff.history import SchemaHistory, SnapshotEntry


@dataclass
class TagEntry:
    tag: str
    version: int
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "version": self.version,
            "description": self.description,
        }

    @staticmethod
    def from_dict(data: dict) -> "TagEntry":
        return TagEntry(
            tag=data["tag"],
            version=data["version"],
            description=data.get("description", ""),
        )


@dataclass
class SchemaTagger:
    history: SchemaHistory
    _tags: Dict[str, TagEntry] = field(default_factory=dict)

    def add_tag(self, tag: str, version: Optional[int] = None, description: str = "") -> TagEntry:
        if not tag or not tag.strip():
            raise ValueError("Tag name must not be empty")
        if tag in self._tags:
            raise ValueError(f"Tag '{tag}' already exists")
        resolved_version = version if version is not None else self.history.latest_version()
        if resolved_version is None:
            raise ValueError("No snapshots available to tag")
        if self.history.get_version(resolved_version) is None:
            raise ValueError(f"Version {resolved_version} does not exist in history")
        entry = TagEntry(tag=tag, version=resolved_version, description=description)
        self._tags[tag] = entry
        return entry

    def get_tag(self, tag: str) -> Optional[TagEntry]:
        return self._tags.get(tag)

    def remove_tag(self, tag: str) -> bool:
        if tag in self._tags:
            del self._tags[tag]
            return True
        return False

    def list_tags(self) -> List[TagEntry]:
        return sorted(self._tags.values(), key=lambda t: t.version)

    def resolve_snapshot(self, tag: str) -> Optional[SnapshotEntry]:
        entry = self._tags.get(tag)
        if entry is None:
            return None
        return self.history.get_version(entry.version)

    def tags_as_dict(self) -> dict:
        return {tag: entry.to_dict() for tag, entry in self._tags.items()}

    @staticmethod
    def tags_from_dict(history: SchemaHistory, data: dict) -> "SchemaTagger":
        tagger = SchemaTagger(history=history)
        for tag, entry_data in data.items():
            tagger._tags[tag] = TagEntry.from_dict(entry_data)
        return tagger
