# FastAPI Authentication System

A production-ready FastAPI authentication boilerplate with JWT, RBAC, OAuth2, and comprehensive security features.

## Quick Start

### 1. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Update .env with your settings (especially SECRET_KEY, DATABASE_URL, REDIS_URL)
```

### 2. Start Services with Docker

```bash
# Start all services (PostgreSQL, Redis, MongoDB, FastAPI)
./manage.py docker up -d

# Or use docker-compose directly
docker-compose -f docker-compose.dev.yml up --build
```

### 3. Run Database Migrations

```bash
# Apply migrations
./manage.py upgrade

# Or create a new migration
./manage.py migrate -m "your migration message"
```

### 4. Seed Database

```bash
# Run all seeders (permissions, roles, super admin)
./manage.py db:seed

# Run a specific seeder
./manage.py db:seed permissions

# Force run even if already seeded
./manage.py db:seed --force
```

### 5. Access the API

- **API**: <http://localhost:8000>
- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## Management Commands

All commands run locally by default. Add `--docker` or `-d` to run in Docker container.

| Command | Description |
|---------|-------------|
| `./manage.py run` | Run the development server |
| `./manage.py test` | Run tests locally (auto-discovers `tests/` and `app/modules/*/tests/`) |
| `./manage.py migrate -m "msg"` | Create a new migration |
| `./manage.py upgrade` | Apply database migrations |
| `./manage.py downgrade` | Revert last migration |
| `./manage.py docker up` | Start Docker containers |
| `./manage.py docker down` | Stop Docker containers |
| `./manage.py make:module <name>` | Scaffold a new module |

**Running commands in Docker:**

```bash
# Run tests in Docker
./manage.py test --docker

# Run migration in Docker
./manage.py upgrade --docker

# Run seeders in Docker
./manage.py db:seed --docker
```

### Module Scaffolding

Use the `make:module` command to quickly generate standard module structures:

```bash
# Basic module scaffolding
./manage.py make:module my_module

# Generate with a test file in 'tests/modules/'
./manage.py make:module my_module --with-test

# Generate with a CO-LOCATED test file (Recommended)
# Creates app/modules/my_module/tests/test_my_module.py
./manage.py make:module my_module --colocated-test
```

### Seeder Commands

| Command | Description |
|---------|-------------|
| `./manage.py db:seed` | Run all seeders |
| `./manage.py db:seed <name>` | Run a specific seeder |
| `./manage.py db:seed --force` | Force run even if already seeded |
| `./manage.py db:seed:list` | List available seeders |
| `./manage.py make:seeder <name>` | Create a new seeder file |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new customer |
| POST | `/api/v1/auth/login` | Login (returns access + refresh tokens) |
| POST | `/api/v1/auth/verify-email` | Verify email with OTP |
| POST | `/api/v1/auth/resend-otp` | Resend OTP |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout (blacklist token) |
| GET | `/api/v1/auth/me` | Get current user info |
| POST | `/api/v1/auth/change-password` | Change password |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with OTP |

### OAuth

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/oauth/providers` | List OAuth providers |
| GET | `/api/v1/oauth/login/{provider}` | Get OAuth login URL |
| POST | `/api/v1/oauth/callback` | OAuth callback |

### Admin - User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/admins` | List admins |
| POST | `/api/v1/admin/admins` | Create admin |
| GET | `/api/v1/admin/admins/{id}` | Get admin |
| PUT | `/api/v1/admin/admins/{id}` | Update admin |
| DELETE | `/api/v1/admin/admins/{id}` | Delete admin |
| GET | `/api/v1/admin/customers` | List customers |
| POST | `/api/v1/admin/customers` | Create customer |
| GET | `/api/v1/admin/customers/{id}` | Get customer |
| PUT | `/api/v1/admin/customers/{id}` | Update customer |
| DELETE | `/api/v1/admin/customers/{id}` | Delete customer |

### Admin - RBAC

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/roles` | List roles |
| POST | `/api/v1/admin/roles` | Create role |
| GET | `/api/v1/admin/roles/{id}` | Get role with permissions |
| PUT | `/api/v1/admin/roles/{id}` | Update role |
| DELETE | `/api/v1/admin/roles/{id}` | Delete role |
| GET | `/api/v1/admin/permissions` | List permissions |

### Admin - OAuth Provider Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/oauth-providers` | List OAuth providers |
| POST | `/api/v1/admin/oauth-providers` | Create OAuth provider |
| GET | `/api/v1/admin/oauth-providers/{id}` | Get OAuth provider |
| PUT | `/api/v1/admin/oauth-providers/{id}` | Update OAuth provider |
| DELETE | `/api/v1/admin/oauth-providers/{id}` | Delete OAuth provider |
| PATCH | `/api/v1/admin/oauth-providers/{id}/status` | Activate/deactivate |

### Audit Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/audit-logs` | List audit logs (MongoDB) |

## Features

### Authentication & Security

- ✅ JWT Authentication (access tokens: 15min, refresh tokens: 7 days)
- ✅ Token rotation with reuse detection
- ✅ Token blacklist for immediate logout
- ✅ Email verification with OTP
- ✅ Password reset with OTP
- ✅ Rate limiting for OTP operations
- ✅ HttpOnly cookies for refresh tokens
- ✅ Bcrypt password hashing

### Authorization

- ✅ Role-Based Access Control (RBAC)
- ✅ Dynamic permissions with caching
- ✅ Permission overrides per user
- ✅ Super admin protection (cannot be edited/deleted)

### OAuth2

- ✅ Multiple OAuth providers support
- ✅ Provider management API
- ✅ Account linking

### Audit & Monitoring

- ✅ Comprehensive audit logging (MongoDB)
- ✅ User action tracking (login, logout, register, etc.)
- ✅ IP and User-Agent logging

### Developer Experience

- ✅ Swagger/OpenAPI documentation
- ✅ Consistent API response format
  - See [Error Codes](docs/error_codes.md) for full list
  - **Validation Errors**: Standardized error response structure including specific `field` identification for frontend mapping.
- ✅ Database seeders system
- ✅ Management CLI commands

### Filtering & Pagination

The API supports standardized listing parameters across endpoints (e.g., Customers, Roles):

- **Pagination**: `page`, `per_page` (or `skip`, `limit`)
- **Search**: `q=term` (searches across relevant fields)
- **Sorting**: `sort=field` and `order=asc|desc`
- **Filtering**: Endpoint-specific fields (e.g., `email=foo`, `is_active=true`)

Example:
`GET /api/v1/admin/customers?q=alice&sort=created_at&order=desc&is_active=true`

#### Filter Syntax

Advanced filtering is supported using double underscores `__`:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals (default) | `role=ADMIN` |
| `ne` | Not Equals | `role__ne=CUSTOMER` |
| `gt` / `gte` | Greater Than (or Equal) | `age__gt=18` |
| `lt` / `lte` | Less Than (or Equal) | `price__lte=100` |
| `like` | Case-sensitive contains | `name__like=Admin` |
| `ilike` | Case-insensitive contains | `email__ilike=john` |
| `in` | In list (comma-separated) | `status__in=active,pending` |

## Project Structure

```text
├── app/
│   ├── api/v1/router.py      # Main API router
│   ├── constants/            # Application constants and literals
│   ├── core/                 # Core functionality (config, db, email, base classes)
│   ├── modules/              # Domain-specific modules
│   │   ├── auth/             # Authentication module
│   │   │   ├── tests/        # Co-located tests
│   │   │   └── ...
│   │   ├── users/            # User management module
│   │   ├── roles/            # RBAC module
│   │   ├── oauth/            # OAuth module
│   │   └── audit/            # Audit logging module
│   └── main.py               # Application entry point
├── alembic/                  # Database migrations
├── seeders/                  # Database seeders
├── tests/                    # Core & Infrastructure tests
├── docs/                     # Documentation
├── manage.py                 # CLI management script
└── docker-compose.dev.yml    # Docker development setup
```

## Testing

```bash
# Run all tests in Docker
./manage.py test

### ⚡ Fast Setup with UV

This project uses [uv](https://github.com/astral-sh/uv) for lightning-fast dependency management.

1.  **Install uv** (if not installed):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Install Dependencies**:
    ```bash
    uv sync
    ```

3.  **Run Development Server**:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

# Run tests locally (requires environment setup)
source venv/bin/activate
./manage.py test

# Run specific module tests
pytest app/modules/auth/tests/

# Run specific test file
pytest app/modules/auth/tests/test_auth_api.py -v
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Required |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_HOST` | Redis host | `redis` |
| `MONGO_URI` | MongoDB connection | `mongodb://mongo:27017` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` |
| `SUPER_ADMIN_EMAIL` | Default super admin email | `admin@example.com` |
| `SUPER_ADMIN_PASSWORD` | Default super admin password | `Admin@123` |

## Email Configuration

By default, OTP codes are printed to console. To send actual emails:

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourapp.com
```

## License

MIT
