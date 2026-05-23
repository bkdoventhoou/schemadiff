"""Watch a schema file for changes and emit diffs automatically."""

import time
import os
from typing import Callable, Optional

from schemadiff.serializer import schema_from_dict
from schemadiff.differ import diff_schemas, has_changes
from schemadiff.formatter import format_diff_as_string
from schemadiff.schema import Schema

import json


def _load_schema(path: str) -> Schema:
    with open(path, "r") as f:
        data = json.load(f)
    return schema_from_dict(data)


def _get_mtime(path: str) -> float:
    return os.path.getmtime(path)


def watch_schema_file(
    path: str,
    on_change: Optional[Callable[[str], None]] = None,
    poll_interval: float = 2.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll a schema JSON file and print diffs when it changes.

    Args:
        path: Path to the schema JSON file to watch.
        on_change: Optional callback receiving the diff string on each change.
        poll_interval: Seconds between polls.
        max_iterations: Stop after this many iterations (None = run forever).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema file not found: {path}")

    previous_schema = _load_schema(path)
    last_mtime = _get_mtime(path)
    iteration = 0

    print(f"[watcher] Watching {path} (interval={poll_interval}s)")

    while max_iterations is None or iteration < max_iterations:
        time.sleep(poll_interval)
        iteration += 1

        try:
            current_mtime = _get_mtime(path)
        except FileNotFoundError:
            print(f"[watcher] File removed: {path}")
            break

        if current_mtime == last_mtime:
            continue

        last_mtime = current_mtime
        try:
            current_schema = _load_schema(path)
        except Exception as exc:
            print(f"[watcher] Failed to load schema: {exc}")
            continue

        diff = diff_schemas(previous_schema, current_schema)
        if has_changes(diff):
            diff_str = format_diff_as_string(diff, use_color=False)
            if on_change:
                on_change(diff_str)
            else:
                print(f"[watcher] Schema changed:\n{diff_str}")
            previous_schema = current_schema
