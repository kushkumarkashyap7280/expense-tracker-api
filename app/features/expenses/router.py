from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.features.expenses.dependencies import get_expense_service
from app.features.expenses.exceptions import ExpenseNotFoundError
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummaryResponse,
    ExpenseUpdate,
    ExpenseCursorResponse
)
from app.features.expenses.service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense(
    payload: ExpenseCreate,
    service: ExpenseService = Depends(get_expense_service),
):
    expense = service.create_expense(payload)
    return expense


@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_summary(
    year: int,
    month: int,
    service: ExpenseService = Depends(get_expense_service),
):
    try:
        return service.get_summary(year, month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 100,
    service: ExpenseService = Depends(get_expense_service),
):
    return service.list_expenses(
        category=category,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )



@router.get("/cursor", response_model=ExpenseCursorResponse)
def list_expenses_by_cursor(
    cursor_id: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
    service: ExpenseService = Depends(get_expense_service),
):
    expenses, next_cursor = service.list_expenses_by_cursor(
        cursor_id=cursor_id,
        category=category,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return {
        "items": expenses,
        "next_cursor": next_cursor,
    }


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
):
    try:
        return service.get_expense(expense_id)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found")


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    service: ExpenseService = Depends(get_expense_service),
):
    try:
        return service.update_expense(expense_id, payload)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found")


@router.delete("/{expense_id}", response_model=ExpenseResponse)
def delete_expense(
    expense_id: str,
    service: ExpenseService = Depends(get_expense_service),
):
    try:
        return service.delete_expense(expense_id)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found")

