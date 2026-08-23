from datetime import date
from typing import Optional

from pydantic import BaseModel


class Expense(BaseModel):
    id: str
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None