from fastapi import FastAPI

from app.features.expenses.router import router as expenses_router

app = FastAPI(title="Expense Tracker API")

app.include_router(expenses_router)