"""Loading and saving habits to the local JSON file. Only module that touches it."""

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from habits.core import Habit

FORMAT_VERSION = 1


class StorageError(Exception):
    """The data file exists but cannot be read or does not follow the schema."""


def default_path() -> Path:
    """Return `HABITS_FILE` if set, otherwise `~/.habits.json` (plan D6)."""
    env_path = os.environ.get("HABITS_FILE")
    if env_path:
        return Path(env_path)
    return Path.home() / ".habits.json"


def load_habits(path: Path) -> list[Habit]:
    """Load habits in creation order; a missing file means no habits (RF-4.5).

    Raises StorageError if the file is unreadable or malformed; the file is never modified.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as exc:
        raise StorageError(str(path)) from exc
    try:
        return _parse(json.loads(text))
    except (ValueError, TypeError, KeyError) as exc:
        raise StorageError(str(path)) from exc


def _parse(data: Any) -> list[Habit]:
    if not isinstance(data, dict) or data.get("version") != FORMAT_VERSION:
        raise ValueError("unsupported data format")
    raw_habits = data["habits"]
    if not isinstance(raw_habits, list):
        raise ValueError("'habits' must be a list")
    habits = []
    for raw in raw_habits:
        if not isinstance(raw, dict):
            raise ValueError("each habit must be an object")
        name, raw_dates = raw["name"], raw["done_dates"]
        if not isinstance(name, str) or not isinstance(raw_dates, list):
            raise ValueError("invalid habit fields")
        # date.fromisoformat raises TypeError for non-strings and ValueError for bad formats.
        habits.append(Habit(name=name, done_dates={date.fromisoformat(d) for d in raw_dates}))
    return habits


def save_habits(path: Path, habits: list[Habit]) -> None:
    """Write habits atomically: temporary file in the same directory + os.replace (RNF-3)."""
    data = {
        "version": FORMAT_VERSION,
        "habits": [
            {"name": h.name, "done_dates": [d.isoformat() for d in sorted(h.done_dates)]}
            for h in habits
        ],
    }
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as tmp_file:
            tmp_file.write(text)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
