def test_generate_planning_requires_admin(client, employee_auth_headers, test_schedule):
    response = client.post(
        f"/planning/generate/{test_schedule.id}",
        json = {"employees_per_shift": 1},
        headers = employee_auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_generate_planning_creates_assignments(client, auth_headers, test_schedule, active_employees, test_shifts):
    response = client.post(
        f"/planning/generate/{test_schedule.id}",
        json = {"employees_per_shift": 1},
        headers = auth_headers,
    )

    assert response.status_code == 200
    assert "assignments_created" in response.json()
    assert len(response.json()["assignments_created"]) == 2
    assert response.json()["unfilled_shifts"] == []


def test_generate_planning_returns_404_for_missing_schedule(client, auth_headers):
    response = client.post(
        "/planning/generate/9999",
        json = {"employees_per_shift": 1},
        headers = auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"