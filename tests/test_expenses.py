from tests.conftest import auth_headers, create_category, create_expense


def test_create_and_list_expenses(client):
    headers = auth_headers(client, "ana@gmail.com")
    comida = create_category(client, headers, "Comida")
    create_expense(client, headers, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida)
    create_expense(client, headers, description="Mercado", amount=95000, date="2026-09-28", category_id=comida)

    res = client.get("/expenses", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert [e["description"] for e in items] == ["Almuerzo", "Mercado"]  # más reciente primero


def test_filters_by_date_and_category(client):
    headers = auth_headers(client, "ana@gmail.com")
    comida = create_category(client, headers, "Comida")
    transporte = create_category(client, headers, "Transporte")
    create_expense(client, headers, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida)
    create_expense(client, headers, description="Metro", amount=3200, date="2026-10-16", category_id=transporte)
    create_expense(client, headers, description="Mercado", amount=95000, date="2026-09-28", category_id=comida)

    res = client.get("/expenses", params={"date_from": "2026-10-01"}, headers=headers)
    assert len(res.json()) == 2

    res = client.get("/expenses", params={"category_id": transporte}, headers=headers)
    assert [e["description"] for e in res.json()] == ["Metro"]


def test_invalid_amount_is_rejected(client):
    headers = auth_headers(client, "ana@gmail.com")
    comida = create_category(client, headers, "Comida")
    for amount in (-5, 0):
        res = client.post(
            "/expenses",
            json={"description": "Raro", "amount": amount, "date": "2026-10-17", "category_id": comida},
            headers=headers,
        )
        assert res.status_code == 422


def test_update_expense_partially(client):
    headers = auth_headers(client, "ana@gmail.com")
    comida = create_category(client, headers, "Comida")
    expense = create_expense(client, headers, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida)

    res = client.patch(f"/expenses/{expense['id']}", json={"amount": 20000}, headers=headers)
    assert res.status_code == 200
    assert res.json()["amount"] == 20000
    assert res.json()["description"] == "Almuerzo"


def test_delete_expense(client):
    headers = auth_headers(client, "ana@gmail.com")
    comida = create_category(client, headers, "Comida")
    expense = create_expense(client, headers, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida)

    assert client.delete(f"/expenses/{expense['id']}", headers=headers).status_code == 204
    assert client.get(f"/expenses/{expense['id']}", headers=headers).status_code == 404


def test_cannot_delete_category_with_expenses(client):
    headers = auth_headers(client, "ana@gmail.com")
    comida = create_category(client, headers, "Comida")
    expense = create_expense(client, headers, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida)

    assert client.delete(f"/categories/{comida}", headers=headers).status_code == 409

    client.delete(f"/expenses/{expense['id']}", headers=headers)
    assert client.delete(f"/categories/{comida}", headers=headers).status_code == 204


def test_duplicate_category_name_is_rejected(client):
    headers = auth_headers(client, "ana@gmail.com")
    create_category(client, headers, "Comida")
    res = client.post("/categories", json={"name": "comida"}, headers=headers)
    assert res.status_code == 409