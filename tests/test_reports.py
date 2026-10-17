from tests.conftest import auth_headers, create_category, create_expense


def load_sample_data(client, headers):
    comida = create_category(client, headers, "Comida")
    transporte = create_category(client, headers, "Transporte")
    create_expense(client, headers, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida)
    create_expense(client, headers, description="Metro", amount=3200, date="2026-10-16", category_id=transporte)
    create_expense(client, headers, description="Mercado", amount=95000, date="2026-09-28", category_id=comida)


def test_summary(client):
    headers = auth_headers(client, "ana@gmail.com")
    load_sample_data(client, headers)

    data = client.get("/reports/summary", headers=headers).json()
    assert data["total"] == 116200
    assert data["count"] == 3
    assert data["average"] == 38733.33
    assert data["largest_expense"]["description"] == "Mercado"


def test_summary_with_date_range(client):
    headers = auth_headers(client, "ana@gmail.com")
    load_sample_data(client, headers)

    data = client.get("/reports/summary", params={"date_from": "2026-10-01"}, headers=headers).json()
    assert data["total"] == 21200
    assert data["count"] == 2


def test_summary_without_expenses(client):
    headers = auth_headers(client, "ana@gmail.com")
    data = client.get("/reports/summary", headers=headers).json()
    assert data["total"] == 0
    assert data["count"] == 0
    assert data["average"] == 0
    assert data["largest_expense"] is None


def test_invalid_date_range_is_rejected(client):
    headers = auth_headers(client, "ana@gmail.com")
    res = client.get(
        "/reports/summary",
        params={"date_from": "2026-12-01", "date_to": "2026-01-01"},
        headers=headers,
    )
    assert res.status_code == 422


def test_by_category(client):
    headers = auth_headers(client, "ana@gmail.com")
    load_sample_data(client, headers)

    data = client.get("/reports/by-category", headers=headers).json()
    assert [row["category"] for row in data] == ["Comida", "Transporte"]  # mayor gasto primero
    assert data[0]["total"] == 113000
    assert data[0]["percentage"] == 97.2
    assert data[1]["total"] == 3200
    assert data[1]["percentage"] == 2.8


def test_monthly_returns_twelve_months(client):
    headers = auth_headers(client, "ana@gmail.com")
    load_sample_data(client, headers)

    data = client.get("/reports/monthly", params={"year": 2026}, headers=headers).json()
    assert len(data) == 12
    by_month = {row["month"]: row for row in data}
    assert by_month["2026-09"]["total"] == 95000
    assert by_month["2026-10"]["total"] == 21200
    assert by_month["2026-10"]["count"] == 2
    assert by_month["2026-01"]["total"] == 0