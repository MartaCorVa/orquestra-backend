from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.shift import Shift
from app.models.assignment import Assignment

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

        while len(assigned_employee_ids) < max_employees_per_shift:
            employee = employees[employee_index]

            if employee.id not in assigned_employee_ids:
                assignment = Assignment(
                    employee_id = employee.id,
                    shift_id = shift.id
                )

                db.add(assignment)
                assignments_created.append(assignment)
                assigned_employee_ids.add(employee.id)

            employee_index = (employee_index + 1) % len(employees)
            
            if len(assigned_employee_ids) == len(employees):
                break

        
    db.commit()
    
    return assignments_created