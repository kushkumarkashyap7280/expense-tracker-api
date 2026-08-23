# Expense Tracker API — Remaining Implementation Plan

Build out the clean layered architecture (repository → service → router), wire DI, add Supabase integration, tests, config, and docs — per [plan.md](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/plan.md).

## Current State
Stage 2 step 1 is done: files are split into `models.py`, `schemas.py`, `router.py`, but the router still owns the in-memory `expense_db` list and does summary math inline. We need to complete steps 1–9 from the plan.

## Proposed Changes

### 1. Install Missing Dependencies

```bash
pip install pydantic-settings supabase httpx pytest
```
- `pydantic-settings` — for `.env` config
- `supabase` — Supabase Python client
- `httpx` — required by FastAPI's `TestClient`
- `pytest` — test runner

---

### 2. Repository Layer

#### [NEW] [`repository.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/repository.py)

- `ExpenseRepository` — abstract base class (using `abc.ABC`) defining the contract:
  - `create(expense: Expense) -> Expense`
  - `get_by_id(expense_id: str) -> Expense | None`
  - `list_all(category: str | None, date_from: date | None, date_to: date | None, skip: int, limit: int) -> list[Expense]`
  - `delete(expense_id: str) -> Expense | None`
  - `update(expense_id: str, data: dict) -> Expense | None`
  - `get_by_month(year: int, month: int) -> list[Expense]`
- `InMemoryExpenseRepository` — concrete impl using a `list[dict]`, satisfies the interface. This becomes the pytest fake too.

---

### 3. Domain Exceptions

#### [NEW] [`exceptions.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/exceptions.py)

- `ExpenseNotFoundError(expense_id: str)` — raised by the service layer
- `InvalidDateRangeError` — for bad filter ranges (if needed)

---

### 4. Service Layer

#### [NEW] [`service.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/service.py)

- `ExpenseService` — constructor takes `ExpenseRepository` (injected).
- Methods: `create_expense`, `get_expense`, `list_expenses`, `update_expense`, `delete_expense`, `get_summary`.
- Summary aggregation logic (currently in router) moves here.
- Raises `ExpenseNotFoundError`, never `HTTPException`.

---

### 5. Router Refactor

#### [MODIFY] [`router.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/router.py)

- Remove `expense_db` list entirely.
- Each route handler: parse request → call `ExpenseService` → catch domain exceptions → translate to `HTTPException` → return response schema.
- Zero business logic, zero direct data access.
- Receives `ExpenseService` via `Depends`.

---

### 6. Dependency Wiring

#### [NEW] [`dependencies.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/dependencies.py)

- `get_repository() -> ExpenseRepository` — returns the active repository impl (InMemory for dev, Supabase for prod).
- `get_expense_service(repo = Depends(get_repository)) -> ExpenseService` — builds the service with injected repo.
- Reads config to decide which repository implementation to use.

---

### 7. Config

#### [NEW] [`config.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/config.py)

- `Settings` class using `pydantic-settings`, reads from `.env`:
  - `SUPABASE_URL: str = ""`
  - `SUPABASE_KEY: str = ""`
  - `USE_SUPABASE: bool = False`
- `get_settings()` function (cached).

#### [NEW] [`.env.example`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/.env.example)

- Placeholder values only.

---

### 8. Supabase Integration

#### [NEW] [`database/supabase_client.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/database/supabase_client.py)

- Creates the Supabase client once using settings from config.

#### [NEW] [`database/__init__.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/database/__init__.py)

#### [NEW] [`supabase_repository.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/supabase_repository.py)

- `SupabaseExpenseRepository` — implements `ExpenseRepository` interface.
- Translates domain model ↔ DB rows via the Supabase client.
- Assumes an `expenses` table in Supabase.

---

### 9. Tests

#### [NEW] [`tests/__init__.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/tests/__init__.py)
#### [NEW] [`tests/test_expense_service.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/tests/test_expense_service.py)

- Unit tests for `ExpenseService` using `InMemoryExpenseRepository` (no mocks of owned code).
- Tests: create, get, get not found, list with filters, delete, delete not found, summary aggregation.

#### [NEW] [`tests/test_expense_router.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/tests/test_expense_router.py)

- Integration tests via `TestClient` with `app.dependency_overrides` swapping in the in-memory repository.
- At least one test per endpoint.

---

### 10. Package Init Files & Main Update

#### [NEW] [`app/__init__.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/__init__.py)
#### [NEW] [`app/features/__init__.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/__init__.py)
#### [NEW] [`app/features/expenses/__init__.py`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/app/features/expenses/__init__.py)

---

### 11. Docs & Submission

#### [NEW] [`README.md`](file:///home/kushkumarkashyap7280/Desktop/expense-tracker-api/README.md)

- Setup instructions, how to run, how to test, architectural decisions.

#### [MODIFY] Generate `requirements.txt` via `pip freeze`.

---

## Verification Plan

### Automated Tests
```bash
pytest tests/ -v
```

### Manual Verification
```bash
uvicorn app.main:app --reload
# Hit endpoints via /docs (Swagger UI)
```

## Final File Tree
```
expense-tracker-api/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── plan.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── supabase_client.py
│   └── features/
│       ├── __init__.py
│       └── expenses/
│           ├── __init__.py
│           ├── models.py
│           ├── schemas.py
│           ├── exceptions.py
│           ├── repository.py
│           ├── supabase_repository.py
│           ├── service.py
│           ├── dependencies.py
│           └── router.py
└── tests/
    ├── __init__.py
    ├── test_expense_service.py
    └── test_expense_router.py
```
