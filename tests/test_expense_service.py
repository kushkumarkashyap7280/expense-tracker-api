from datetime import date

import pytest

from app.features.expenses.exceptions import ExpenseNotFoundError
from app.features.expenses.schemas import ExpenseCreate, ExpenseUpdate
from app.features.expenses.service import ExpenseService
from tests.conftest import FakeExpenseRepository


@pytest.fixture
def service() -> ExpenseService:
    repo = FakeExpenseRepository()
    return ExpenseService(repository=repo)


def _make_payload(**overrides) -> ExpenseCreate:
    defaults = {
        "title": "Coffee",
        "amount": 4.50,
        "category": "food",
        "date": date(2025, 8, 15),
        "description": None,
    }
    defaults.update(overrides)
    return ExpenseCreate(**defaults)


class TestCreateExpense:
    def test_creates_and_returns_expense(self, service: ExpenseService):
        payload = _make_payload()
        expense = service.create_expense(payload)

        assert expense.title == "Coffee"
        assert expense.amount == 4.50
        assert expense.category == "food"
        assert expense.id

    def test_create_with_description(self, service: ExpenseService):
        payload = _make_payload(description="Morning latte")
        expense = service.create_expense(payload)

        assert expense.description == "Morning latte"


class TestGetExpense:
    def test_get_existing_expense(self, service: ExpenseService):
        created = service.create_expense(_make_payload())
        fetched = service.get_expense(created.id)

        assert fetched.id == created.id
        assert fetched.title == created.title

    def test_get_nonexistent_expense_raises(self, service: ExpenseService):
        with pytest.raises(ExpenseNotFoundError):
            service.get_expense("nonexistent-id")


class TestListExpenses:
    def test_list_empty(self, service: ExpenseService):
        assert service.list_expenses() == []

    def test_list_returns_all(self, service: ExpenseService):
        service.create_expense(_make_payload(title="A"))
        service.create_expense(_make_payload(title="B"))

        result = service.list_expenses()
        assert len(result) == 2

    def test_list_filter_by_category(self, service: ExpenseService):
        service.create_expense(_make_payload(category="food"))
        service.create_expense(_make_payload(category="transport"))

        result = service.list_expenses(category="food")
        assert len(result) == 1
        assert result[0].category == "food"

    def test_list_filter_by_date_range(self, service: ExpenseService):
        service.create_expense(_make_payload(date=date(2025, 8, 1)))
        service.create_expense(_make_payload(date=date(2025, 8, 15)))
        service.create_expense(_make_payload(date=date(2025, 9, 1)))

        result = service.list_expenses(
            date_from=date(2025, 8, 1), date_to=date(2025, 8, 31)
        )
        assert len(result) == 2

    def test_list_pagination(self, service: ExpenseService):
        for i in range(5):
            service.create_expense(_make_payload(title=f"Item {i}"))

        page = service.list_expenses(skip=2, limit=2)
        assert len(page) == 2


class TestUpdateExpense:
    def test_update_existing_expense(self, service: ExpenseService):
        created = service.create_expense(_make_payload(amount=10.0))
        updated = service.update_expense(
            created.id, ExpenseUpdate(amount=20.0)
        )

        assert updated.amount == 20.0
        assert updated.title == "Coffee"

    def test_update_nonexistent_raises(self, service: ExpenseService):
        with pytest.raises(ExpenseNotFoundError):
            service.update_expense("bad-id", ExpenseUpdate(amount=99.0))


class TestDeleteExpense:
    def test_delete_existing_expense(self, service: ExpenseService):
        created = service.create_expense(_make_payload())
        deleted = service.delete_expense(created.id)

        assert deleted.id == created.id
        with pytest.raises(ExpenseNotFoundError):
            service.get_expense(created.id)

    def test_delete_nonexistent_raises(self, service: ExpenseService):
        with pytest.raises(ExpenseNotFoundError):
            service.delete_expense("bad-id")


class TestGetSummary:
    def test_summary_aggregates_by_category(self, service: ExpenseService):
        service.create_expense(
            _make_payload(category="food", amount=10.0, date=date(2025, 8, 5))
        )
        service.create_expense(
            _make_payload(category="food", amount=15.0, date=date(2025, 8, 10))
        )
        service.create_expense(
            _make_payload(
                category="transport", amount=30.0, date=date(2025, 8, 12)
            )
        )

        summary = service.get_summary(year=2025, month=8)

        assert summary.total_spending == 55.0
        assert summary.by_category == {"food": 25.0, "transport": 30.0}

    def test_summary_empty_month(self, service: ExpenseService):
        summary = service.get_summary(year=2025, month=1)

        assert summary.total_spending == 0.0
        assert summary.by_category == {}

    def test_summary_excludes_other_months(self, service: ExpenseService):
        service.create_expense(
            _make_payload(category="food", amount=10.0, date=date(2025, 8, 5))
        )
        service.create_expense(
            _make_payload(
                category="food", amount=99.0, date=date(2025, 9, 5)
            )
        )

        summary = service.get_summary(year=2025, month=8)
        assert summary.total_spending == 10.0

    def test_summary_future_month_raises(self, service: ExpenseService):
        with pytest.raises(ValueError, match="Future year or month not allowed"):
            service.get_summary(year=2099, month=12)


class TestListExpensesByCursor:
    def test_cursor_pagination_flow(self, service: ExpenseService):
        for i in range(15):
            service.create_expense(_make_payload(title=f"Item {i}"))

        page1, next_cursor = service.list_expenses_by_cursor(limit=10)

        assert len(page1) == 10
        assert next_cursor is not None

        page2, next_cursor2 = service.list_expenses_by_cursor(cursor_id=next_cursor, limit=10)

        assert len(page2) == 5
        assert next_cursor2 is None
