class ExpenseNotFoundError(Exception):
    def __init__(self, expense_id: str) -> None:
        self.expense_id = expense_id
        super().__init__(f"Expense with id '{expense_id}' not found")


class InvalidDateRangeError(Exception):
    def __init__(self, message: str = "date_from cannot be after date_to") -> None:
        super().__init__(message)


class FutureDateError(Exception):
    def __init__(self, message: str = "Future year or month not allowed") -> None:
        super().__init__(message)
