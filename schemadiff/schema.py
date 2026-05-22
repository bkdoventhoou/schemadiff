"""Core data models for representing database schemas."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Column):
            return False
        return (
            self.name == other.name
            and self.data_type == other.data_type
            and self.nullable == other.nullable
            and self.default == other.default
            and self.primary_key == other.primary_key
        )


@dataclass
class Index:
    name: str
    columns: List[str]
    unique: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Index):
            return False
        return (
            self.name == other.name
            and sorted(self.columns) == sorted(other.columns)
            and self.unique == other.unique
        )


@dataclass
class Table:
    name: str
    columns: Dict[str, Column] = field(default_factory=dict)
    indexes: Dict[str, Index] = field(default_factory=dict)

    def add_column(self, column: Column) -> None:
        self.columns[column.name] = column

    def add_index(self, index: Index) -> None:
        self.indexes[index.name] = index


@dataclass
class Schema:
    name: str
    tables: Dict[str, Table] = field(default_factory=dict)

    def add_table(self, table: Table) -> None:
        self.tables[table.name] = table

    @classmethod
    def from_dict(cls, data: dict) -> "Schema":
        schema = cls(name=data.get("name", "unnamed"))
        for table_data in data.get("tables", []):
            table = Table(name=table_data["name"])
            for col_data in table_data.get("columns", []):
                table.add_column(Column(**col_data))
            for idx_data in table_data.get("indexes", []):
                table.add_index(Index(**idx_data))
            schema.add_table(table)
        return schema
