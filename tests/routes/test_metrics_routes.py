def test_fairness_requires_admin(client, metrics_employee_headers, metrics_data):
    schedule_id = metrics_data["schedule"].id

    response = client.get(
        f"/metrics/fairness/{schedule_id}",
        headers = metrics_employee_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_fairness_returns_404_for_missing_schedule(client, metrics_admin_headers):
    response = client.get(
        "/metrics/fairness/9999",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_fairness_returns_empty_metrics_for_schedule_without_shifts(client, metrics_admin_headers, empty_schedule):
    response = client.get(
        f"/metrics/fairness/{empty_schedule.id}",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["schedule_id"] == empty_schedule.id
    assert data["total_assigned_hours"] == 0
    assert data["employees"] == []
    assert data["max_assigned_hours"] == 0
    assert data["min_assigned_hours"] == 0
    assert data["hours_gap"] == 0
    assert data["max_workload_percentage"] == 0
    assert data["min_workload_percentage"] == 0
    assert data["workload_percentage_gap"] == 0


def test_fairness_returns_metrics_for_schedule_with_assignments(client, metrics_admin_headers, metrics_data):
    schedule_id = metrics_data["schedule"].id

    response = client.get(
        f"/metrics/fairness/{schedule_id}",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["schedule_id"] == schedule_id
    assert data["total_assigned_hours"] == 8.0
    assert len(data["employees"]) == 2
    assert data["max_assigned_hours"] == 4.0
    assert data["min_assigned_hours"] == 4.0
    assert data["hours_gap"] == 0.0
    assert data["max_workload_percentage"] == 20.0
    assert data["min_workload_percentage"] == 10.0
    assert data["workload_percentage_gap"] == 10.0

    first_employee = data["employees"][0]
    second_employee = data["employees"][1]

    assert "contract_weekly_hours" in first_employee
    assert "contract_weekly_hours" in second_employee


def test_workload_requires_authentication(client):
    response = client.get(
        "/metrics/workload?start_date=2026-03-01&end_date=2026-03-07",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_workload_returns_metrics_for_admin(client, metrics_admin_headers, metrics_data):
    response = client.get(
        "/metrics/workload?start_date=2026-03-01&end_date=2026-03-07",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["start_date"] == "2026-03-01"
    assert data["end_date"] == "2026-03-07"
    assert data["total_assigned_hours"] == 8.0
    assert len(data["employees"]) == 2
    assert "contract_weekly_hours" in data["employees"][0]


def test_workload_allows_admin_filter_by_employee(client, metrics_admin_headers, metrics_data):
    employee_id = metrics_data["employee_1"].id

    response = client.get(
        f"/metrics/workload?start_date=2026-03-01&end_date=2026-03-07&employee_id={employee_id}",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["employees"]) == 1
    assert data["employees"][0]["employee_id"] == employee_id
    assert data["employees"][0]["assigned_hours"] == 4.0
    assert data["employees"][0]["contract_weekly_hours"] == 40
    assert data["total_assigned_hours"] == 4.0


def test_workload_employee_only_sees_own_metrics(client, metrics_employee_headers, metrics_data):
    response = client.get(
        "/metrics/workload?start_date=2026-03-01&end_date=2026-03-07",
        headers = metrics_employee_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["employees"]) == 1
    assert data["employees"][0]["employee_id"] == metrics_data["employee_1"].id
    assert data["employees"][0]["assigned_hours"] == 4.0
    assert data["employees"][0]["contract_weekly_hours"] == 40
    assert data["total_assigned_hours"] == 4.0


def test_workload_returns_400_for_invalid_date_range(client, metrics_admin_headers):
    response = client.get(
        "/metrics/workload?start_date=2026-03-10&end_date=2026-03-01",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Start date cannot be later than end date"


def test_fairness_uses_contract_valid_for_shift_date(client, metrics_admin_headers, metrics_data_with_contract_change):
    schedule_id = metrics_data_with_contract_change["schedule"].id

    response = client.get(
        f"/metrics/fairness/{schedule_id}",
        headers = metrics_admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["employees"]) == 1
    assert data["employees"][0]["assigned_hours"] == 4.0
    assert data["employees"][0]["contract_weekly_hours"] == 20
    assert data["employees"][0]["workload_percentage"] == 20.0


def test_workload_uses_contract_valid_for_shift_date(client, metrics_employee_headers, metrics_data_with_contract_change):
    response = client.get(
        "/metrics/workload?start_date=2026-03-01&end_date=2026-03-07",
        headers = metrics_employee_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["employees"]) == 1
    assert data["employees"][0]["assigned_hours"] == 4.0
    assert data["employees"][0]["contract_weekly_hours"] == 20
    assert data["employees"][0]["workload_percentage"] == 20.0