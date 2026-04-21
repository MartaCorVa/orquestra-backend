import datetime

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.assignment import Assignment
from app.models.contract import Contract
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

    marta_user = users[1]
    ana_user = users[2]
    carlos_user = users[3]

    employees = [
        Employee(
            first_name = "Marta",
            last_name = "Lopez",
            phone_number = "600123456",
            active = True,
            user_id = marta_user.id,
        ),
        Employee(
            first_name = "Juan",
            last_name = "Perez",
            phone_number = "600654321",
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Ana",
            last_name = "Garcia",
            phone_number = "611111111",
            active = True,
            user_id = ana_user.id,
        ),
        Employee(
            first_name = "Carlos",
            last_name = "Ruiz",
            phone_number = "622222222",
            active = True,
            user_id = carlos_user.id,
        ),
        Employee(
            first_name = "Lucia",
            last_name = "Martin",
            phone_number = "633333333",
            active = True,
            user_id = None,
        ),
        Employee(
            first_name = "Sergio",
            last_name = "Navarro",
            phone_number = "644444444",
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
    sergio_employee = employees[5]

    contracts = [
        Contract(
            employee_id = marta_employee.id,
            weekly_hours = 40,
            daily_hours = 8,
            min_days_off_per_week = 2,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = False,
            work_sunday = False,
            has_fixed_schedule = True,
            preferred_start_time = datetime.time(8, 0),
            preferred_end_time = datetime.time(16, 0),
            active = True,
            start_date = datetime.date(2026, 4, 1),
            end_date = None,
        ),
        Contract(
            employee_id = juan_employee.id,
            weekly_hours = 35,
            daily_hours = 7,
            min_days_off_per_week = 1,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = True,
            work_sunday = False,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = datetime.date(2026, 4, 1),
            end_date = None,
        ),
        Contract(
            employee_id = ana_employee.id,
            weekly_hours = 30,
            daily_hours = 6,
            min_days_off_per_week = 1,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = True,
            work_sunday = False,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = datetime.date(2026, 4, 1),
            end_date = None,
        ),
        Contract(
            employee_id = carlos_employee.id,
            weekly_hours = 40,
            daily_hours = 8,
            min_days_off_per_week = 2,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = False,
            work_sunday = False,
            has_fixed_schedule = True,
            preferred_start_time = datetime.time(8, 0),
            preferred_end_time = datetime.time(16, 0),
            active = True,
            start_date = datetime.date(2026, 4, 1),
            end_date = None,
        ),
        Contract(
            employee_id = lucia_employee.id,
            weekly_hours = 25,
            daily_hours = 5,
            min_days_off_per_week = 1,
            work_monday = False,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = True,
            work_sunday = True,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = datetime.date(2026, 4, 1),
            end_date = None,
        ),
        Contract(
            employee_id = sergio_employee.id,
            weekly_hours = 20,
            daily_hours = 4,
            min_days_off_per_week = 2,
            work_monday = True,
            work_tuesday = True,
            work_wednesday = True,
            work_thursday = True,
            work_friday = True,
            work_saturday = False,
            work_sunday = False,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = False,
            start_date = datetime.date(2026, 4, 1),
            end_date = None,
        ),
    ]

    db.add_all(contracts)
    db.commit()

    schedules = [
        Schedule(
            start_date = datetime.date(2026, 3, 30),
            end_date = datetime.date(2026, 4, 5),
            status = "published",
        ),
        Schedule(
            start_date = datetime.date(2026, 4, 6),
            end_date = datetime.date(2026, 4, 12),
            status = "draft",
        ),
        Schedule(
            start_date = datetime.date(2026, 4, 13),
            end_date = datetime.date(2026, 4, 19),
            status = "generated",
        ),
        Schedule(
            start_date = datetime.date(2026, 4, 20),
            end_date = datetime.date(2026, 4, 26),
            status = "published",
        ),
        Schedule(
            start_date = datetime.date(2026, 4, 27),
            end_date = datetime.date(2026, 5, 3),
            status = "draft",
        ),
    ]

    db.add_all(schedules)
    db.commit()

    for schedule in schedules:
        db.refresh(schedule)

    shifts = []

    for schedule in schedules:
        current_date = schedule.start_date

        while current_date <= schedule.end_date:
            if current_date.month == 4 or (
                schedule.start_date == datetime.date(2026, 3, 30)
                and current_date in [datetime.date(2026, 4, 1), datetime.date(2026, 4, 2), datetime.date(2026, 4, 3), datetime.date(2026, 4, 4), datetime.date(2026, 4, 5)]
            ):
                if current_date.weekday() < 5:
                    shifts.append(
                        Shift(
                            start_datetime = datetime.datetime.combine(current_date, datetime.time(8, 0)),
                            end_datetime = datetime.datetime.combine(current_date, datetime.time(16, 0)),
                            creation_type = "manual" if schedule.status == "published" else "automatic",
                            status = "assigned" if schedule.status == "published" else "planned",
                            schedule_id = schedule.id,
                        )
                    )
                else:
                    shifts.append(
                        Shift(
                            start_datetime = datetime.datetime.combine(current_date, datetime.time(8, 0)),
                            end_datetime = datetime.datetime.combine(current_date, datetime.time(13, 0)),
                            creation_type = "manual" if schedule.status == "published" else "automatic",
                            status = "assigned" if schedule.status == "published" else "planned",
                            schedule_id = schedule.id,
                        )
                    )

            current_date += datetime.timedelta(days = 1)

    db.add_all(shifts)
    db.commit()

    for shift in shifts:
        db.refresh(shift)


    db.close()
    print("Seed completed successfully")


if __name__ == "__main__":
    seed_data()