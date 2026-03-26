from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.shift import Shift
from app.models.assignment import Assignment

def generate_schedule(db: Session, schedule_id: int):
    employees = db.query(Employee).filter(Employee.active == True).all()
    shifts = db.query(Shift).filter(Shift.schedule_id == schedule_id).all()

    if not employees or not shifts:
        return []
    
    assignments_created = []

    employee_index = 0

    for shift in shifts:
        employee = employees[employee_index]

        assignment = Assignment(
            employee_id = employee.id,
            shift_id = shift.id
        )

        db.add(assignment)
        assignments_created.append(assignment)

        employee_index = (employee_index + 1) % len(employees)

    db.commit()
    
    return assignments_created