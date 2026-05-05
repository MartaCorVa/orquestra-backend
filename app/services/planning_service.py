from typing import Any

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.shift import Shift
from app.services.assignment_validation_service import (
    get_assignment_errors,
    get_employee_weekly_assigned_hours,
    get_employee_weekly_working_days,
)
from app.services.shift_service import validate_schedule_exists


def get_active_contract(db: Session, employee_id: int) -> Contract | None:
    return (
        db.query(Contract)
        .filter(
            Contract.employee_id == employee_id,
            Contract.active == True,
        )
        .first()
    )


def get_candidate_priority(
    db: Session,
    employee: Employee,
    contract: Contract,
    shift: Shift,
) -> tuple[float, int, int]:
    assigned_hours = get_employee_weekly_assigned_hours(
        db = db,
        employee_id = employee.id,
        reference_datetime = shift.start_datetime,
    )

    working_days = get_employee_weekly_working_days(
        db = db,
        employee_id = employee.id,
        reference_datetime = shift.start_datetime,
    )

    remaining_hours = contract.weekly_hours - assigned_hours

    return (
        remaining_hours,
        contract.weekly_hours,
        -len(working_days),
    )


def get_employees_below_target(
    db: Session,
    employees_with_contracts: list[tuple[Employee, Contract]],
    reference_shift: Shift,
) -> tuple[list[dict[str, Any]], float]:
    employees_below_target: list[dict[str, Any]] = []
    missing_contract_hours_total = 0.0

    for employee, contract in employees_with_contracts:
        assigned_hours = get_employee_weekly_assigned_hours(
            db = db,
            employee_id = employee.id,
            reference_datetime = reference_shift.start_datetime,
        )

        missing_hours = max(0.0, contract.weekly_hours - assigned_hours)

        if missing_hours > 0:
            employees_below_target.append(
                {
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "contract_id": contract.id,
                    "contract_hours": contract.weekly_hours,
                    "assigned_hours": assigned_hours,
                    "missing_hours": missing_hours,
                }
            )

            missing_contract_hours_total += missing_hours

    return employees_below_target, missing_contract_hours_total


def get_active_employees_with_contracts(db: Session) -> list[tuple[Employee, Contract]]:
    employees = (
        db.query(Employee)
        .filter(Employee.active == True)
        .order_by(Employee.id.asc())
        .all()
    )

    employees_with_contracts = []

    for employee in employees:
        active_contract = get_active_contract(db = db, employee_id = employee.id)

        if active_contract is not None:
            employees_with_contracts.append((employee, active_contract))

    return employees_with_contracts


def get_schedule_shifts(db: Session, schedule_id: int) -> list[Shift]:
    return (
        db.query(Shift)
        .filter(Shift.schedule_id == schedule_id)
        .order_by(Shift.start_datetime.asc())
        .all()
    )


def get_shift_assigned_employee_ids(db: Session, shift: Shift) -> set[int]:
    existing_assignments = (
        db.query(Assignment)
        .filter(Assignment.shift_id == shift.id)
        .all()
    )

    return {assignment.employee_id for assignment in existing_assignments}


def build_candidate_pool(
    employees_with_contracts: list[tuple[Employee, Contract]],
    assigned_employee_ids: set[int],
) -> list[tuple[Employee, Contract]]:
    return [
        (employee, contract)
        for employee, contract in employees_with_contracts
        if employee.id not in assigned_employee_ids
    ]


def sort_candidate_pool(
    db: Session,
    candidate_pool: list[tuple[Employee, Contract]],
    shift: Shift,
) -> None:
    candidate_pool.sort(
        key = lambda candidate, current_shift = shift: get_candidate_priority(
            db = db,
            employee = candidate[0],
            contract = candidate[1],
            shift = current_shift,
        ),
        reverse = True,
    )


def build_available_hours_candidate_pool(
    db: Session,
    shift: Shift,
    employees_with_contracts: list[tuple[Employee, Contract]],
    assigned_employee_ids: set[int],
) -> list[tuple[Employee, Contract]]:
    candidate_pool = []

    for employee, contract in employees_with_contracts:
        if employee.id in assigned_employee_ids:
            continue

        assigned_hours = get_employee_weekly_assigned_hours(
            db = db,
            employee_id = employee.id,
            reference_datetime = shift.start_datetime,
        )

        if contract.weekly_hours - assigned_hours > 0:
            candidate_pool.append((employee, contract))

    return candidate_pool


def assign_valid_candidates_to_shift(
    db: Session,
    shift: Shift,
    candidate_pool: list[tuple[Employee, Contract]],
) -> list[Assignment]:
    assignments_created = []

    for employee, contract in candidate_pool:
        errors = get_assignment_errors(
            db = db,
            shift = shift,
            employee = employee,
            contract = contract,
        )

        if errors:
            continue

        assignment = Assignment(
            employee_id = employee.id,
            shift_id = shift.id,
        )

        db.add(assignment)
        db.flush()
        assignments_created.append(assignment)

    return assignments_created


def build_empty_planning_response() -> dict[str, Any]:
    return {
        "assignments_created": [],
        "unfilled_shifts": [],
        "employees_below_target": [],
        "missing_contract_hours_total": 0.0,
        "message": "No employees with active contracts or shifts available for planning",
    }


def build_planning_message(missing_contract_hours_total: float) -> str:
    if missing_contract_hours_total > 0:
        return (
            "Planning generated successfully. "
            f"Additional shifts covering {missing_contract_hours_total} hours are needed "
            "to fulfill all active contract hours before regenerating planning."
        )

    return "Planning generated successfully and all active contract hours were fulfilled"


def build_planning_response(
    db: Session,
    shifts: list[Shift],
    employees_with_contracts: list[tuple[Employee, Contract]],
    assignments_created: list[Assignment],
    unfilled_shifts: list[dict[str, Any]],
) -> dict[str, Any]:
    employees_below_target, missing_contract_hours_total = get_employees_below_target(
        db = db,
        employees_with_contracts = employees_with_contracts,
        reference_shift = shifts[0],
    )

    return {
        "assignments_created": [
            {
                "shift_id": assignment.shift_id,
                "employee_id": assignment.employee_id,
            }
            for assignment in assignments_created
        ],
        "unfilled_shifts": unfilled_shifts,
        "employees_below_target": employees_below_target,
        "missing_contract_hours_total": missing_contract_hours_total,
        "message": build_planning_message(missing_contract_hours_total),
    }


def build_unfilled_shift_response(
    shift: Shift,
    rejected_employees: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "shift_id": shift.id,
        "start_datetime": shift.start_datetime,
        "end_datetime": shift.end_datetime,
        "required_employees": 1,
        "assigned_employees": 0,
        "missing_employees": 1,
        "rejected_employees": rejected_employees,
    }


def assign_required_employee_to_shift(
    db: Session,
    shift: Shift,
    employees_with_contracts: list[tuple[Employee, Contract]],
    assigned_employee_ids: set[int],
) -> tuple[list[Assignment], dict[str, Any] | None]:
    rejected_employees: list[dict[str, Any]] = []

    candidate_pool = build_candidate_pool(
        employees_with_contracts = employees_with_contracts,
        assigned_employee_ids = assigned_employee_ids,
    )

    sort_candidate_pool(
        db = db,
        candidate_pool = candidate_pool,
        shift = shift,
    )

    for employee, contract in candidate_pool:
        errors = get_assignment_errors(
            db = db,
            shift = shift,
            employee = employee,
            contract = contract,
        )

        if errors:
            rejected_employees.append(
                {
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "contract_id": contract.id,
                    "errors": errors,
                }
            )
            continue

        assignment = Assignment(
            employee_id = employee.id,
            shift_id = shift.id,
        )

        db.add(assignment)
        db.flush()
        assigned_employee_ids.add(employee.id)

        return [assignment], None

    return [], build_unfilled_shift_response(
        shift = shift,
        rejected_employees = rejected_employees,
    )


def assign_required_employees_to_shifts(
    db: Session,
    shifts: list[Shift],
    employees_with_contracts: list[tuple[Employee, Contract]],
) -> tuple[list[Assignment], list[dict[str, Any]]]:
    assignments_created = []
    unfilled_shifts = []

    for shift in shifts:
        assigned_employee_ids = get_shift_assigned_employee_ids(db = db, shift = shift)

        if len(assigned_employee_ids) >= 1:
            continue

        assignments, unfilled_shift = assign_required_employee_to_shift(
            db = db,
            shift = shift,
            employees_with_contracts = employees_with_contracts,
            assigned_employee_ids = assigned_employee_ids,
        )

        assignments_created.extend(assignments)

        if unfilled_shift is not None:
            unfilled_shifts.append(unfilled_shift)

    return assignments_created, unfilled_shifts


def assign_additional_employees_to_shifts(
    db: Session,
    shifts: list[Shift],
    employees_with_contracts: list[tuple[Employee, Contract]],
) -> list[Assignment]:
    assignments_created = []

    for shift in shifts:
        assigned_employee_ids = get_shift_assigned_employee_ids(db = db, shift = shift)

        candidate_pool = build_available_hours_candidate_pool(
            db = db,
            shift = shift,
            employees_with_contracts = employees_with_contracts,
            assigned_employee_ids = assigned_employee_ids,
        )

        sort_candidate_pool(
            db = db,
            candidate_pool = candidate_pool,
            shift = shift,
        )

        assignments_created.extend(
            assign_valid_candidates_to_shift(
                db = db,
                shift = shift,
                candidate_pool = candidate_pool,
            )
        )

    return assignments_created


def generate_schedule(db: Session, schedule_id: int) -> dict[str, Any]:
    validate_schedule_exists(db = db, schedule_id = schedule_id)

    employees_with_contracts = get_active_employees_with_contracts(db)
    shifts = get_schedule_shifts(db = db, schedule_id = schedule_id)

    if not employees_with_contracts or not shifts:
        return build_empty_planning_response()

    required_assignments, unfilled_shifts = assign_required_employees_to_shifts(
        db = db,
        shifts = shifts,
        employees_with_contracts = employees_with_contracts,
    )

    additional_assignments = assign_additional_employees_to_shifts(
        db = db,
        shifts = shifts,
        employees_with_contracts = employees_with_contracts,
    )

    db.commit()

    return build_planning_response(
        db = db,
        shifts = shifts,
        employees_with_contracts = employees_with_contracts,
        assignments_created = required_assignments + additional_assignments,
        unfilled_shifts = unfilled_shifts,
    )