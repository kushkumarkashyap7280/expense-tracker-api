from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    date: date
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
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


class ExpenseCursorResponse(BaseModel):
    items: list[ExpenseResponse]
    next_cursor: Optional[str] = None
