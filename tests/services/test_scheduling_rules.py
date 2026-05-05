from datetime import date, datetime

from app.services.scheduling_rules import (
    get_week_bounds,
    validate_shift_within_schedule,
)


class FakeSchedule:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


def test_get_week_bounds_returns_monday_start_and_next_monday_end():
    reference_datetime = datetime(2026, 3, 4, 15, 30)

    week_start, week_end = get_week_bounds(reference_datetime)

    assert week_start == datetime(2026, 3, 2, 0, 0)
    assert week_end == datetime(2026, 3, 9, 0, 0)


def test_get_week_bounds_when_reference_is_monday():
    reference_datetime = datetime(2026, 3, 2, 10, 0)

    week_start, week_end = get_week_bounds(reference_datetime)

    assert week_start == datetime(2026, 3, 2, 0, 0)
    assert week_end == datetime(2026, 3, 9, 0, 0)


def test_validate_shift_within_schedule_returns_no_errors_when_shift_is_inside_range():
    schedule = FakeSchedule(
        start_date = date(2026, 3, 1),
        end_date = date(2026, 3, 7),
    )

    errors = validate_shift_within_schedule(
        start_datetime = datetime(2026, 3, 2, 9, 0),
        end_datetime = datetime(2026, 3, 2, 13, 0),
        schedule = schedule,
    )

    assert errors == []


def test_validate_shift_within_schedule_returns_error_when_shift_starts_before_schedule():
    schedule = FakeSchedule(
        start_date = date(2026, 3, 1),
        end_date = date(2026, 3, 7),
    )

    errors = validate_shift_within_schedule(
        start_datetime = datetime(2026, 2, 28, 23, 0),
        end_datetime = datetime(2026, 3, 1, 2, 0),
        schedule = schedule,
    )

    assert errors == ["Shift must be within the schedule date range"]


def test_validate_shift_within_schedule_returns_error_when_shift_ends_after_schedule():
    schedule = FakeSchedule(
        start_date = date(2026, 3, 1),
        end_date = date(2026, 3, 7),
    )

    errors = validate_shift_within_schedule(
        start_datetime = datetime(2026, 3, 7, 22, 0),
        end_datetime = datetime(2026, 3, 8, 2, 0),
        schedule = schedule,
    )

    assert errors == ["Shift must be within the schedule date range"]