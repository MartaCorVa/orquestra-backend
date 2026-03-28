from datetime import date, time

from app.models.assignment import Assignment
from app.models.shift import Shift
from app.services.planning_service import generate_schedule


def test_generate_schedule_creates_assignments(db, test_schedule, active_employees, test_shifts):
    assignments = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 1,
    )

    assert len(assignments) == 2

    stored_assignments = db.query(Assignment).all()
    assert len(stored_assignments) == 2


def test_generate_schedule_returns_empty_when_no_employees(db, test_schedule, test_shifts):
    assignments = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 1,
    )

    assert assignments == []


def test_generate_schedule_returns_empty_when_no_shifts(db, test_schedule, active_employees):
    assignments = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 1,
    )

    assert assignments == []


def test_generate_schedule_respects_employees_per_shift(db, test_schedule, active_employees, test_shifts):
    assignments = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 2,
    )

    assert len(assignments) == 4

    for shift in test_shifts:
        shift_assignments = db.query(Assignment).filter(Assignment.shift_id == shift.id).all()
        assert len(shift_assignments) == 2


def test_generate_schedule_does_not_create_duplicate_assignments(db, test_schedule, active_employees, test_shifts):
    generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 1,
    )

    second_run = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 1,
    )

    assert second_run == []

    stored_assignments = db.query(Assignment).all()
    assert len(stored_assignments) == 2


def test_generate_schedule_avoids_overlapping_assignments(db, test_schedule, active_employees):
    overlapping_shifts = [
        Shift(
            date = date(2026, 3, 2),
            start_time = time(9, 0),
            end_time = time(13, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
        Shift(
            date = date(2026, 3, 2),
            start_time = time(12, 0),
            end_time = time(16, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
    ]

    db.add_all(overlapping_shifts)
    db.commit()

    for shift in overlapping_shifts:
        db.refresh(shift)

    assignments = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
        employees_per_shift = 1,
    )

    assert len(assignments) == 2

    first_shift_assignment = db.query(Assignment).filter(Assignment.shift_id == overlapping_shifts[0].id).first()
    second_shift_assignment = db.query(Assignment).filter(Assignment.shift_id == overlapping_shifts[1].id).first()

    assert first_shift_assignment.employee_id != second_shift_assignment.employee_id