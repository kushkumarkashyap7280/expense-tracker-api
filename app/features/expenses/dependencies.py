from fastapi import Depends
from supabase import Client

from app.database.supabase_client import get_supabase_client
from app.features.expenses.repository import ExpenseRepository
from app.features.expenses.service import ExpenseService
from app.features.expenses.supabase_repository import SupabaseExpenseRepository


def get_repository(
    client: Client = Depends(get_supabase_client),
) -> ExpenseRepository:
    return SupabaseExpenseRepository(client)


def get_expense_service(
    repo: ExpenseRepository = Depends(get_repository),
) -> ExpenseService:
    return ExpenseService(repository=repo)
