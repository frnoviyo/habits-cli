import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

from habits.cli import main
from habits.core import Habit
from habits.storage import load_habits, save_habits

TODAY = date(2026, 10, 14)
YESTERDAY = TODAY - timedelta(days=1)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def data_path(tmp_path: Path) -> Path:
    return tmp_path / "habits.json"


def run(argv: list[str], data_path: Path, today: date = TODAY) -> int:
    return main(argv, today=today, data_path=data_path)


def forbid_save(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_save(path: Path, habits: list[Habit]) -> None:
        raise AssertionError("save_habits must not be called")

    monkeypatch.setattr("habits.cli.save_habits", failing_save)


# --- T11: Spanish parser -------------------------------------------------------


@pytest.mark.parametrize(
    ("argv", "problem"),
    [
        pytest.param([], "Error: falta el comando.", id="no_command"),
        pytest.param(["borrar", "Leer"], "Error: comando desconocido «borrar».", id="unknown_command"),
        pytest.param(["crear"], "Error: falta el nombre del hábito.", id="crear_without_name"),
        pytest.param(["hecho"], "Error: falta el nombre del hábito.", id="hecho_without_name"),
        pytest.param(["listar", "extra"], "Error: argumentos incorrectos para «listar».", id="extra_args"),
    ],
)
def test_wrong_usage_shows_spanish_usage_and_returns_2_rf_4_4(
    argv: list[str], problem: str, data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(argv, data_path) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.startswith(problem)
    assert "Uso: python -m habits <comando> [nombre]" in err
    assert "usage" not in err.lower()
    assert "error: argument" not in err
    assert not data_path.exists()


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_shows_spanish_usage_rf_4_2(
    flag: str, data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run([flag], data_path) == 0
    out, err = capsys.readouterr()
    assert out.startswith("Uso: python -m habits <comando> [nombre]")
    assert "usage" not in out.lower()
    assert err == ""


# --- T12: crear ----------------------------------------------------------------


def test_crear_creates_habit_rf_1_1_rf_1_2_rf_4_5(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(["crear", "  Repasar inglés  "], data_path) == 0
    out, err = capsys.readouterr()
    assert out == "Hábito «Repasar inglés» creado.\n"
    assert err == ""
    assert load_habits(data_path) == [Habit(name="Repasar inglés")]


def test_crear_duplicate_fails_without_changes_rf_1_3_cl_1(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    save_habits(data_path, [Habit(name="Leer")])
    before = data_path.read_bytes()
    assert run(["crear", " leer "], data_path) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "Error: ya existe un hábito llamado «Leer».\n"
    assert data_path.read_bytes() == before


@pytest.mark.parametrize("name", ["", "   "])
def test_crear_empty_name_fails_without_changes_rf_1_4_cl_2(
    name: str, data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    save_habits(data_path, [Habit(name="Leer")])
    before = data_path.read_bytes()
    assert run(["crear", name], data_path) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "Error: el nombre del hábito no puede estar vacío.\n"
    assert data_path.read_bytes() == before


# --- T13: hecho ----------------------------------------------------------------


def test_hecho_marks_today_and_shows_streak_rf_2_1_rf_2_2_cl_3(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    save_habits(
        data_path, [Habit(name="Leer", done_dates={YESTERDAY, YESTERDAY - timedelta(days=1)})]
    )
    assert run(["hecho", "LEER"], data_path) == 0
    out, err = capsys.readouterr()
    assert out == "«Leer» marcado como hecho hoy. Racha actual: 3 días.\n"
    assert err == ""
    assert TODAY in load_habits(data_path)[0].done_dates


def test_hecho_first_day_uses_singular_rf_2_1(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    save_habits(data_path, [Habit(name="Leer")])
    assert run(["hecho", "Leer"], data_path) == 0
    assert capsys.readouterr().out == "«Leer» marcado como hecho hoy. Racha actual: 1 día.\n"


def test_hecho_twice_warns_and_does_not_save_rf_2_3_cl_4(
    data_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    save_habits(data_path, [Habit(name="Leer", done_dates={TODAY, YESTERDAY})])
    before = data_path.read_bytes()
    forbid_save(monkeypatch)
    assert run(["hecho", "leer"], data_path) == 0
    out, err = capsys.readouterr()
    assert out == "«Leer» ya estaba marcado hoy. Racha actual: 2 días.\n"
    assert err == ""
    assert data_path.read_bytes() == before


def test_hecho_missing_habit_fails_without_changes_rf_2_4_cl_5(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    save_habits(data_path, [Habit(name="Leer")])
    before = data_path.read_bytes()
    assert run(["hecho", "Correr"], data_path) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "Error: no existe el hábito «Correr». Usa «listar» para ver tus hábitos.\n"
    assert data_path.read_bytes() == before


def test_hecho_marks_only_the_given_today_rf_2_5(data_path: Path) -> None:
    save_habits(data_path, [Habit(name="Leer")])
    assert run(["hecho", "Leer"], data_path, today=date(2027, 1, 1)) == 0
    assert load_habits(data_path)[0].done_dates == {date(2027, 1, 1)}


# --- T14: listar ---------------------------------------------------------------


def test_listar_matches_plan_example_rf_3_1_rf_3_2_cl_6_cl_13(
    data_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    save_habits(
        data_path,
        [
            Habit(name="Leer", done_dates={TODAY, YESTERDAY, YESTERDAY - timedelta(days=1)}),
            Habit(name="Repasar inglés", done_dates={YESTERDAY}),  # CL-6: yesterday still counts
        ],
    )
    forbid_save(monkeypatch)
    assert run(["listar"], data_path) == 0
    out, err = capsys.readouterr()
    assert out == (
        "[x] Leer            racha: 3 días\n"
        "[ ] Repasar inglés  racha: 1 día\n"
    )
    assert err == ""


def test_listar_new_habit_has_zero_streak_cl_9(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    save_habits(data_path, [Habit(name="Leer")])
    assert run(["listar"], data_path) == 0
    assert capsys.readouterr().out == "[ ] Leer  racha: 0 días\n"


def test_listar_empty_rf_3_3_cl_12(data_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["listar"], data_path) == 0
    out, err = capsys.readouterr()
    assert out == "No hay hábitos todavía.\n"
    assert err == ""
    assert not data_path.exists()


# --- T15: unreadable data ------------------------------------------------------


@pytest.mark.parametrize("argv", [["crear", "Leer"], ["hecho", "Leer"], ["listar"]])
def test_corrupt_data_fails_without_changes_rnf_3_rnf_5(
    argv: list[str], data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_path.write_bytes(b"{not json")
    assert run(argv, data_path) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == (
        f"Error: no se pudo leer el archivo de datos {data_path}. "
        "Revísalo o muévelo para empezar de cero.\n"
    )
    assert data_path.read_bytes() == b"{not json"


# --- Exit code convention ------------------------------------------------------


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        pytest.param(["crear", "Correr"], 0, id="crear_ok"),
        pytest.param(["hecho", "Leer"], 0, id="hecho_ok"),
        pytest.param(["listar"], 0, id="listar_ok"),
        pytest.param(["crear", "Leer"], 1, id="domain_error_duplicate"),
        pytest.param(["hecho", "Correr"], 1, id="domain_error_missing"),
        pytest.param(["borrar"], 2, id="usage_error"),
    ],
)
def test_exit_codes_follow_convention_rf_4_3(
    argv: list[str], expected: int, data_path: Path
) -> None:
    """0 = success, 1 = domain or data error, 2 = wrong usage (plan §4)."""
    save_habits(data_path, [Habit(name="Leer")])
    assert run(argv, data_path) == expected


def test_unreadable_data_exit_code_is_1_rf_4_3(data_path: Path) -> None:
    data_path.write_bytes(b"{not json")
    assert run(["listar"], data_path) == 1


# --- Full flow -----------------------------------------------------------------


def test_full_flow_create_mark_list(data_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["crear", "Leer"], data_path, today=YESTERDAY) == 0
    assert run(["hecho", "leer"], data_path, today=YESTERDAY) == 0
    assert run(["hecho", "Leer"], data_path) == 0
    capsys.readouterr()
    assert run(["listar"], data_path) == 0
    assert capsys.readouterr().out == "[x] Leer  racha: 2 días\n"


# --- T16: python -m habits (smoke) ---------------------------------------------


def test_python_m_habits_end_to_end_rf_4_1_rf_4_5(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "HABITS_FILE": str(tmp_path / "habits.json"),
        "PYTHONIOENCODING": "utf-8",
    }

    def habits_cmd(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "habits", *args],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=30,
        )

    created = habits_cmd("crear", "Leer")
    assert created.returncode == 0, created.stderr
    marked = habits_cmd("hecho", "Leer")
    assert marked.returncode == 0, marked.stderr
    listed = habits_cmd("listar")
    assert listed.returncode == 0, listed.stderr
    assert listed.stdout == "[x] Leer  racha: 1 día\n"
