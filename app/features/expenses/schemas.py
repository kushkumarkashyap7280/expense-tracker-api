from datetime import date
from typing import Optional

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: str
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None


class ExpenseSummaryResponse(BaseModel):
    total_spending: float
    by_category: dict[str, float]