# Expense Tracker API

A FastAPI-based expense tracking REST API demonstrating **clean layered architecture** with proper separation of concerns, dependency injection, and testability.

## Architecture

```
Router (HTTP adapter)
  ↓ Depends()
Service (business logic)
  ↓ constructor injection
Repository (data access — abstract interface)
  ↓
SupabaseExpenseRepository (Supabase / Postgres)
```

### Layer Responsibilities

| Layer | File | Responsibility |
|-------|------|----------------|
| **Schemas** | `schemas.py` | HTTP contract — request/response shapes (Pydantic) |
| **Models** | `models.py` | Domain model — internal shape, transport-agnostic |
| **Repository** | `repository.py` | Abstract data access interface |
| **Supabase Repo** | `supabase_repository.py` | Concrete implementation backed by Supabase Postgres |
| **Exceptions** | `exceptions.py` | Domain exceptions — raised by service, never `HTTPException` |
| **Service** | `service.py` | All business logic, including summary aggregation |
| **Router** | `router.py` | Thin HTTP adapter — parse, delegate, translate exceptions |
| **Dependencies** | `dependencies.py` | DI wiring via FastAPI `Depends` |
| **Config** | `config.py` | `pydantic-settings` reading from `.env` |

### Key Design Decisions

- **Repository pattern with ABC interface** — decouples service logic from the data store; makes it easy to swap implementations or test with fakes.
- **Service layer owns all business logic** — summary aggregation, validation, and error handling happen here, not in the router.
- **Domain exceptions** — the service raises `ExpenseNotFoundError` (not `HTTPException`), keeping it transport-agnostic. The router catches and translates.
- **Constructor injection** — `ExpenseService` receives its repository via constructor, wired through FastAPI's `Depends` chain.
- **Test fakes** — tests use a `FakeExpenseRepository` (defined in test code only) that satisfies the same abstract interface — no mocking of owned code.

## Project Structure

```
expense-tracker-api/
├── .env.example          # Placeholder environment config
├── .gitignore
├── README.md
├── requirements.txt
├── plan.md               # Architecture plan and progress
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # pydantic-settings config
│   ├── database/
│   │   ├── __init__.py
│   │   └── supabase_client.py
│   └── features/
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
    ├── conftest.py               # FakeExpenseRepository for tests
    ├── test_expense_service.py   # Unit tests (service layer)
    └── test_expense_router.py    # Integration tests (TestClient)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/expenses` | Create a new expense |
| `GET` | `/expenses` | List expenses (filterable by category, date range; paginated) |
| `GET` | `/expenses/{id}` | Get a single expense by ID |
| `PUT` | `/expenses/{id}` | Partial update an expense |
| `DELETE` | `/expenses/{id}` | Delete an expense |
| `GET` | `/expenses/summary?year=&month=` | Monthly spending summary with category breakdown |

## Setup

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd expense-tracker-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Supabase

```bash
cp .env.example .env
# Edit .env with your Supabase project URL and API key
```

Create an `expenses` table in your Supabase project:

```sql
CREATE TABLE expenses (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  amount FLOAT8 NOT NULL,
  category TEXT NOT NULL,
  date DATE NOT NULL,
  description TEXT
);
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

## Testing

```bash
pytest tests/ -v
```

Tests run against a `FakeExpenseRepository` — no real database needed, no mocking of owned code.

- **`test_expense_service.py`** — 17 unit tests covering service-layer logic in isolation
- **`test_expense_router.py`** — 16 integration tests via `TestClient` with `dependency_overrides`

## Running with Docker (e.g. on Azure VM)

### 1. Build and run using Docker Compose

```bash
# Start container in background with auto-restart
docker compose up -d --build
```

### 2. Or using standard Docker commands

```bash
# Build the image
docker build -t expense-tracker-api .

# Run the container
docker run -d \
  --name expense-tracker-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  expense-tracker-api
```

Check container status & logs:
```bash
docker logs -f expense-tracker-api
```

> **Azure VM Tip:** Make sure port `8000` (or `80`/`443` if using Nginx reverse proxy) is allowed in your Azure VM's **Network Security Group (NSG) Inbound port rules**.

