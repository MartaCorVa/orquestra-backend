from datetime import date, datetime

import pytest

from app.services.metrics_service import (
    calculate_shift_duration_hours,
    calculate_workload_metrics,
)


class FakeShift:
    def __init__(self, start_datetime, end_datetime):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime


class FakeUser:
    def __init__(self, id = 1, role = "admin"):
        self.id = id
        self.role = role


def test_calculate_shift_duration_hours_returns_duration_in_hours():
    shift = FakeShift(
        start_datetime = datetime(2026, 3, 1, 9, 0),
        end_datetime = datetime(2026, 3, 1, 13, 30),
    )

    result = calculate_shift_duration_hours(shift)

    assert result == 4.5


def test_calculate_shift_duration_hours_returns_zero_for_same_datetime():
    shift = FakeShift(
        start_datetime = datetime(2026, 3, 1, 9, 0),
        end_datetime = datetime(2026, 3, 1, 9, 0),
    )

    result = calculate_shift_duration_hours(shift)

    assert result == 0


def test_calculate_workload_metrics_raises_when_start_date_is_after_end_date():
    current_user = FakeUser(role = "admin")

    with pytest.raises(ValueError) as exc:
        calculate_workload_metrics(
            db = None,
            current_user = current_user,
            start_date = date(2026, 3, 10),
            end_date = date(2026, 3, 1),
        )

    assert str(exc.value) == "Start date cannot be later than end date"