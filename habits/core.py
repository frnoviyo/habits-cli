"""Pure domain logic: habits, name normalization and streaks. No I/O allowed."""

from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class Habit:
    """A habit with the name as typed by the user and the days it was done."""

    name: str
    done_dates: set[date] = field(default_factory=set)


class HabitError(Exception):
    """Base class for domain errors. Carries no user-facing text (plan D8)."""


class EmptyNameError(HabitError):
    """The habit name is empty or only whitespace (RF-1.4)."""


class DuplicateHabitError(HabitError):
    """A habit with the same normalized name already exists (RF-1.3)."""


class HabitNotFoundError(HabitError):
    """No habit matches the given normalized name (RF-2.4)."""


def normalize_name(name: str) -> str:
    """Return the comparison key: outer spaces removed, case-insensitive (RF-2.2)."""
    return name.strip().casefold()


def find_habit(habits: list[Habit], name: str) -> Habit | None:
    """Return the habit whose normalized name matches `name`, or None."""
    key = normalize_name(name)
    for habit in habits:
        if normalize_name(habit.name) == key:
            return habit
    return None


def add_habit(habits: list[Habit], name: str) -> Habit:
    """Append a new habit named `name` (without outer spaces) and return it (RF-1)."""
    clean_name = name.strip()
    if not clean_name:
        raise EmptyNameError(name)
    if find_habit(habits, clean_name) is not None:
        raise DuplicateHabitError(clean_name)
    habit = Habit(name=clean_name)
    habits.append(habit)
    return habit


def mark_done(
    habits: list[Habit], name: str, today: date, *, yesterday: bool = False
) -> tuple[Habit, bool]:
    """Mark `today`, or the day before if `yesterday` is True, as done (RF-2, RF-5).

    The flag is False if that day was already marked. Only these two days can be
    marked (RF-2.5), so the day is derived from `today` rather than passed in.
    """
    habit = find_habit(habits, name)
    if habit is None:
        raise HabitNotFoundError(name)
    day = today - timedelta(days=1) if yesterday else today
    if day in habit.done_dates:
        return habit, False
    habit.done_dates.add(day)
    return habit, True


def is_done_on(habit: Habit, day: date) -> bool:
    """Return whether the habit was done on `day`."""
    return day in habit.done_dates


def current_streak(habit: Habit, today: date) -> int:
    """Consecutive done days ending today, or yesterday if today is not done (RF-3.2).

    Dates after `today` are ignored.
    """
    one_day = timedelta(days=1)
    if today in habit.done_dates:
        cursor = today
    elif today - one_day in habit.done_dates:
        cursor = today - one_day
    else:
        return 0
    streak = 0
    while cursor in habit.done_dates:
        streak += 1
        cursor -= one_day
    return streak
