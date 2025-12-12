# Contributing Guide

Welcome to the FastAPI Project! We appreciate your interest in contributing. This document provides guidelines and information to help you get started.

## Project Structure

The project follows a modular architecture designed for scalability and maintainability.

```text
.
├── app
│   ├── api
│   │   └── v1
│   │       └── router.py    # Main API router (aggregates module routers)
│   ├── constants            # Application constants and literals
│   ├── core                 # Core functionality (config, db, security, email)
│   ├── modules              # Domain-Driven Modules
│   │   ├── auth             # Auth (Login, Register, Tokens)
│   │   │   └── tests        # Co-located tests
│   │   ├── users            # User Management
│   │   ├── roles            # RBAC (Roles & Permissions)
│   │   ├── oauth            # OAuth Providers
│   │   └── audit            # Audit Logging
│   └── main.py              # Application entry point
├── alembic                  # Database migrations
├── tests                    # Core & Infrastructure tests
├── docker-compose.yml       # Production Docker composition
├── docker-compose.dev.yml   # Development Docker composition
└── requirements.txt         # Project dependencies
```

## Best Practices

### 1. Code Style

- **Type Hinting**: All functions and methods must have type hints.
- **Async/Await**: Use `async` and `await` for all I/O bound operations.
- **Pydantic**: Use Pydantic models for all data validation.
- **SQLModel**: Use SQLModel for database interactions.

### 2. Modular Architecture (DDD)

The project is organized by **Modules** (Domain-Driven Design).

**Recommendation**: Use the CLI to scaffold new modules:

```bash
# Creates module structure with co-located tests
./manage.py make:module my_module --colocated-test
```

- **Structure**: Each module should contain:
  - `models.py`: Database models.
  - `schemas.py`: Pydantic schemas.
  - `service.py`: Business logic.
  - `repository.py`: Database access.
  - `endpoints.py`: API routes.
  - `tests/`: Module-specific tests.
- **Router Registration**: Register your module's router in `app/api/v1/router.py`.

### 3. API Development

- **Response Models**: All endpoints must define a `response_model` using the generic `ResponseModel[T]` wrapper.
- **Error Handling**: Use `create_error_responses` in `app.core.docs` to document error responses in OpenAPI.
  - **Validation Errors**: When raising `ValidationError`, ALWAYS provide the `field` argument to map the error to a specific form field (e.g., `field="password"`).
- **Dependency Injection**: Use FastAPI's dependency injection for database sessions (`get_db`) and other shared resources.
- **Filtering**: Use the scalable filtering system (`app.core.filtering`).

  **Implementation Steps**:
  1. **Repository**: Inherit from `BaseRepository`. You get `get_list()` for free.

     ```python
     # For standard usage, no extra code needed in repo.
     # For custom queries, use utilities:
     from app.core.filtering import apply_filters, apply_sorting, apply_search, SortOrder
     ```

  2. **Endpoint**: Accept standard parameters and pass them to your service/repository.

     ```python
     @router.get("/")
     async def list_items(
         q: Optional[str] = None,
         sort: str = "created_at",
         order: str = "desc",
         # Add model-specific filters
         status: Optional[str] = None
     ):
         filters = {"status": status}
         # Pass to service/repo
         return await repo.get_list(filters=filters, search_query=q, ...)
     ```

  3. **Advanced Usage**: For advanced filters (e.g. ranges), simply add them to the `filters` dict in the endpoint logic:

     ```python
     # e.g. /items?min_price=10
     if min_price:
         filters["price__gte"] = min_price
     ```

### 🛠️ Development Setup

1. **Install `uv`**:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. **Install Dependencies**:

    ```bash
    uv sync
    ```

3. **Run Tests**:

    ```bash
    uv run pytest
    ```

4. **Run Linter**:

    ```bash
    uv run ruff check .
    ```

### 4. Database Migrations

We use **Alembic** for database migrations.
**Note**: Alembic is configured to automatically discover models in `app/modules/*/models.py`. You do NOT need to edit `alembic/env.py` when creating new modules.

- **Create a new migration**:

  ```bash
  alembic revision --autogenerate -m "Description of change"
  ```

- **Apply migrations**:

  ```bash
  alembic upgrade head
  ```

### 5. Testing

We use **Pytest** for testing. All new features must include tests.

- **Run tests**:

  ```bash
  # Using Manager Script (runs all tests)
  ./manage.py test

  # Using Pytest directly
  source venv/bin/activate
  pytest tests/
  pytest app/modules/
  ```

- **Test Database**: The test suite automatically creates and destroys a separate `test_db`.

## Development Workflow

1. **Fork** the repository.
2. **Clone** your fork locally.
3. Create a **feature branch** (`git checkout -b feature/my-feature`).
4. Make your changes.
5. **Run tests** to ensure no regressions.
6. **Commit** your changes with clear messages.
7. **Push** to your fork and submit a **Pull Request**.

## Environment Variables

See `.env.example` for the required environment variables. Copy it to `.env` for local development.
