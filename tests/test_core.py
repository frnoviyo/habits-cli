import inspect
from datetime import date, timedelta

import pytest

from habits.core import (
    DuplicateHabitError,
    EmptyNameError,
    Habit,
    HabitError,
    HabitNotFoundError,
    add_habit,
    current_streak,
    find_habit,
    is_done_on,
    mark_done,
    normalize_name,
)

TODAY = date(2026, 10, 14)


# --- T03: model and normalization ---------------------------------------------


def test_habit_starts_without_done_dates() -> None:
    habit = Habit(name="Leer")
    assert habit.done_dates == set()


def test_habit_errors_share_base_class() -> None:
    for error in (EmptyNameError, DuplicateHabitError, HabitNotFoundError):
        assert issubclass(error, HabitError)


def test_normalize_name_ignores_case_and_outer_spaces_rf_2_2_cl_1_cl_3() -> None:
    assert normalize_name(" Leer ") == normalize_name("LEER")


def test_normalize_name_keeps_accents_cl_13() -> None:
    assert normalize_name("Repasar Inglés") == "repasar inglés"
    assert normalize_name("Repasar inglés") != normalize_name("Repasar ingles")


def test_normalize_name_uses_unicode_casefold() -> None:
    assert normalize_name("Straße") == normalize_name("STRASSE")


# --- T04: create habits --------------------------------------------------------


def test_find_habit_by_normalized_name_rf_2_2() -> None:
    habits = [Habit(name="Leer")]
    assert find_habit(habits, "  LEER ") is habits[0]


def test_find_habit_returns_none_when_missing() -> None:
    assert find_habit([Habit(name="Leer")], "Correr") is None


def test_add_habit_appends_new_habit_without_done_dates_rf_1_1() -> None:
    habits = [Habit(name="Leer")]
    habit = add_habit(habits, "Correr")
    assert habits == [Habit(name="Leer"), habit]
    assert habit.done_dates == set()
    assert current_streak(habit, TODAY) == 0


def test_add_habit_stores_name_without_outer_spaces_rf_1_2_cl_13() -> None:
    habit = add_habit([], "  Repasar Inglés  ")
    assert habit.name == "Repasar Inglés"


def test_add_habit_rejects_duplicate_rf_1_3_cl_1() -> None:
    habits = [Habit(name="leer")]
    with pytest.raises(DuplicateHabitError):
        add_habit(habits, " Leer ")
    assert habits == [Habit(name="leer")]


@pytest.mark.parametrize("name", ["", "   ", "\t \n"])
def test_add_habit_rejects_empty_name_rf_1_4_cl_2(name: str) -> None:
    habits = [Habit(name="Leer")]
    with pytest.raises(EmptyNameError):
        add_habit(habits, name)
    assert habits == [Habit(name="Leer")]


# --- T05: mark as done ---------------------------------------------------------


def test_mark_done_records_today_rf_2_1_rf_2_5() -> None:
    habits = [Habit(name="Leer")]
    habit, changed = mark_done(habits, "Leer", TODAY)
    assert changed is True
    assert habit is habits[0]
    assert habit.done_dates == {TODAY}


def test_mark_done_finds_habit_by_normalized_name_rf_2_2_cl_3() -> None:
    habits = [Habit(name="Leer")]
    habit, _ = mark_done(habits, "LEER", TODAY)
    assert habit is habits[0]
    assert is_done_on(habits[0], TODAY)


def test_mark_done_twice_same_day_changes_nothing_rf_2_3_cl_4() -> None:
    habits = [Habit(name="Leer", done_dates={TODAY})]
    habit, changed = mark_done(habits, "Leer", TODAY)
    assert changed is False
    assert habit.done_dates == {TODAY}


def test_mark_done_missing_habit_raises_rf_2_4_cl_5() -> None:
    habits = [Habit(name="Leer")]
    with pytest.raises(HabitNotFoundError):
        mark_done(habits, "Correr", TODAY)
    assert habits == [Habit(name="Leer")]


def test_is_done_on() -> None:
    habit = Habit(name="Leer", done_dates={TODAY})
    assert is_done_on(habit, TODAY) is True
    assert is_done_on(habit, TODAY - timedelta(days=1)) is False


# --- T06: streak ---------------------------------------------------------------


def _days(*offsets: int, base: date = TODAY) -> set[date]:
    """Dates relative to `base`: 0 = base, 1 = the day before, -1 = the day after."""
    return {base - timedelta(days=offset) for offset in offsets}


@pytest.mark.parametrize(
    ("done_dates", "today", "expected"),
    [
        pytest.param(set(), TODAY, 0, id="cl_9_new_habit"),
        pytest.param(_days(0), TODAY, 1, id="only_today"),
        pytest.param(_days(0, 1, 2), TODAY, 3, id="three_days_ending_today"),
        pytest.param(_days(1, 2), TODAY, 2, id="cl_6_yesterday_and_before"),
        pytest.param(_days(0, 2), TODAY, 1, id="cl_7_gap_yesterday"),
        pytest.param(_days(2, 3, 4), TODAY, 0, id="cl_8_two_days_ago"),
        pytest.param(_days(10), TODAY, 0, id="cl_8_long_ago"),
        pytest.param(
            {date(2025, 12, 30), date(2025, 12, 31), date(2026, 1, 1)},
            date(2026, 1, 1),
            3,
            id="cl_10_year_change",
        ),
        pytest.param(
            {date(2026, 9, 30), date(2026, 10, 1)},
            date(2026, 10, 1),
            2,
            id="cl_10_month_change",
        ),
        pytest.param(
            {date(2028, 2, 28), date(2028, 2, 29), date(2028, 3, 1)},
            date(2028, 3, 1),
            3,
            id="cl_11_leap_day",
        ),
        pytest.param(_days(-1, 0, 1), TODAY, 2, id="future_date_ignored"),
        pytest.param(_days(-1), TODAY, 0, id="only_future_date"),
    ],
)
def test_current_streak_rf_3_2(done_dates: set[date], today: date, expected: int) -> None:
    habit = Habit(name="Leer", done_dates=done_dates)
    assert current_streak(habit, today) == expected


# --- T18: mark yesterday -------------------------------------------------------

YESTERDAY = TODAY - timedelta(days=1)


def test_mark_done_yesterday_records_previous_day_rf_5_1() -> None:
    habits = [Habit(name="Leer")]
    habit, changed = mark_done(habits, "LEER", TODAY, yesterday=True)
    assert changed is True
    assert habit is habits[0]
    assert habit.done_dates == {YESTERDAY}


def test_mark_done_yesterday_twice_changes_nothing_rf_5_2_cl_14() -> None:
    habits = [Habit(name="Leer", done_dates={YESTERDAY})]
    habit, changed = mark_done(habits, "Leer", TODAY, yesterday=True)
    assert changed is False
    assert habit.done_dates == {YESTERDAY}


def test_mark_done_yesterday_missing_habit_raises_rf_5_3_cl_20() -> None:
    habits = [Habit(name="Leer")]
    with pytest.raises(HabitNotFoundError):
        mark_done(habits, "Correr", TODAY, yesterday=True)
    assert habits == [Habit(name="Leer")]


@pytest.mark.parametrize(
    "initial",
    [pytest.param(set(), id="today_not_done"), pytest.param({TODAY}, id="today_done")],
)
def test_mark_done_yesterday_does_not_touch_today_rf_5_4(initial: set[date]) -> None:
    habits = [Habit(name="Leer", done_dates=set(initial))]
    mark_done(habits, "Leer", TODAY, yesterday=True)
    assert habits[0].done_dates == initial | {YESTERDAY}


@pytest.mark.parametrize("yesterday_first", [True, False])
def test_mark_yesterday_and_today_keeps_both_cl_22(yesterday_first: bool) -> None:
    habits = [Habit(name="Leer")]
    for yesterday in (yesterday_first, not yesterday_first):
        _, changed = mark_done(habits, "Leer", TODAY, yesterday=yesterday)
        assert changed is True
    assert habits[0].done_dates == {TODAY, YESTERDAY}


def test_mark_done_yesterday_on_habit_created_today_rf_5_6_cl_21() -> None:
    habits: list[Habit] = []
    add_habit(habits, "Leer")
    habit, changed = mark_done(habits, "Leer", TODAY, yesterday=True)
    assert changed is True
    assert current_streak(habit, TODAY) == 1


@pytest.mark.parametrize(
    ("today", "expected_day"),
    [
        pytest.param(date(2026, 1, 1), date(2025, 12, 31), id="year_change"),
        pytest.param(date(2028, 3, 1), date(2028, 2, 29), id="leap_year"),
        pytest.param(date(2027, 3, 1), date(2027, 2, 28), id="non_leap_year"),
    ],
)
def test_mark_done_yesterday_crosses_calendar_boundaries_cl_19(
    today: date, expected_day: date
) -> None:
    habits = [Habit(name="Leer")]
    mark_done(habits, "Leer", today, yesterday=True)
    assert habits[0].done_dates == {expected_day}


def test_mark_done_only_accepts_today_or_yesterday_rf_2_5() -> None:
    """The day is derived from `today`; no arbitrary date can be passed (plan D11)."""
    params = inspect.signature(mark_done).parameters
    assert list(params) == ["habits", "name", "today", "yesterday"]
    assert params["yesterday"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["yesterday"].default is False


# --- T19: streak after marking yesterday ---------------------------------------


@pytest.mark.parametrize(
    ("initial", "expected"),
    [
        pytest.param(set(), 1, id="cl_15_nothing_marked"),
        pytest.param(_days(0), 2, id="cl_16_today_marked"),
        pytest.param(_days(0, 2, 3), 4, id="cl_17_joins_streaks"),
        pytest.param(_days(2, 3), 3, id="cl_18_recovers_streak"),
    ],
)
def test_streak_after_marking_yesterday_rf_5_5(initial: set[date], expected: int) -> None:
    habits = [Habit(name="Leer", done_dates=set(initial))]
    habit, _ = mark_done(habits, "Leer", TODAY, yesterday=True)
    assert current_streak(habit, TODAY) == expected
    assert is_done_on(habit, TODAY) is (TODAY in initial)
