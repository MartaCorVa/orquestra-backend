import datetime

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User


def seed_data():
    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == "admin@orquestra.com").first()
    if existing_user:
        print("Database already seeded")
        db.close()
        return

    users = [
        User(
            email = "admin@orquestra.com",
            password = hash_password("admin123"),
            role = "admin",
            active = True,
            must_change_password = False,
        ),
        User(
            email = "marta@orquestra.com",
            password = hash_password("user123"),
            role = "employee",
            active = True,
            must_change_password = False,
        ),
        User(
            email = "ana@orquestra.com",
            password = hash_password("user123"),
            role = "employee",
            active = True,
            must_change_password = False,
        ),
        User(
            email = "carlos@orquestra.com",
            password = hash_password("user123"),
            role = "employee",
            active = True,
            must_change_password = False,
        ),
    ]

    db.add_all(users)
    db.commit()

    for user in users:
        db.refresh(user)

    admin_user = users[0]
    marta_user = users[1]
    ana_user = users[2]
    carlos_user = users[3]

    employees = [
        Employee(
            first_name = "Marta",
            last_name = "Lopez",
            phone_number = "600123456",
            max_weekly_hours = 40,
            active = True,
            user_id = marta_user.id,
        ),
        Employee(
            first_name = "Juan",
            last_name = "Perez",
            phone_number = "600654321",
            max_weekly_hours = 35,
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Ana",
            last_name = "Garcia",
            phone_number = "611111111",
            max_weekly_hours = 30,
            active = True,
            user_id = ana_user.id,
        ),
        Employee(
            first_name = "Carlos",
            last_name = "Ruiz",
            phone_number = "622222222",
            max_weekly_hours = 40,
            active = True,
            user_id = carlos_user.id,
        ),
        Employee(
            first_name = "Lucia",
            last_name = "Martin",
            phone_number = "633333333",
            max_weekly_hours = 25,
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Sergio",
            last_name = "Navarro",
            phone_number = "644444444",
            max_weekly_hours = 20,
            active = False,
            user_id = None,
        ),
    ]

    db.add_all(employees)
    db.commit()

    for employee in employees:
        db.refresh(employee)

    marta_employee = employees[0]
    juan_employee = employees[1]
    ana_employee = employees[2]
    carlos_employee = employees[3]
    lucia_employee = employees[4]

    schedules = [
        Schedule(
            start_date = datetime.date(2026, 3, 25),
            end_date = datetime.date(2026, 3, 31),
            status = "published",
        ),
        Schedule(
            start_date = datetime.date(2026, 4, 1),
            end_date = datetime.date(2026, 4, 7),
            status = "draft",
        ),
        Schedule(
            start_date = datetime.date(2026, 4, 8),
            end_date = datetime.date(2026, 4, 14),
            status = "generated",
        ),
    ]

    db.add_all(schedules)
    db.commit()

    for schedule in schedules:
        db.refresh(schedule)

    schedule_1 = schedules[0]
    schedule_2 = schedules[1]
    schedule_3 = schedules[2]

    shifts = [
        Shift(
            start_datetime = datetime.datetime(2026, 3, 25, 8, 0, 0),
            end_datetime = datetime.datetime(2026, 3, 25, 14, 0, 0),
            creation_type = "manual",
            status = "assigned",
            schedule_id = schedule_1.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 3, 26, 15, 0, 0),
            end_datetime = datetime.datetime(2026, 3, 26, 21, 0, 0),
            creation_type = "manual",
            status = "assigned",
            schedule_id = schedule_1.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 3, 27, 22, 0, 0),
            end_datetime = datetime.datetime(2026, 3, 28, 4, 0, 0),
            creation_type = "automatic",
            status = "planned",
            schedule_id = schedule_1.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 3, 29, 9, 0, 0),
            end_datetime = datetime.datetime(2026, 3, 29, 13, 0, 0),
            creation_type = "manual",
            status = "assigned",
            schedule_id = schedule_1.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 4, 1, 8, 0, 0),
            end_datetime = datetime.datetime(2026, 4, 1, 14, 0, 0),
            creation_type = "manual",
            status = "planned",
            schedule_id = schedule_2.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 4, 2, 14, 0, 0),
            end_datetime = datetime.datetime(2026, 4, 2, 20, 0, 0),
            creation_type = "automatic",
            status = "planned",
            schedule_id = schedule_2.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 4, 3, 22, 0, 0),
            end_datetime = datetime.datetime(2026, 4, 4, 6, 0, 0),
            creation_type = "automatic",
            status = "planned",
            schedule_id = schedule_2.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 4, 8, 7, 0, 0),
            end_datetime = datetime.datetime(2026, 4, 8, 13, 0, 0),
            creation_type = "manual",
            status = "assigned",
            schedule_id = schedule_3.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 4, 9, 13, 0, 0),
            end_datetime = datetime.datetime(2026, 4, 9, 19, 0, 0),
            creation_type = "manual",
            status = "assigned",
            schedule_id = schedule_3.id,
        ),
        Shift(
            start_datetime = datetime.datetime(2026, 4, 10, 21, 0, 0),
            end_datetime = datetime.datetime(2026, 4, 11, 3, 0, 0),
            creation_type = "automatic",
            status = "cancelled",
            schedule_id = schedule_3.id,
        ),
    ]

    db.add_all(shifts)
    db.commit()

    for shift in shifts:
        db.refresh(shift)

    assignments = [
        Assignment(
            employee_id = marta_employee.id,
            shift_id = shifts[0].id,
        ),
        Assignment(
            employee_id = juan_employee.id,
            shift_id = shifts[0].id,
        ),
        Assignment(
            employee_id = ana_employee.id,
            shift_id = shifts[1].id,
        ),
        Assignment(
            employee_id = carlos_employee.id,
            shift_id = shifts[1].id,
        ),
        Assignment(
            employee_id = lucia_employee.id,
            shift_id = shifts[3].id,
        ),
        Assignment(
            employee_id = marta_employee.id,
            shift_id = shifts[7].id,
        ),
        Assignment(
            employee_id = juan_employee.id,
            shift_id = shifts[8].id,
        ),
    ]

    db.add_all(assignments)
    db.commit()

    db.close()
    print("Seed completed successfully")


if __name__ == "__main__":
    seed_data()