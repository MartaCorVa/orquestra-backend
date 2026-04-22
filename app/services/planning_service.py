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


def generate_schedule(db: Session, schedule_id: int) -> dict[str, Any]:
    validate_schedule_exists(db = db, schedule_id = schedule_id)

    all_employees = (
        db.query(Employee)
        .filter(Employee.active == True)
        .order_by(Employee.id.asc())
        .all()
    )

    employees_with_contracts: list[tuple[Employee, Contract]] = []

    for employee in all_employees:
        active_contract = get_active_contract(db = db, employee_id = employee.id)

        if active_contract is not None:
            employees_with_contracts.append((employee, active_contract))

    shifts = (
        db.query(Shift)
        .filter(Shift.schedule_id == schedule_id)
        .order_by(Shift.start_datetime.asc())
        .all()
    )

    if not employees_with_contracts or not shifts:
        return {
            "assignments_created": [],
            "unfilled_shifts": [],
            "employees_below_target": [],
            "missing_contract_hours_total": 0.0,
            "message": "No employees with active contracts or shifts available for planning",
        }

    assignments_created: list[Assignment] = []
    unfilled_shifts: list[dict[str, Any]] = []

    for shift in shifts:
        existing_assignments = (
            db.query(Assignment)
            .filter(Assignment.shift_id == shift.id)
            .all()
        )
        assigned_employee_ids = {assignment.employee_id for assignment in existing_assignments}

        if len(assigned_employee_ids) >= 1:
            continue

        rejected_employees: list[dict[str, Any]] = []

        candidate_pool = [
            (employee, contract)
            for employee, contract in employees_with_contracts
            if employee.id not in assigned_employee_ids
        ]

        candidate_pool.sort(
            key = lambda candidate: get_candidate_priority(
                db = db,
                employee = candidate[0],
                contract = candidate[1],
                shift = shift,
            ),
            reverse = True,
        )

        assigned = False

        for employee, contract in candidate_pool:
            errors = get_assignment_errors(
                db = db,
                shift = shift,
                employee = employee,
                contract = contract,
            )

            if not errors:
                assignment = Assignment(
                    employee_id = employee.id,
                    shift_id = shift.id,
                )

                db.add(assignment)
                db.flush()

                assignments_created.append(assignment)
                assigned_employee_ids.add(employee.id)
                assigned = True
                break

            rejected_employees.append(
                {
                    "employee_id": employee.id,
                    "employee_name": f"{employee.first_name} {employee.last_name}",
                    "contract_id": contract.id,
                    "errors": errors,
                }
            )

        if not assigned:
            unfilled_shifts.append(
                {
                    "shift_id": shift.id,
                    "start_datetime": shift.start_datetime,
                    "end_datetime": shift.end_datetime,
                    "required_employees": 1,
                    "assigned_employees": 0,
                    "missing_employees": 1,
                    "rejected_employees": rejected_employees,
                }
            )

    for shift in shifts:
        existing_assignments = (
            db.query(Assignment)
            .filter(Assignment.shift_id == shift.id)
            .all()
        )
        assigned_employee_ids = {assignment.employee_id for assignment in existing_assignments}

        candidate_pool = []

        for employee, contract in employees_with_contracts:
            if employee.id in assigned_employee_ids:
                continue

            assigned_hours = get_employee_weekly_assigned_hours(
                db = db,
                employee_id = employee.id,
                reference_datetime = shift.start_datetime,
            )

            remaining_hours = contract.weekly_hours - assigned_hours

            if remaining_hours <= 0:
                continue

            candidate_pool.append((employee, contract))

        candidate_pool.sort(
            key = lambda candidate: get_candidate_priority(
                db = db,
                employee = candidate[0],
                contract = candidate[1],
                shift = shift,
            ),
            reverse = True,
        )

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
            assigned_employee_ids.add(employee.id)

    db.commit()

    reference_shift = shifts[0]
    employees_below_target, missing_contract_hours_total = get_employees_below_target(
        db = db,
        employees_with_contracts = employees_with_contracts,
        reference_shift = reference_shift,
    )

    if missing_contract_hours_total > 0:
        message = (
            "Planning generated successfully. "
            f"Additional shifts covering {missing_contract_hours_total} hours are needed "
            "to fulfill all active contract hours before regenerating planning."
        )
    else:
        message = "Planning generated successfully and all active contract hours were fulfilled"

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
        "message": message,
    }