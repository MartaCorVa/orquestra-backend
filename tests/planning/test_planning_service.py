from datetime import datetime

from app.models.assignment import Assignment
from app.models.shift import Shift
from app.services.planning_service import generate_schedule


def test_generate_schedule_creates_assignments(db, test_schedule, active_employees, test_shifts):
    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert len(result["assignments_created"]) >= 2
    assert result["unfilled_shifts"] == []
    assert "employees_below_target" in result
    assert "missing_contract_hours_total" in result

    stored_assignments = db.query(Assignment).all()
    assert len(stored_assignments) >= 2


def test_generate_schedule_returns_empty_when_no_employees(db, test_schedule, test_shifts):
    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert result["assignments_created"] == []
    assert result["unfilled_shifts"] == []
    assert result["employees_below_target"] == []
    assert result["missing_contract_hours_total"] == 0.0
    assert result["message"] == "No employees with active contracts or shifts available for planning"


def test_generate_schedule_returns_empty_when_no_shifts(db, test_schedule, active_employees):
    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert result["assignments_created"] == []
    assert result["unfilled_shifts"] == []
    assert result["employees_below_target"] == []
    assert result["missing_contract_hours_total"] == 0.0
    assert result["message"] == "No employees with active contracts or shifts available for planning"


def test_generate_schedule_creates_minimum_one_assignment_per_shift(db, test_schedule, active_employees):
    shifts = [
        Shift(
            start_datetime = datetime(2026, 3, 1, 9, 0),
            end_datetime = datetime(2026, 3, 1, 13, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
        Shift(
            start_datetime = datetime(2026, 3, 2, 9, 0),
            end_datetime = datetime(2026, 3, 2, 13, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
    ]

    db.add_all(shifts)
    db.commit()

    for shift in shifts:
        db.refresh(shift)

    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert len(result["assignments_created"]) >= 2
    assert result["unfilled_shifts"] == []

    for shift in shifts:
        shift_assignments = db.query(Assignment).filter(Assignment.shift_id == shift.id).all()
        assert len(shift_assignments) >= 1


def test_generate_schedule_does_not_create_duplicate_assignments(db, test_schedule, active_employees, test_shifts):
    generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    second_run = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert second_run["assignments_created"] == []

    stored_assignments = db.query(Assignment).all()
    assignment_pairs = {(assignment.employee_id, assignment.shift_id) for assignment in stored_assignments}

    assert len(assignment_pairs) == len(stored_assignments)


def test_generate_schedule_avoids_overlapping_assignments(db, test_schedule, active_employees):
    overlapping_shifts = [
        Shift(
            start_datetime = datetime(2026, 3, 2, 9, 0),
            end_datetime = datetime(2026, 3, 2, 13, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
        Shift(
            start_datetime = datetime(2026, 3, 2, 12, 0),
            end_datetime = datetime(2026, 3, 2, 16, 0),
            creation_type = "manual",
            status = "pending",
            schedule_id = test_schedule.id,
        ),
    ]

    db.add_all(overlapping_shifts)
    db.commit()

    for shift in overlapping_shifts:
        db.refresh(shift)

    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert len(result["assignments_created"]) >= 2

    first_shift_assignments = db.query(Assignment).filter(Assignment.shift_id == overlapping_shifts[0].id).all()
    second_shift_assignments = db.query(Assignment).filter(Assignment.shift_id == overlapping_shifts[1].id).all()

    assert len(first_shift_assignments) >= 1
    assert len(second_shift_assignments) >= 1

    first_shift_employee_ids = {assignment.employee_id for assignment in first_shift_assignments}
    second_shift_employee_ids = {assignment.employee_id for assignment in second_shift_assignments}

    assert first_shift_employee_ids.isdisjoint(second_shift_employee_ids)