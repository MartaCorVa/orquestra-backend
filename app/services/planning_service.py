from typing import Any

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.shift import Shift
from app.services.assignment_validation_service import get_assignment_errors
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


def generate_schedule(db: Session, schedule_id: int, employees_per_shift: int) -> dict[str, Any]:
    schedule = validate_schedule_exists(db = db, schedule_id = schedule_id)

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

    if employees_per_shift <= 0:
        return {
            "assignments_created": [],
            "unfilled_shifts": [],
            "message": "Employees per shift must be greater than 0",
        }

    if not employees_with_contracts or not shifts:
        return {
            "assignments_created": [],
            "unfilled_shifts": [],
            "message": "No employees with active contracts or shifts available for planning",
        }

    assignments_created: list[Assignment] = []
    unfilled_shifts: list[dict[str, Any]] = []
    employee_index = 0
    max_employees_per_shift = min(employees_per_shift, len(employees_with_contracts))

    for shift in shifts:
        existing_assignments = (
            db.query(Assignment)
            .filter(Assignment.shift_id == shift.id)
            .all()
        )
        assigned_employee_ids = {assignment.employee_id for assignment in existing_assignments}

        rejected_employees: list[dict[str, Any]] = []
        attempts = 0
        max_attempts = len(employees_with_contracts) * 2

        while len(assigned_employee_ids) < max_employees_per_shift and attempts < max_attempts:
            employee, contract = employees_with_contracts[employee_index]

            if employee.id not in assigned_employee_ids:
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
                else:
                    rejected_employees.append(
                        {
                            "employee_id": employee.id,
                            "employee_name": f"{employee.first_name} {employee.last_name}",
                            "contract_id": contract.id,
                            "errors": errors,
                        }
                    )

            employee_index = (employee_index + 1) % len(employees_with_contracts)
            attempts += 1

        if len(assigned_employee_ids) < max_employees_per_shift:
            missing_employees = max_employees_per_shift - len(assigned_employee_ids)

            unique_rejected_employees: list[dict[str, Any]] = []
            seen_employee_ids: set[int] = set()

            for rejected_employee in rejected_employees:
                if rejected_employee["employee_id"] not in seen_employee_ids:
                    unique_rejected_employees.append(rejected_employee)
                    seen_employee_ids.add(rejected_employee["employee_id"])

            unfilled_shifts.append(
                {
                    "shift_id": shift.id,
                    "start_datetime": shift.start_datetime,
                    "end_datetime": shift.end_datetime,
                    "required_employees": max_employees_per_shift,
                    "assigned_employees": len(assigned_employee_ids),
                    "missing_employees": missing_employees,
                    "rejected_employees": unique_rejected_employees,
                }
            )

    db.commit()

    return {
        "assignments_created": [
            {
                "shift_id": assignment.shift_id,
                "employee_id": assignment.employee_id,
            }
            for assignment in assignments_created
        ],
        "unfilled_shifts": unfilled_shifts,
        "message": "Planning generated successfully using active contracts",
    }