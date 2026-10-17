from tests.conftest import auth_headers, create_category, create_expense


def test_user_cannot_see_or_touch_another_users_data(client):
    ana = auth_headers(client, "ana@gmail.com")
    beto = auth_headers(client, "beto@gmail.com")

    comida_ana = create_category(client, ana, "Comida")
    expense = create_expense(client, ana, description="Almuerzo", amount=18000, date="2026-10-17", category_id=comida_ana)

    # Beto no ve nada de Ana
    assert client.get("/expenses", headers=beto).json() == []
    assert client.get("/categories", headers=beto).json() == []

    # Beto no puede leer, editar ni borrar el gasto de Ana (404, no revela que existe)
    assert client.get(f"/expenses/{expense['id']}", headers=beto).status_code == 404
    assert client.patch(f"/expenses/{expense['id']}", json={"amount": 1}, headers=beto).status_code == 404
    assert client.delete(f"/expenses/{expense['id']}", headers=beto).status_code == 404

    # Beto no puede usar la categoría de Ana
    res = client.post(
        "/expenses",
        json={"description": "Intruso", "amount": 100, "date": "2026-10-17", "category_id": comida_ana},
        headers=beto,
    )
    assert res.status_code == 404
    assert client.delete(f"/categories/{comida_ana}", headers=beto).status_code == 404

    # Los reportes de Beto no incluyen los gastos de Ana
    summary = client.get("/reports/summary", headers=beto).json()
    assert summary["total"] == 0
    assert summary["count"] == 0
    assert client.get("/reports/by-category", headers=beto).json() == []

    # Y el gasto de Ana sigue intacto
    assert client.get(f"/expenses/{expense['id']}", headers=ana).json()["amount"] == 18000