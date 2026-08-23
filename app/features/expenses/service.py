from datetime import date
from uuid import uuid4

from app.features.expenses.exceptions import ExpenseNotFoundError
from app.features.expenses.models import Expense
from app.features.expenses.repository import ExpenseRepository
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseSummaryResponse,
    ExpenseUpdate,
)


class ExpenseService:
    def __init__(self, repository: ExpenseRepository) -> None:
        self._repo = repository

    def create_expense(self, payload: ExpenseCreate) -> Expense:
        expense = Expense(id=str(uuid4()), **payload.model_dump())
        return self._repo.create(expense)

    def update_expense(self, expense_id: str, payload: ExpenseUpdate) -> Expense:
        data = payload.model_dump(exclude_unset=True)
        updated = self._repo.update(expense_id, data)
        if updated is None:
            raise ExpenseNotFoundError(expense_id)
        return updated

    def delete_expense(self, expense_id: str) -> Expense:
        deleted = self._repo.delete(expense_id)
        if deleted is None:
            raise ExpenseNotFoundError(expense_id)
        return deleted

    def get_expense(self, expense_id: str) -> Expense:
        expense = self._repo.get_by_id(expense_id)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        return expense

    def list_expenses(
        self,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Expense]:
        return self._repo.list_all(
            category=category,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
        )

    def get_summary(self, year: int, month: int) -> ExpenseSummaryResponse:
        today = date.today()
        if year > today.year or (year == today.year and month > today.month):
            raise ValueError("Future year or month not allowed")

        expenses = self._repo.get_by_month(year, month)

        by_category: dict[str, float] = {}
        for expense in expenses:
            by_category[expense.category] = round(
                by_category.get(expense.category, 0.0) + expense.amount, 2
            )

        return ExpenseSummaryResponse(
            total_spending=round(sum(by_category.values()), 2),
            by_category=by_category,
        )
