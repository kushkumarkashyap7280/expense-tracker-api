"""
Shared test fixtures — provides a FakeExpenseRepository that satisfies the
abstract interface for testing without hitting Supabase.
"""

from datetime import date

import pytest

from app.features.expenses.models import Expense
from app.features.expenses.repository import ExpenseRepository


class FakeExpenseRepository(ExpenseRepository):
    """Test-only in-memory implementation of ExpenseRepository."""

    def __init__(self) -> None:
        self._store: list[dict] = []

    def create(self, expense: Expense) -> Expense:
        self._store.append(expense.model_dump())
        return expense

    def get_by_id(self, expense_id: str) -> Expense | None:
        for record in self._store:
            if record["id"] == expense_id:
                return Expense(**record)
        return None

    def list_all(
        self,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Expense]:
        results = self._store

        if category is not None:
            results = [r for r in results if r["category"] == category]
        if date_from is not None:
            results = [r for r in results if r["date"] >= date_from]
        if date_to is not None:
            results = [r for r in results if r["date"] <= date_to]

        results = results[skip : skip + limit]
        return [Expense(**r) for r in results]

    def update(self, expense_id: str, data: dict) -> Expense | None:
        for index, record in enumerate(self._store):
            if record["id"] == expense_id:
                merged = {**record, **data}
                expense = Expense(**merged)
                self._store[index] = expense.model_dump()
                return expense
        return None

    def delete(self, expense_id: str) -> Expense | None:
        for index, record in enumerate(self._store):
            if record["id"] == expense_id:
                removed = self._store.pop(index)
                return Expense(**removed)
        return None

    def get_by_month(self, year: int, month: int) -> list[Expense]:
        return [
            Expense(**r)
            for r in self._store
            if r["date"].year == year and r["date"].month == month
        ]
