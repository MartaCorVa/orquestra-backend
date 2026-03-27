from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.shift import Shift
from app.models.assignment import Assignment


def has_overlapping_shift(db: Session, employee_id: int, shift: Shift) -> bool:
    employee_assignments = (
        db.query(Assignment)
        .join(Shift, Assignment.shift_id == Shift.id)
        .filter(
            Assignment.employee_id == employee_id,
            Shift.date == shift.date
        )
        .all()
    )

    for assignment in employee_assignments:
        assignment_shift = db.query(Shift).filter(Shift.id == assignment.shift_id).first()

        if assignment_shift.start_time < shift.end_time and shift.start_time < assignment_shift.end_time:
            return True
        
    return False


def generate_schedule(db: Session, schedule_id: int, employees_per_shift: int):
    employees = db.query(Employee).filter(Employee.active == True).all()
    shifts = db.query(Shift).filter(Shift.schedule_id == schedule_id).all()

    if not employees or not shifts:
        return []
    
    assignments_created = []
    employee_index = 0
    max_employees_per_shift = min(employees_per_shift, len(employees))

    for shift in shifts:
        existing_assignments = db.query(Assignment).filter(Assignment.shift_id == shift.id).all()
        assigned_employee_ids = {assignment.employee_id for assignment in existing_assignments}

        attempts = 0
        max_attempts = len(employees) * 2

        while len(assigned_employee_ids) < max_employees_per_shift and attempts < max_attempts:
            employee = employees[employee_index]

            if (
                employee.id not in assigned_employee_ids
                and not has_overlapping_shift(db, employee.id, shift)
            ):
                assignment = Assignment(
                    employee_id = employee.id,
                    shift_id = shift.id
                )

                db.add(assignment)
                assignments_created.append(assignment)
                assigned_employee_ids.add(employee.id)

            employee_index = (employee_index + 1) % len(employees)
            attempts += 1
            
    db.commit()
    
    return assignments_created