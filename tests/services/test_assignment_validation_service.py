from datetime import datetime, time

from app.services.assignment_validation_service import (
    validate_contract_daily_hours,
    validate_contract_fixed_schedule,
    validate_contract_working_day,
)


class FakeContract:
    def __init__(
        self,
        weekly_hours = 40,
        daily_hours = 8,
        min_days_off_per_week = 2,
        work_monday = True,
        work_tuesday = True,
        work_wednesday = True,
        work_thursday = True,
        work_friday = True,
        work_saturday = False,
        work_sunday = False,
        has_fixed_schedule = False,
        preferred_start_time = None,
        preferred_end_time = None,
    ):
        self.weekly_hours = weekly_hours
        self.daily_hours = daily_hours
        self.min_days_off_per_week = min_days_off_per_week
        self.work_monday = work_monday
        self.work_tuesday = work_tuesday
        self.work_wednesday = work_wednesday
        self.work_thursday = work_thursday
        self.work_friday = work_friday
        self.work_saturday = work_saturday
        self.work_sunday = work_sunday
        self.has_fixed_schedule = has_fixed_schedule
        self.preferred_start_time = preferred_start_time
        self.preferred_end_time = preferred_end_time


def test_validate_contract_working_day_returns_no_errors_for_allowed_day():
    contract = FakeContract(work_monday = True)

    errors = validate_contract_working_day(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 9, 0),
    )

    assert errors == []


def test_validate_contract_working_day_returns_error_for_not_allowed_day():
    contract = FakeContract(work_saturday = False)

    errors = validate_contract_working_day(
        contract = contract,
        start_datetime = datetime(2026, 3, 7, 9, 0),
    )

    assert errors == [
        "The employee cannot work on this day according to the active contract"
    ]


def test_validate_contract_daily_hours_returns_no_errors_when_shift_fits_limit():
    contract = FakeContract(daily_hours = 8)

    errors = validate_contract_daily_hours(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 9, 0),
        end_datetime = datetime(2026, 3, 2, 17, 0),
    )

    assert errors == []


def test_validate_contract_daily_hours_returns_error_when_shift_exceeds_limit():
    contract = FakeContract(daily_hours = 6)

    errors = validate_contract_daily_hours(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 9, 0),
        end_datetime = datetime(2026, 3, 2, 17, 0),
    )

    assert errors == [
        "The shift exceeds the daily hours allowed by the active contract"
    ]


def test_validate_contract_fixed_schedule_returns_no_errors_when_contract_has_no_fixed_schedule():
    contract = FakeContract(has_fixed_schedule = False)

    errors = validate_contract_fixed_schedule(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 8, 0),
        end_datetime = datetime(2026, 3, 2, 20, 0),
    )

    assert errors == []


def test_validate_contract_fixed_schedule_returns_no_errors_when_preferred_times_are_missing():
    contract = FakeContract(
        has_fixed_schedule = True,
        preferred_start_time = None,
        preferred_end_time = None,
    )

    errors = validate_contract_fixed_schedule(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 8, 0),
        end_datetime = datetime(2026, 3, 2, 20, 0),
    )

    assert errors == []


def test_validate_contract_fixed_schedule_returns_no_errors_when_shift_is_inside_fixed_schedule():
    contract = FakeContract(
        has_fixed_schedule = True,
        preferred_start_time = time(9, 0),
        preferred_end_time = time(17, 0),
    )

    errors = validate_contract_fixed_schedule(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 9, 0),
        end_datetime = datetime(2026, 3, 2, 17, 0),
    )

    assert errors == []


def test_validate_contract_fixed_schedule_returns_error_when_shift_starts_too_early():
    contract = FakeContract(
        has_fixed_schedule = True,
        preferred_start_time = time(9, 0),
        preferred_end_time = time(17, 0),
    )

    errors = validate_contract_fixed_schedule(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 8, 0),
        end_datetime = datetime(2026, 3, 2, 16, 0),
    )

    assert errors == [
        "The shift is outside the fixed schedule allowed by the active contract"
    ]


def test_validate_contract_fixed_schedule_returns_error_when_shift_ends_too_late():
    contract = FakeContract(
        has_fixed_schedule = True,
        preferred_start_time = time(9, 0),
        preferred_end_time = time(17, 0),
    )

    errors = validate_contract_fixed_schedule(
        contract = contract,
        start_datetime = datetime(2026, 3, 2, 10, 0),
        end_datetime = datetime(2026, 3, 2, 18, 0),
    )

    assert errors == [
        "The shift is outside the fixed schedule allowed by the active contract"
    ]