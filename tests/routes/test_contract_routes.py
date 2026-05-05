from datetime import date

from app.models.contract import Contract


def build_contract_payload(employee_id):
    return {
        "employee_id": employee_id,
        "weekly_hours": 40,
        "daily_hours": 8,
        "min_days_off_per_week": 2,
        "work_monday": True,
        "work_tuesday": True,
        "work_wednesday": True,
        "work_thursday": True,
        "work_friday": True,
        "work_saturday": False,
        "work_sunday": False,
        "has_fixed_schedule": False,
        "preferred_start_time": None,
        "preferred_end_time": None,
        "active": True,
        "start_date": "2026-04-01",
        "end_date": None,
    }


def test_create_contract_requires_admin(client, employee_auth_headers, active_employees):
    payload = build_contract_payload(active_employees[0].id)

    response = client.post(
        "/contracts/",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_contract_success(client, auth_headers, active_employees):
    payload = build_contract_payload(active_employees[0].id)

    response = client.post(
        "/contracts/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_id"] == active_employees[0].id
    assert data["weekly_hours"] == 40
    assert data["daily_hours"] == 8
    assert data["active"] is True


def test_create_contract_returns_400_when_employee_does_not_exist(client, auth_headers):
    payload = build_contract_payload(9999)

    response = client.post(
        "/contracts/",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Employee does not exist"


def test_get_employee_contracts_returns_contracts(client, auth_headers, active_employees):
    employee = active_employees[0]

    response = client.get(
        f"/contracts/employee/{employee.id}",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_employee_contracts_returns_404_when_employee_does_not_exist(client, auth_headers):
    response = client.get(
        "/contracts/employee/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


def test_get_active_contract_returns_contract(client, auth_headers, active_employees):
    employee = active_employees[0]

    response = client.get(
        f"/contracts/employee/{employee.id}/active",
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["employee_id"] == employee.id
    assert data["active"] is True


def test_get_active_contract_returns_404_when_employee_does_not_exist(client, auth_headers):
    response = client.get(
        "/contracts/employee/9999/active",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


def test_get_active_contract_returns_404_when_active_contract_does_not_exist(
    client,
    auth_headers,
    db,
    active_employees,
):
    employee = active_employees[0]

    db.query(Contract).filter(Contract.employee_id == employee.id).update({"active": False})
    db.commit()

    response = client.get(
        f"/contracts/employee/{employee.id}/active",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active contract not found"


def test_get_contract_returns_contract(client, auth_headers, db, active_employees):
    employee = active_employees[0]
    contract = db.query(Contract).filter(Contract.employee_id == employee.id).first()

    response = client.get(
        f"/contracts/{contract.id}",
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == contract.id
    assert data["employee_id"] == employee.id


def test_get_contract_returns_404_when_contract_does_not_exist(client, auth_headers):
    response = client.get(
        "/contracts/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contract not found"


def test_update_contract_requires_admin(client, employee_auth_headers, db, active_employees):
    employee = active_employees[0]
    contract = db.query(Contract).filter(Contract.employee_id == employee.id).first()

    payload = {
        "weekly_hours": 35,
    }

    response = client.put(
        f"/contracts/{contract.id}",
        json = payload,
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_update_contract_success(client, auth_headers, db, active_employees):
    employee = active_employees[0]
    contract = db.query(Contract).filter(Contract.employee_id == employee.id).first()

    payload = {
        "weekly_hours": 35,
    }

    response = client.put(
        f"/contracts/{contract.id}",
        json = payload,
        headers = auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == contract.id
    assert data["weekly_hours"] == 35


def test_update_contract_returns_404_when_contract_does_not_exist(client, auth_headers):
    response = client.put(
        "/contracts/9999",
        json = {"weekly_hours": 35},
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contract not found"


def test_activate_contract_requires_admin(client, employee_auth_headers, db, active_employees):
    employee = active_employees[0]
    contract = db.query(Contract).filter(Contract.employee_id == employee.id).first()

    response = client.patch(
        f"/contracts/{contract.id}/activate",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_activate_contract_success(client, auth_headers, db, active_employees):
    employee = active_employees[0]

    inactive_contract = Contract(
        employee_id = employee.id,
        weekly_hours = 30,
        daily_hours = 6,
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
        start_date = date(2026, 5, 1),
        end_date = None,
    )

    db.add(inactive_contract)
    db.commit()
    db.refresh(inactive_contract)

    response = client.patch(
        f"/contracts/{inactive_contract.id}/activate",
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["active"] is True


def test_activate_contract_returns_404_when_contract_does_not_exist(client, auth_headers):
    response = client.patch(
        "/contracts/9999/activate",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contract not found"


def test_delete_contract_requires_admin(client, employee_auth_headers, db, active_employees):
    employee = active_employees[0]
    contract = db.query(Contract).filter(Contract.employee_id == employee.id).first()

    response = client.delete(
        f"/contracts/{contract.id}",
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_delete_contract_success(client, auth_headers, db, active_employees):
    employee = active_employees[0]
    contract = db.query(Contract).filter(Contract.employee_id == employee.id).first()

    response = client.delete(
        f"/contracts/{contract.id}",
        headers = auth_headers,
    )

    assert response.status_code == 204


def test_delete_contract_returns_404_when_contract_does_not_exist(client, auth_headers):
    response = client.delete(
        "/contracts/9999",
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contract not found"