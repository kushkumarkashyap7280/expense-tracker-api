from abc import ABC, abstractmethod
from uuid import uuid4
from datetime import date

from app.features.expenses.models import Expense


class ExpenseRepository(ABC):
    @abstractmethod
    def create(self, expense: Expense) -> Expense:
        ...

    @abstractmethod
    def get_by_id(self, expense_id: str) -> Expense | None:
        ...

    @abstractmethod
    def list_all(
        self,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Expense]:
        ...

    @abstractmethod
    def update(self, expense_id: str, data: dict) -> Expense | None:
        ...

    @abstractmethod
    def delete(self, expense_id: str) -> Expense | None:
        ...

    @abstractmethod
    def get_by_month(self, year: int, month: int) -> list[Expense]:
        ...

# ---------------------------------------------
    @abstractmethod
    def list_all_by_cursor(
        self,
        cursor_id : str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit : int = 10
    ) ->  tuple[list[Expense], str | None]:
        ...

# ----------------------------------------------
