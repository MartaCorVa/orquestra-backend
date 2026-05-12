import datetime

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.assignment import Assignment
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.schedule import Schedule
from app.models.shift import Shift
from app.models.user import User


def create_shift(db, schedule, start_date, start_time, end_date, end_time, status):
    shift = Shift(
        start_datetime = datetime.datetime.combine(start_date, start_time),
        end_datetime = datetime.datetime.combine(end_date, end_time),
        creation_type = "manual" if schedule.status == "published" else "automatic",
        status = status,
        schedule_id = schedule.id,
    )

    db.add(shift)
    db.commit()
    db.refresh(shift)

    return shift


def seed_data():
    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == "admin@orquestra.com").first()
    if existing_user:
        print("Database already seeded")
        db.close()
        return

    users = [
        User(email = "admin@orquestra.com", password = hash_password("admin123"), role = "admin", active = True, must_change_password = False),
        User(email = "marta@orquestra.com", password = hash_password("user123"), role = "employee", active = True, must_change_password = False),
        User(email = "ana@orquestra.com", password = hash_password("user123"), role = "employee", active = True, must_change_password = False),
        User(email = "carlos@orquestra.com", password = hash_password("user123"), role = "employee", active = True, must_change_password = False),
    ]

    db.add_all(users)
    db.commit()

    for user in users:
        db.refresh(user)

    employees = [
        Employee(first_name = "Marta", last_name = "Lopez", phone_number = "600123456", active = True, user_id = users[1].id),
        Employee(first_name = "Juan", last_name = "Perez", phone_number = "600654321", active = True, user_id = None),
        Employee(first_name = "Ana", last_name = "Garcia", phone_number = "611111111", active = True, user_id = users[2].id),
        Employee(first_name = "Carlos", last_name = "Ruiz", phone_number = "622222222", active = True, user_id = users[3].id),
        Employee(first_name = "Lucia", last_name = "Martin", phone_number = "633333333", active = True, user_id = None),
        Employee(first_name = "Sergio", last_name = "Navarro", phone_number = "644444444", active = False, user_id = None),
    ]

    db.add_all(employees)
    db.commit()

    for employee in employees:
        db.refresh(employee)

    marta, juan, ana, carlos, lucia, sergio = employees

    contracts = [
        Contract(
            employee_id = marta.id,
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
            start_date = datetime.date(2026, 5, 1),
            end_date = None
        ),
        Contract(
            employee_id = juan.id,
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
            start_date = datetime.date(2026, 5, 1),
            end_date = None,
        ),
        Contract(
            employee_id = ana.id,
            weekly_hours = 12,
            daily_hours = 6,
            min_days_off_per_week = 5,
            work_monday = False,
            work_tuesday = False,
            work_wednesday = False,
            work_thursday = False,
            work_friday = False,
            work_saturday = True,
            work_sunday = True,
            has_fixed_schedule = False,
            preferred_start_time = None,
            preferred_end_time = None,
            active = True,
            start_date = datetime.date(2026, 5, 1),
            end_date = None
        ),
        Contract(
            employee_id = carlos.id,
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
            preferred_start_time = datetime.time(22, 0),
            preferred_end_time = datetime.time(6, 0),
            active = True,
            start_date = datetime.date(2026, 5, 1),
            end_date = None
        ),
        Contract(
            employee_id = lucia.id,
            weekly_hours = 25,
            daily_hours = 5,
            min_days_off_per_week = 2,
            work_monday = False,
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
            start_date = datetime.date(2026, 5, 1),
            end_date = None
        ),
        Contract(
            employee_id = sergio.id,
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
            start_date = datetime.date(2026, 5, 1),
            end_date = None
        ),
    ]

    db.add_all(contracts)
    db.commit()

    schedules = [
        Schedule(start_date = datetime.date(2026, 5, 4), end_date = datetime.date(2026, 5, 10), status = "published"),
        Schedule(start_date = datetime.date(2026, 5, 11), end_date = datetime.date(2026, 5, 17), status = "generated"),
        Schedule(start_date = datetime.date(2026, 5, 18), end_date = datetime.date(2026, 5, 24), status = "draft"),
        Schedule(start_date = datetime.date(2026, 5, 25), end_date = datetime.date(2026, 5, 31), status = "draft"),
    ]

    db.add_all(schedules)
    db.commit()

    for schedule in schedules:
        db.refresh(schedule)

    for schedule in schedules:
        should_assign = schedule.status in ["published", "generated"]
        shift_status = "assigned" if should_assign else "planned"

        current_date = schedule.start_date

        while current_date <= schedule.end_date:
            weekday = current_date.weekday()

            if weekday < 5:
                day_shift = create_shift(
                    db,
                    schedule,
                    current_date,
                    datetime.time(8, 0),
                    current_date,
                    datetime.time(16, 0),
                    shift_status,
                )

                night_shift = create_shift(
                    db,
                    schedule,
                    current_date,
                    datetime.time(22, 0),
                    current_date + datetime.timedelta(days = 1),
                    datetime.time(6, 0),
                    shift_status,
                )

                if should_assign:
                    db.add_all([
                        Assignment(shift_id = day_shift.id, employee_id = marta.id),
                        Assignment(shift_id = day_shift.id, employee_id = juan.id),
                        Assignment(shift_id = night_shift.id, employee_id = carlos.id),
                    ])

            
            if weekday in [5, 6]:
                ana_shift = create_shift(
                    db,
                    schedule,
                    current_date,
                    datetime.time(9, 0),
                    current_date,
                    datetime.time(15, 0),
                    shift_status,
                )

                if should_assign:
                    db.add(
                        Assignment(
                            shift_id = ana_shift.id,
                            employee_id = ana.id,
                        )
                    )

                    
            is_last_schedule = schedule.start_date == datetime.date(2026, 5, 25)

            if weekday in [1, 2, 3, 4, 5] and not (
                is_last_schedule and weekday == 5
            ):
                lucia_shift = create_shift(
                    db,
                    schedule,
                    current_date,
                    datetime.time(10, 0),
                    current_date,
                    datetime.time(15, 0),
                    shift_status,
                )

                if should_assign:
                    db.add(
                        Assignment(
                            shift_id = lucia_shift.id,
                            employee_id = lucia.id,
                        )
                    )

            current_date += datetime.timedelta(days = 1)

        db.commit()

    db.close()
    print("Seed completed successfully")


if __name__ == "__main__":
    seed_data()