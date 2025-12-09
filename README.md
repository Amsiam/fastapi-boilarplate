# Production Ready FastAPI Project

A robust, production-ready FastAPI boilerplate featuring Async PostgreSQL, Redis caching, Docker support, and comprehensive testing.

## Features

-   **FastAPI**: High performance, easy to learn, fast to code, ready for production.
-   **Async PostgreSQL**: Using `SQLModel` and `asyncpg` for non-blocking database operations.
-   **Redis Caching**: Integrated caching support.
-   **Alembic Migrations**: Database schema version control.
-   **Docker**: Optimized configurations for Development and Production.
-   **Testing**: Pytest suite with automated test database management.
-   **Standardized Responses**: Consistent success and error response formats.
-   **Email**: Integrated email sending utility.

## Prerequisites

-   [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
-   Python 3.11+ (for local development without Docker)

## Quick Start (Docker)

The easiest way to run the project is using Docker Compose.

### Development
Starts the app in reload mode with a local PostgreSQL and Redis instance.

1.  **Configure Environment**:
    ```bash
    cp .env.example .env
    ```

2.  **Run Containers**:
    ```bash
    docker-compose -f docker-compose.dev.yml up --build
    ```

-   **API**: [http://localhost:8000](http://localhost:8000)
-   **Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Production
Starts the app in production mode (no reload, optimized build).

```bash
docker-compose -f docker-compose.yml up --build -d
```

## Local Development

If you prefer running locally without Docker:

1.  **Create Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start Services**:
    Ensure you have PostgreSQL and Redis running locally. Update `.env` with your local credentials.

4.  **Run Migrations**:
    ```bash
    alembic upgrade head
    ```

5.  **Run Application**:
    ```bash
    uvicorn app.main:app --reload
    ```

## Running Tests

Tests are powered by `pytest` and run in an isolated environment.

**Using Docker (Recommended):**
```bash
docker-compose -f docker-compose.dev.yml run --rm -e PYTHONPATH=. -e POSTGRES_SERVER=db web pytest
```

**Locally:**
Ensure your local DB credentials in `.env` are correct, then:
```bash
pytest
```

## CLI Tool

The project includes a `manage.py` CLI tool to simplify common tasks.

```bash
# Install dependencies first (including typer)
pip install -r requirements.txt

# Run the server (Dev)
./manage.py run

# Run tests (Docker)
./manage.py test

# Run tests (Local)
./manage.py test --no-docker

# Create a migration
./manage.py migrate -m "Add user table"

# Apply migrations
./manage.py upgrade

# Docker management
./manage.py docker up
./manage.py docker down
```

## Project Structure

See [CONTRIBUTING.md](CONTRIBUTING.md) for a detailed breakdown of the project structure and development guidelines.
