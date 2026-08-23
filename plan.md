# Plan — Expense Tracker API (AcharyaX/Lemantus Take-Home Challenge)

## Objective
Build a FastAPI Expense Tracker demonstrating clean layered architecture —
graded on structure and separation of concerns, not features.

## Tech stack (required)
- FastAPI
- Supabase (hosted Postgres) — via supabase-py client OR asyncpg/SQLAlchemy
- Pydantic v2 for validation
- FastAPI `Depends` (or a DI library) for dependency injection
- `.env` + `pydantic-settings` for config
- pytest for testing

## Required endpoints
- `POST /expenses` — create (title, amount, category, date, optional description)
- `GET /expenses` — list, filterable by category + date range, paginated
- `GET /expenses/{id}` — get by id or 404
- `DELETE /expenses/{id}`
- `GET /expenses/summary` — accepts month + year, returns total spending +
  category breakdown. Key differentiator endpoint — real service-layer logic
  required, not a DB passthrough.

## Current state (already built, working, tested)

### Stage 1 — DONE
Flat single-file CRUD with an in-memory list, all 5 endpoints working and
smoke-tested (create, list, get-by-id, update, delete, summary). Route
ordering bug (`/expenses/summary` vs `/expenses/{id}`) was hit and fixed.
Partial-update bug (missing `exclude_unset=True`) was hit and fixed.

### Stage 2, step 1 — DONE
Split into folder structure:
```
app/
├── main.py
└── features/
    └── expenses/
        ├── router.py     — routes, still directly touching expense_db list
        ├── schemas.py    — ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummaryResponse
        └── models.py     — Expense (internal domain model)
```
Router still holds `expense_db: list[dict]` directly and does the summary
math inline. This is the known gap the next steps close.

## Remaining work (in order)

1. **Repository layer** — `repository.py`
   - Define an abstract interface (`ABC` or `Protocol`): `ExpenseRepository`
     with `create`, `get_by_id`, `list` (category/date-range filter +
     pagination), `delete`.
   - `InMemoryExpenseRepository` — concrete impl using a list, used by the
     app until Supabase is wired in, and reused as the pytest fake.
   - Router must stop touching `expense_db` directly once this exists.

2. **Domain exceptions** — `exceptions.py`
   - `ExpenseNotFoundError` (and others as needed). Raised by the service,
     never by the repository or router directly.

3. **Service layer** — `service.py`
   - `ExpenseService`, constructor takes an `ExpenseRepository` (injected).
   - All business logic here, including the summary aggregation (move it
     out of `router.py`).
   - Raises domain exceptions, never `HTTPException`.

4. **Router refactor** — `router.py`
   - Router only: parse request, call service, catch domain exceptions and
     translate to `HTTPException`, return response schema.
   - Zero business logic, zero direct data access left.

5. **Dependency wiring** — `dependencies.py`
   - Functions that build the dependency chain: repository → service →
     router, all via `Depends`. Nothing imported as a bare global.

6. **Config** — `config.py`
   - `pydantic-settings` reading `SUPABASE_URL` / `SUPABASE_KEY` from `.env`.

7. **Supabase integration**
   - `database/supabase_client.py` — creates the client once.
   - `SupabaseExpenseRepository` — real implementation of the same
     interface as the in-memory one, translates domain model ↔ DB rows.
   - Swap it in via `dependencies.py` (repository choice becomes
     configurable/injectable, not hardcoded).

8. **Tests** — `tests/`
   - `test_expense_service.py` — unit tests against
     `InMemoryExpenseRepository`/`FakeExpenseRepository` (no real DB, no
     mocking of code we own).
   - `test_expense_router.py` — at least one integration test via
     `TestClient`, with `app.dependency_overrides` swapping in the fake
     repository.
   - Mock only the Supabase client itself if directly testing the
     Supabase repository implementation.

9. **Docs & submission**
   - `README.md` — setup, how to run, how to test, architectural decisions.
   - `.env.example` — placeholder values only.
   - `.gitignore` already created (venv/, __pycache__/, .env, etc.)
   - `requirements.txt` via `pip freeze`.
   - Push to a public GitHub repo, share the link.

## Evaluation criteria (what's actually being graded)
Layer separation · service-layer summary logic quality · real DI (no
tight coupling) · proper Pydantic schema/model separation · test quality
(fakes for service, mocks only for third-party SDK, one integration test)
· code clarity · graceful error handling across all layers · externalized
config, no hardcoded secrets.

## Explicitly out of scope
UI, authentication/authorization, deployment configuration.
