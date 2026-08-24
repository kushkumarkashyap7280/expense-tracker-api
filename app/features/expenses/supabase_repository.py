from datetime import date

from supabase import Client

from app.features.expenses.models import Expense
from app.features.expenses.repository import ExpenseRepository


class SupabaseExpenseRepository(ExpenseRepository):
    TABLE = "expenses"

    def __init__(self, client: Client) -> None:
        self._client = client

    @staticmethod
    def _row_to_expense(row: dict) -> Expense:
        return Expense(**row)

    @staticmethod
    def _expense_to_row(expense: Expense) -> dict:
        data = expense.model_dump()
        data["date"] = data["date"].isoformat()
        return data

    def create(self, expense: Expense) -> Expense:
        row = self._expense_to_row(expense)
        result = self._client.table(self.TABLE).insert(row).execute()
        return self._row_to_expense(result.data[0])

    def get_by_id(self, expense_id: str) -> Expense | None:
        result = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("id", expense_id)
            .execute()
        )
        if not result.data:
            return None
        return self._row_to_expense(result.data[0])

    def list_all(
        self,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Expense]:
        query = self._client.table(self.TABLE).select("*")

        if category is not None:
            query = query.eq("category", category)
        if date_from is not None:
            query = query.gte("date", date_from.isoformat())
        if date_to is not None:
            query = query.lte("date", date_to.isoformat())

        query = query.range(skip, skip + limit - 1)
        result = query.execute()
        return [self._row_to_expense(row) for row in result.data]

    def update(self, expense_id: str, data: dict) -> Expense | None:
        if "date" in data and isinstance(data["date"], date):
            data["date"] = data["date"].isoformat()

        result = (
            self._client.table(self.TABLE)
            .update(data)
            .eq("id", expense_id)
            .execute()
        )
        if not result.data:
            return None
        return self._row_to_expense(result.data[0])

    def delete(self, expense_id: str) -> Expense | None:
        result = (
            self._client.table(self.TABLE)
            .delete()
            .eq("id", expense_id)
            .execute()
        )
        if not result.data:
            return None
        return self._row_to_expense(result.data[0])

    def get_by_month(self, year: int, month: int) -> list[Expense]:
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)

        result = (
            self._client.table(self.TABLE)
            .select("*")
            .gte("date", first_day.isoformat())
            .lt("date", last_day.isoformat())
            .execute()
        )
        return [self._row_to_expense(row) for row in result.data]
    
    def list_all_by_cursor(
    self,
    cursor_id: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
    ) -> tuple[list[Expense], str | None]:

        query = self._client.table(self.TABLE).select("*")

        
        if category is not None:
            query = query.eq("category", category)

        if date_from is not None:
            query = query.gte("date", date_from.isoformat())

        if date_to is not None:
            query = query.lte("date", date_to.isoformat())
        
        query = query.order("id") 
        if cursor_id is not None:
            query = query.gt("id", cursor_id)
        
        query = query.limit(limit + 1)

        result = query.execute()

        expenses = [self._row_to_expense(row) for row in result.data]
        
        next_cursor = None
        if len(expenses) > limit:
            expenses = expenses[:limit]
            next_cursor = expenses[-1].id
            


        return (expenses, next_cursor )





        
