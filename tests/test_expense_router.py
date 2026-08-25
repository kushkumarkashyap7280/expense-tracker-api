import pytest
from fastapi.testclient import TestClient

from app.features.expenses.dependencies import get_repository
from app.main import app
from tests.conftest import FakeExpenseRepository


@pytest.fixture
def client():
    test_repo = FakeExpenseRepository()
    app.dependency_overrides[get_repository] = lambda: test_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def _expense_payload(**overrides) -> dict:
    defaults = {
        "title": "Lunch",
        "amount": 12.50,
        "category": "food",
        "date": "2025-08-15",
    }
    defaults.update(overrides)
    return defaults


class TestCreateEndpoint:
    def test_create_returns_201(self, client: TestClient):
        resp = client.post("/expenses", json=_expense_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Lunch"
        assert data["amount"] == 12.50
        assert "id" in data

    def test_create_with_description(self, client: TestClient):
        resp = client.post(
            "/expenses",
            json=_expense_payload(description="Team lunch"),
        )
        assert resp.status_code == 201
        assert resp.json()["description"] == "Team lunch"

    def test_create_missing_required_field_returns_422(self, client: TestClient):
        resp = client.post("/expenses", json={"title": "Oops"})
        assert resp.status_code == 422


class TestListEndpoint:
    def test_list_empty(self, client: TestClient):
        resp = client.get("/expenses")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created_expenses(self, client: TestClient):
        client.post("/expenses", json=_expense_payload(title="A"))
        client.post("/expenses", json=_expense_payload(title="B"))

        resp = client.get("/expenses")
        assert len(resp.json()) == 2

    def test_list_filter_by_category(self, client: TestClient):
        client.post("/expenses", json=_expense_payload(category="food"))
        client.post("/expenses", json=_expense_payload(category="transport"))

        resp = client.get("/expenses", params={"category": "food"})
        data = resp.json()
        assert len(data) == 1
        assert data[0]["category"] == "food"

    def test_list_filter_invalid_date_range_returns_400(self, client: TestClient):
        resp = client.get(
            "/expenses",
            params={"date_from": "2025-08-31", "date_to": "2025-08-01"},
        )
        assert resp.status_code == 400

    def test_list_pagination(self, client: TestClient):
        for i in range(5):
            client.post("/expenses", json=_expense_payload(title=f"E{i}"))

        resp = client.get("/expenses", params={"skip": 1, "limit": 2})
        assert len(resp.json()) == 2


class TestGetByIdEndpoint:
    def test_get_existing(self, client: TestClient):
        create_resp = client.post("/expenses", json=_expense_payload())
        expense_id = create_resp.json()["id"]

        resp = client.get(f"/expenses/{expense_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == expense_id

    def test_get_nonexistent_returns_404(self, client: TestClient):
        resp = client.get("/expenses/does-not-exist")
        assert resp.status_code == 404


class TestUpdateEndpoint:
    def test_update_existing(self, client: TestClient):
        create_resp = client.post("/expenses", json=_expense_payload(amount=10.0))
        expense_id = create_resp.json()["id"]

        resp = client.put(
            f"/expenses/{expense_id}", json={"amount": 25.0}
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 25.0
        assert resp.json()["title"] == "Lunch"

    def test_update_nonexistent_returns_404(self, client: TestClient):
        resp = client.put("/expenses/bad-id", json={"amount": 99.0})
        assert resp.status_code == 404


class TestDeleteEndpoint:
    def test_delete_existing(self, client: TestClient):
        create_resp = client.post("/expenses", json=_expense_payload())
        expense_id = create_resp.json()["id"]

        resp = client.delete(f"/expenses/{expense_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == expense_id

        assert client.get(f"/expenses/{expense_id}").status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient):
        resp = client.delete("/expenses/bad-id")
        assert resp.status_code == 404


class TestSummaryEndpoint:
    def test_summary_aggregation(self, client: TestClient):
        client.post(
            "/expenses",
            json=_expense_payload(category="food", amount=10.0, date="2025-08-05"),
        )
        client.post(
            "/expenses",
            json=_expense_payload(category="food", amount=20.0, date="2025-08-10"),
        )
        client.post(
            "/expenses",
            json=_expense_payload(
                category="transport", amount=15.0, date="2025-08-12"
            ),
        )

        resp = client.get("/expenses/summary", params={"year": 2025, "month": 8})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_spending"] == 45.0
        assert data["by_category"] == {"food": 30.0, "transport": 15.0}

    def test_summary_empty_month(self, client: TestClient):
        resp = client.get("/expenses/summary", params={"year": 2025, "month": 1})
        assert resp.status_code == 200
        assert resp.json()["total_spending"] == 0.0

    def test_summary_future_month_returns_400(self, client: TestClient):
        resp = client.get("/expenses/summary", params={"year": 2099, "month": 12})
        assert resp.status_code == 400

    def test_summary_invalid_month_returns_422(self, client: TestClient):
        resp = client.get("/expenses/summary", params={"year": 2025, "month": 13})
        assert resp.status_code == 422
        resp_zero = client.get("/expenses/summary", params={"year": 2025, "month": 0})
        assert resp_zero.status_code == 422



class TestListExpensesByCursorEndpoint:
    def test_cursor_pagination_http_flow(self, client: TestClient):
        for i in range(15):
            client.post("/expenses", json=_expense_payload(title=f"Expense {i}"))

        resp1 = client.get("/expenses/cursor", params={"limit": 10})
        assert resp1.status_code == 200
        data1 = resp1.json()

        assert len(data1["items"]) == 10
        assert data1["next_cursor"] is not None

        next_cursor = data1["next_cursor"]

        resp2 = client.get("/expenses/cursor", params={"cursor_id": next_cursor, "limit": 10})
        assert resp2.status_code == 200
        data2 = resp2.json()

        assert len(data2["items"]) == 5
        assert data2["next_cursor"] is None

    def test_cursor_invalid_date_range_returns_400(self, client: TestClient):
        resp = client.get(
            "/expenses/cursor",
            params={"date_from": "2025-08-31", "date_to": "2025-08-01"},
        )
        assert resp.status_code == 400
