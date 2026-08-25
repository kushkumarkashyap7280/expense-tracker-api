# Expense Tracker API

A FastAPI-based expense tracking REST API demonstrating **clean layered architecture** with proper separation of concerns, dependency injection, and testability.

##  Live Demo & API Documentation

- **Interactive Swagger UI**: [http://20.2.250.240:8000/docs](http://20.2.250.240:8000/docs)
- **ReDoc UI**: [http://20.2.250.240:8000/redoc](http://20.2.250.240:8000/redoc)
- **Base URL**: `http://20.2.250.240:8000`

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
| **Repository** | `repository.py` | Abstract data access interface (`ABC`) |
| **Supabase Repo** | `supabase_repository.py` | Concrete implementation backed by Supabase Postgres |
| **Exceptions** | `exceptions.py` | Domain exceptions — raised by service, translated to `HTTPException` by router |
| **Service** | `service.py` | All business logic, summary aggregation math, validation rules |
| **Router** | `router.py` | Thin HTTP adapter — parse, delegate, translate exceptions, return schemas |
| **Dependencies** | `dependencies.py` | DI wiring via FastAPI `Depends` |
| **Config** | `config.py` | `pydantic-settings` reading from `.env` |

### Key Design Decisions

- **Repository Pattern with ABC Interface**: Decouples business logic from database operations, making it trivial to swap storage engines or test with fast in-memory fakes.
- **Domain Exception Hierarchy**: The service raises domain exceptions (`ExpenseNotFoundError`, `FutureDateError`, `InvalidDateRangeError`), keeping it 100% transport-agnostic. The router catches and translates them into appropriate HTTP status codes (404, 400).
- **Service Layer Aggregation & Precision**: Monthly summary calculation runs in the service layer (not a DB passthrough) and applies currency rounding (`round(..., 2)`) to eliminate floating-point precision errors.
- **Constructor Injection & FastAPI `Depends`**: `ExpenseService` receives its repository via constructor, wired through FastAPI's dependency injection chain.
- **Test Fakes (No Mocking of Owned Code)**: Tests use a `FakeExpenseRepository` in memory, ensuring test speed (~0.5s) and zero reliance on live third-party network connections.


## Project Structure

```
expense-tracker-api/
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD pipeline (Tests + Auto-deploy to Azure VM)
├── .dockerignore
├── .env.example                  # Placeholder environment config
├── .gitignore
├── Dockerfile                    # Production container image
├── docker-compose.yml            # Compose service with auto-restart
├── README.md
├── requirements.txt
├── plan.md                       # Architecture plan
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # pydantic-settings config
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
    ├── conftest.py               # FakeExpenseRepository & fixtures for tests
    ├── test_expense_service.py   # Unit tests (service layer in isolation)
    └── test_expense_router.py    # Integration tests (TestClient HTTP flow)
```

## API Endpoints

| Method | Path | Query / Body Params | Description |
|--------|------|---------------------|-------------|
| `POST` | `/expenses` | JSON body (`ExpenseCreate`) | Create a new expense |
| `GET` | `/expenses` | `category`, `date_from`, `date_to`, `skip`, `limit` | List expenses (offset paginated & filterable) |
| `GET` | `/expenses/cursor` | `cursor_id`, `category`, `date_from`, `date_to`, `limit` | High-performance cursor-based pagination |
| `GET` | `/expenses/summary` | `year`, `month` | Monthly spending summary with category breakdown |
| `GET` | `/expenses/{id}` | `expense_id` | Get a single expense by ID (or 404) |
| `PUT` | `/expenses/{id}` | `expense_id`, JSON (`ExpenseUpdate`) | Partial update an expense |
| `DELETE` | `/expenses/{id}` | `expense_id` | Delete an expense |

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
# Edit .env with your Supabase project URL and Service Role Key
```

Create the `expenses` table and performance indexes in Supabase SQL Editor:

```sql
-- Table definition
CREATE TABLE expenses (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  amount FLOAT8 NOT NULL,
  category TEXT NOT NULL,
  date DATE NOT NULL,
  description TEXT
);

-- Performance Indexes
CREATE INDEX idx_expenses_date ON expenses (date);
CREATE INDEX idx_expenses_category_date ON expenses (category, date);
```

### 4. Run the server locally

```bash
uvicorn app.main:app --reload
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

## Testing

```bash
pytest tests/ -v
```

All **41 automated tests** run against an in-memory `FakeExpenseRepository` — fast (~0.5s), isolated, and 100% deterministic:

- **`test_expense_service.py`** — 21 unit tests covering service logic, exceptions, math, and cursor pagination in isolation.
- **`test_expense_router.py`** — 20 integration tests via `TestClient` verifying the full HTTP request/response pipeline and status codes.


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

## CI/CD Pipeline (GitHub Actions)

A complete automated CI/CD pipeline is configured in `.github/workflows/deploy.yml`:
1. On every `git push` to `main`, GitHub Actions automatically installs dependencies and runs the entire **41-test test suite**.
2. If all tests pass, GitHub Actions connects to the **Azure VM via SSH**, pulls the latest changes, and rebuilds the Docker container with zero downtime.
