"""Command-line interface: parses arguments, prints Spanish messages, sets exit codes."""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import NoReturn

from habits.core import (
    DuplicateHabitError,
    EmptyNameError,
    Habit,
    HabitNotFoundError,
    add_habit,
    current_streak,
    find_habit,
    is_done_on,
    mark_done,
)
from habits.storage import StorageError, default_path, load_habits, save_habits

# Exit codes (RF-4.3, plan §4).
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2

COMMANDS_WITH_NAME = ("crear", "hecho")
COMMANDS = (*COMMANDS_WITH_NAME, "listar")

USAGE = """\
Uso: python -m habits <comando> [nombre] [--ayer]

Comandos:
  crear <nombre>          Crea un hábito nuevo (usa comillas si el nombre tiene espacios).
  hecho <nombre>          Marca un hábito como hecho hoy.
  hecho <nombre> --ayer   Marca un hábito como hecho ayer.
  listar                  Muestra tus hábitos con su racha actual.
"""


class UsageError(Exception):
    """Raised by the parser instead of printing argparse's English message and exiting."""


class SpanishArgumentParser(argparse.ArgumentParser):
    """ArgumentParser whose usage text is in Spanish and whose errors return control to main()."""

    def error(self, message: str) -> NoReturn:
        raise UsageError(message)

    def format_usage(self) -> str:
        return USAGE

    def format_help(self) -> str:
        return USAGE


def build_parser() -> SpanishArgumentParser:
    """Build the parser for `crear <nombre>`, `hecho <nombre> [--ayer]` and `listar` (plan D1, D2, D10)."""
    options = {"add_help": False, "allow_abbrev": False}
    parser = SpanishArgumentParser(prog="python -m habits", **options)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("crear", **options).add_argument("name")
    mark_parser = subparsers.add_parser("hecho", **options)
    mark_parser.add_argument("name")
    mark_parser.add_argument("--ayer", action="store_true", dest="yesterday")
    subparsers.add_parser("listar", **options)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    today: date | None = None,
    data_path: Path | None = None,
) -> int:
    """Run one command and return the exit code. `today` and `data_path` exist for tests."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list[:1] in (["-h"], ["--help"]):
        print(USAGE, end="")
        return EXIT_OK
    try:
        args = build_parser().parse_args(args_list)
    except UsageError:
        _error(f"{_usage_problem(args_list)}\n\n{USAGE}", end="")
        return EXIT_USAGE

    # "Today" is read once per run and used throughout (spec D-3).
    today = date.today() if today is None else today
    path = default_path() if data_path is None else data_path
    try:
        habits = load_habits(path)
    except StorageError:
        _error(
            f"no se pudo leer el archivo de datos {path}. "
            "Revísalo o muévelo para empezar de cero."
        )
        return EXIT_ERROR

    if args.command == "crear":
        return _create(habits, args.name, path)
    if args.command == "hecho":
        return _mark(habits, args.name, today, path, yesterday=args.yesterday)
    return _list(habits, today)


def _create(habits: list[Habit], name: str, path: Path) -> int:
    try:
        habit = add_habit(habits, name)
    except EmptyNameError:
        _error("el nombre del hábito no puede estar vacío.")
        return EXIT_ERROR
    except DuplicateHabitError:
        existing = find_habit(habits, name)
        shown = existing.name if existing is not None else name.strip()
        _error(f"ya existe un hábito llamado «{shown}».")
        return EXIT_ERROR
    save_habits(path, habits)
    print(f"Hábito «{habit.name}» creado.")
    return EXIT_OK


def _mark(habits: list[Habit], name: str, today: date, path: Path, *, yesterday: bool) -> int:
    try:
        habit, changed = mark_done(habits, name, today, yesterday=yesterday)
    except HabitNotFoundError:
        _error(f"no existe el hábito «{name.strip()}». Usa «listar» para ver tus hábitos.")
        return EXIT_ERROR
    day_word = "ayer" if yesterday else "hoy"
    streak = _days_text(current_streak(habit, today))
    if changed:
        save_habits(path, habits)
        print(f"«{habit.name}» marcado como hecho {day_word}. Racha actual: {streak}.")
    else:
        print(f"«{habit.name}» ya estaba marcado {day_word}. Racha actual: {streak}.")
    return EXIT_OK


def _list(habits: list[Habit], today: date) -> int:
    if not habits:
        print("No hay hábitos todavía.")
        return EXIT_OK
    width = max(len(habit.name) for habit in habits)
    for habit in habits:
        mark = "[x]" if is_done_on(habit, today) else "[ ]"
        streak = _days_text(current_streak(habit, today))
        print(f"{mark} {habit.name.ljust(width)}  racha: {streak}")
    return EXIT_OK


def _usage_problem(args_list: list[str]) -> str:
    """Describe the usage mistake in Spanish from the raw arguments, not argparse's English text."""
    if not args_list:
        return "falta el comando."
    command = args_list[0]
    if command not in COMMANDS:
        return f"comando desconocido «{command}»."
    has_name = any(not arg.startswith("-") for arg in args_list[1:])
    if command in COMMANDS_WITH_NAME and not has_name:
        return "falta el nombre del hábito."
    return f"argumentos incorrectos para «{command}»."


def _days_text(days: int) -> str:
    return "1 día" if days == 1 else f"{days} días"


def _error(message: str, end: str = "\n") -> None:
    print(f"Error: {message}", file=sys.stderr, end=end)
