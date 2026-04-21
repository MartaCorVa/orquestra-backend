from datetime import datetime, time, timedelta

from app.models.schedule import Schedule


def get_week_bounds(reference_datetime: datetime) -> tuple[datetime, datetime]:
    week_start_date = reference_datetime.date() - timedelta(days = reference_datetime.weekday())
    week_start = datetime.combine(week_start_date, time.min)
    week_end = week_start + timedelta(days = 7)
    return week_start, week_end


def validate_shift_within_schedule(
    start_datetime: datetime,
    end_datetime: datetime,
    schedule: Schedule,
) -> list[str]:
    errors: list[str] = []

    if start_datetime.date() < schedule.start_date or end_datetime.date() > schedule.end_date:
        errors.append("Shift must be within the schedule date range")

    return errors