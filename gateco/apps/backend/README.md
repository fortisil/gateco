# gateco - Backend

FastAPI backend application with async SQLAlchemy, PostgreSQL, and pgvector.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.gateco.main:app --reload --port 8000

# Or via Makefile
make dev
```

## Scripts (Makefile)

| Command | Description |
|---------|-------------|
| `make dev` | Run development server with `--reload` |
| `make test` | Run tests |
| `make lint` | Lint code with ruff |
| `make format` | Format code with ruff |

## Structure

```
src/gateco/
  main.py              # FastAPI app entry point (loads .env via dotenv before imports)
  startup.py           # App initialization
  exceptions.py        # Custom exception handlers
  routes/              # API route handlers (auth, dashboard, audit, simulator, etc.)
  services/            # Business logic (policy, pipeline, data catalog, connector, etc.)
  schemas/             # Pydantic v2 request/response schemas
  utils/
    seed.py            # Database seed data (admin@acmecorp.com / password123 / Sarah Chen)
    security.py        # Password hashing, token generation
    crypto.py          # Encryption utilities
    patch.py           # PATCH operation helpers
  middleware/
    admin_auth.py      # Admin token authentication
    jwt_auth.py        # JWT bearer authentication
    entitlement.py     # Plan entitlement checks
    observability.py   # Request-id + timing headers
    rate_limit.py      # Rate limiting (relaxed to 50 attempts when DEBUG=true)
  database/
    connection.py      # Async engine + session factory (uses pydantic-settings)
    settings.py        # DatabaseSettings (pydantic-settings, reads .env)
    vector.py          # pgvector integration
    enums.py           # Shared enums
    models/            # SQLAlchemy 2.0 async models
tests/
  conftest.py          # Test fixtures
```

## API Documentation

Once running, API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest                       # Run all tests
pytest -v                    # Verbose
pytest --cov=src/gateco      # With coverage
ruff check src/ tests/       # Linting
```

## Environment Variables

Create a `.env` file in the backend directory (or copy `.env.example` if available):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gateco_db
JWT_SECRET_KEY=your-secret-key-min-32-chars-long
ADMIN_TOKEN=your-admin-token
DEBUG=true
```

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/gateco_db` | **Required.** Must use `postgresql+asyncpg://` scheme |
| `JWT_SECRET_KEY` | `(min 32 chars)` | Required for auth token signing |
| `ADMIN_TOKEN` | `(string)` | Admin API access |
| `DEBUG` | `true` | Enables DEBUG logging and relaxed rate limits |

**Important:** `main.py` calls `load_dotenv()` at the top before any other imports, ensuring `.env` values are available to all modules including pydantic-settings. The database connection uses `DatabaseSettings` (pydantic-settings), not raw `os.getenv()`.

## Seed Data

The seed script (`utils/seed.py`) creates a default user for local development:
- **Email:** admin@acmecorp.com
- **Password:** password123
- **Name:** Sarah Chen

## API Response Conventions

List endpoints return responses wrapped in a `{ data: [...] }` envelope. Backend serializers ensure no `null` values for array or date fields that the frontend iterates over -- defaulting to `[]` or appropriate fallbacks instead.

## Database Migrations

```bash
alembic upgrade head                          # Run all pending migrations
alembic revision --autogenerate -m "message"  # Generate new migration
```
