import json
from datetime import date
from pathlib import Path

import pytest

from habits.core import Habit
from habits.storage import StorageError, default_path, load_habits, save_habits

PLAN_EXAMPLE = {
    "version": 1,
    "habits": [
        {"name": "Leer", "done_dates": ["2026-10-12", "2026-10-13", "2026-10-14"]},
        {"name": "Repasar inglés", "done_dates": []},
    ],
}


def _plan_habits() -> list[Habit]:
    return [
        Habit(
            name="Leer",
            done_dates={date(2026, 10, 14), date(2026, 10, 12), date(2026, 10, 13)},
        ),
        Habit(name="Repasar inglés"),
    ]


# --- T08: data path ------------------------------------------------------------


def test_default_path_is_home_file_rf_4_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HABITS_FILE", raising=False)
    assert default_path() == Path.home() / ".habits.json"


def test_default_path_uses_habits_file_env_rf_4_1(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "custom.json"
    monkeypatch.setenv("HABITS_FILE", str(target))
    assert default_path() == target


# --- T09: load -----------------------------------------------------------------


def test_load_missing_file_returns_empty_list_rf_4_5(tmp_path: Path) -> None:
    assert load_habits(tmp_path / "missing.json") == []


def test_load_valid_file_keeps_order_rf_4_1(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text(json.dumps(PLAN_EXAMPLE, ensure_ascii=False), encoding="utf-8")
    assert load_habits(path) == _plan_habits()


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"{not json", id="invalid_json"),
        pytest.param(b"", id="empty_file"),
        pytest.param(b"[]", id="not_an_object"),
        pytest.param(b'{"version": 1}', id="missing_habits"),
        pytest.param(b'{"version": 2, "habits": []}', id="unknown_version"),
        pytest.param(b'{"version": 1, "habits": ["Leer"]}', id="habit_not_an_object"),
        pytest.param(b'{"version": 1, "habits": [{"name": "Leer"}]}', id="missing_done_dates"),
        pytest.param(b'{"version": 1, "habits": [{"name": 3, "done_dates": []}]}', id="bad_name"),
        pytest.param(
            b'{"version": 1, "habits": [{"name": "Leer", "done_dates": ["14/10/2026"]}]}',
            id="bad_date",
        ),
        pytest.param(
            b'{"version": 1, "habits": [{"name": "\xff", "done_dates": []}]}',
            id="not_utf8",
        ),
    ],
)
def test_load_corrupt_file_raises_and_keeps_file_rnf_3(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "habits.json"
    path.write_bytes(content)
    with pytest.raises(StorageError):
        load_habits(path)
    assert path.read_bytes() == content


# --- T10: atomic save ----------------------------------------------------------


def test_save_then_load_roundtrip_rf_4_1_cl_13(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    save_habits(path, _plan_habits())
    assert load_habits(path) == _plan_habits()


def test_save_matches_plan_format_cl_13(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    save_habits(path, _plan_habits())
    text = path.read_text(encoding="utf-8")
    assert json.loads(text) == PLAN_EXAMPLE  # sorted dates, creation order
    assert "Repasar inglés" in text  # UTF-8 without \u escapes


def test_save_replaces_existing_file_and_leaves_no_temp_files_rnf_3(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"
    path.write_text("old content", encoding="utf-8")
    save_habits(path, [Habit(name="Leer")])
    assert load_habits(path) == [Habit(name="Leer")]
    assert [p.name for p in tmp_path.iterdir()] == ["habits.json"]


def test_save_failure_keeps_previous_file_rnf_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "habits.json"
    save_habits(path, [Habit(name="Leer")])
    before = path.read_bytes()

    def failing_replace(src: str, dst: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("habits.storage.os.replace", failing_replace)
    with pytest.raises(OSError):
        save_habits(path, [Habit(name="Correr")])
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["habits.json"]
