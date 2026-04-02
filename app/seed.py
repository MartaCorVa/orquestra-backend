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

    user1 = User(
        email = "admin@orquestra.com",
        password = hash_password("admin123"),
        role = "admin",
        active = True,
        must_change_password = False
    )
    user2 = User(
        email = "user@orquestra.com",
        password = hash_password("user123"),
        role = "employee",
        active = True,
        must_change_password = False
    )

    db.add_all([user1, user2])
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    employee1 = Employee(
        first_name = "Marta",
        last_name = "Lopez",
        phone_number = "600123456",
        max_weekly_hours = 40,
        active = True,
        user_id = user2.id
    )
    employee2 = Employee(
        first_name = "Juan",
        last_name = "Perez",
        phone_number = "600654321",
        max_weekly_hours = 35,
        active = True,
        user_id = None
    )

    db.add_all([employee1, employee2])
    db.commit()
    db.refresh(employee1)
    db.refresh(employee2)

    schedule = Schedule(
        start_date = datetime.date(2026, 3, 25),
        end_date = datetime.date(2026, 3, 31),
        status = "generated"
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    shift1 = Shift(
        date = datetime.date(2026, 3, 25),
        start_time = datetime.time(8, 0, 0),
        end_time = datetime.time(14, 0, 0),
        creation_type = "manual",
        status = "pending",
        schedule_id = schedule.id
    )

    db.add(shift1)
    db.commit()
    db.refresh(shift1)

    assignment1 = Assignment(
        employee_id = employee1.id,
        shift_id = shift1.id
    )
    assignment2 = Assignment(
        employee_id = employee2.id,
        shift_id = shift1.id
    )

    db.add_all([assignment1, assignment2])
    db.commit()

    db.close()
    print("Seed completed successfully")


if __name__ == "__main__":
    seed_data()