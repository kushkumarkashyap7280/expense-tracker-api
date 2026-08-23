class ExpenseNotFoundError(Exception):
    def __init__(self, expense_id: str) -> None:
        self.expense_id = expense_id
        super().__init__(f"Expense with id '{expense_id}' not found")


class InvalidDateRangeError(Exception):
    def __init__(self, message: str = "Invalid date range") -> None:
        super().__init__(message)
