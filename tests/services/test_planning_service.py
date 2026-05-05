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


def test_generate_schedule_creates_unfilled_shift_when_all_candidates_invalid(
    db,
    test_schedule,
    active_employees,
    test_shifts,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.planning_service.get_assignment_errors",
        lambda **kwargs: ["Employee cannot be assigned"],
    )

    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert result["assignments_created"] == []
    assert len(result["unfilled_shifts"]) == len(test_shifts)
    assert result["unfilled_shifts"][0]["missing_employees"] == 1
    assert result["unfilled_shifts"][0]["rejected_employees"] != []


def test_generate_schedule_message_when_missing_hours(
    db,
    test_schedule,
    active_employees,
    test_shifts,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.planning_service.get_employees_below_target",
        lambda **kwargs: ([{"employee_id": active_employees[0].id}], 10.0),
    )

    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert result["missing_contract_hours_total"] == 10.0
    assert "Additional shifts covering 10.0 hours are needed" in result["message"]


def test_generate_schedule_message_when_all_hours_fulfilled(
    db,
    test_schedule,
    active_employees,
    test_shifts,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.planning_service.get_employees_below_target",
        lambda **kwargs: ([], 0.0),
    )

    result = generate_schedule(
        db = db,
        schedule_id = test_schedule.id,
    )

    assert result["missing_contract_hours_total"] == 0.0
    assert result["message"] == "Planning generated successfully and all active contract hours were fulfilled"


def test_get_candidate_priority_returns_expected_tuple(
    db,
    active_employees,
    test_shifts,
    monkeypatch,
):
    from app.services.planning_service import get_candidate_priority

    employee = active_employees[0]
    contract = employee.contracts[0]
    shift = test_shifts[0]

    monkeypatch.setattr(
        "app.services.planning_service.get_employee_weekly_assigned_hours",
        lambda **kwargs: 10,
    )

    monkeypatch.setattr(
        "app.services.planning_service.get_employee_weekly_working_days",
        lambda **kwargs: {shift.start_datetime.date()},
    )

    result = get_candidate_priority(
        db = db,
        employee = employee,
        contract = contract,
        shift = shift,
    )

    assert result == (30, 40, -1)


def test_build_empty_planning_response():
    from app.services.planning_service import build_empty_planning_response

    result = build_empty_planning_response()

    assert result["assignments_created"] == []
    assert result["unfilled_shifts"] == []
    assert result["employees_below_target"] == []
    assert result["missing_contract_hours_total"] == 0.0


def test_build_planning_message_when_missing_hours():
    from app.services.planning_service import build_planning_message

    result = build_planning_message(10.0)

    assert "Additional shifts covering 10.0 hours are needed" in result


def test_build_planning_message_when_no_missing_hours():
    from app.services.planning_service import build_planning_message

    result = build_planning_message(0.0)

    assert result == "Planning generated successfully and all active contract hours were fulfilled"


def test_build_unfilled_shift_response(test_shifts):
    from app.services.planning_service import build_unfilled_shift_response

    shift = test_shifts[0]
    rejected_employees = [{"employee_id": 1, "errors": ["error"]}]

    result = build_unfilled_shift_response(
        shift = shift,
        rejected_employees = rejected_employees,
    )

    assert result["shift_id"] == shift.id
    assert result["missing_employees"] == 1
    assert result["rejected_employees"] == rejected_employees


def test_build_candidate_pool_excludes_assigned_employees(active_employees):
    from app.services.planning_service import build_candidate_pool

    employee = active_employees[0]
    contract = employee.contracts[0]

    result = build_candidate_pool(
        employees_with_contracts = [(employee, contract)],
        assigned_employee_ids = {employee.id},
    )

    assert result == []


def test_build_available_hours_candidate_pool_excludes_employees_without_remaining_hours(
    db,
    active_employees,
    test_shifts,
    monkeypatch,
):
    from app.services.planning_service import build_available_hours_candidate_pool

    employee = active_employees[0]
    contract = employee.contracts[0]
    shift = test_shifts[0]

    monkeypatch.setattr(
        "app.services.planning_service.get_employee_weekly_assigned_hours",
        lambda **kwargs: contract.weekly_hours,
    )

    result = build_available_hours_candidate_pool(
        db = db,
        shift = shift,
        employees_with_contracts = [(employee, contract)],
        assigned_employee_ids = set(),
    )

    assert result == []