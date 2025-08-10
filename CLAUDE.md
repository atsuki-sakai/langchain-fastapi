# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Environment
```bash
# Quick setup (recommended)
./scripts/dev-setup.sh

# Manual setup
make install          # Install dependencies and create venv
make docker-up        # Start PostgreSQL container
make migrate-dev      # Initialize development database
make dev             # Start development server

# Environment management
make clean           # Remove venv and cache files
```

### Testing
```bash
make test           # Run all tests
make test-unit      # Run unit tests only
make test-integration # Run integration tests only

# Specific tests
pytest app/tests/unit/test_auth.py -v
pytest -m "unit" -v    # Run tests with unit marker
pytest -m "integration" -v # Run tests with integration marker
```

### Code Quality
```bash
make format         # Format code with black and isort
make lint           # Run flake8 linting
make check          # Run format + lint + test (pre-commit check)
```

### Database Management
```bash
make migrate-dev    # Initialize dev database (Docker PostgreSQL)
make migrate-prod   # Initialize prod database (Render PostgreSQL)
```

### Development Server
```bash
make dev            # Development mode (local Docker DB)
make dev-prod       # Production mode (remote Render DB)

# Custom port
make dev PORT=3000
```

## Architecture Overview

This is a **FastAPI enterprise application** built with clean architecture principles:

### Core Architecture Layers
- **`app/api/`**: API endpoints with versioning (v1, future v2)
- **`app/core/`**: Configuration, database, security, logging, error handling
- **`app/services/`**: Business logic layer
- **`app/repositories/`**: Data access layer (future implementation)
- **`app/models/`**: Pydantic DTOs for API requests/responses
- **`app/schemas/`**: SQLAlchemy database models
- **`app/middleware/`**: Custom middleware components
- **`app/utils/`**: Utility functions

### Configuration Management
- **Environment-based settings**: Uses different `.env` files per environment
  - `.env.dev` for development (Docker PostgreSQL)
  - `.env` for production (Render PostgreSQL)
- **Dynamic configuration**: `app/core/config.py` loads appropriate env file based on `ENVIRONMENT` variable
- **Settings validation**: Pydantic BaseSettings with validators for security

### Database Architecture
- **Dual database setup**: Sync for migrations, async for runtime
- **SQLAlchemy + asyncpg**: Async PostgreSQL operations
- **Development**: Docker PostgreSQL (localhost:5432)
- **Production**: Render PostgreSQL with SSL
- **Connection management**: Proper session handling with dependency injection

### Known Issues to Fix

#### Critical Pydantic v2 Migration Issue
The codebase has a **critical compatibility issue** with Pydantic v2:
- `app/core/config.py:2` imports `BaseSettings` from `pydantic` (old v1 syntax)
- **Fix required**: Change to `from pydantic_settings import BaseSettings`
- This affects all configuration loading and will break database initialization

#### Missing Dependencies
- `requirements.txt:29` references non-existent `python-cors` package
- **Fix**: Remove this line (CORS is handled by FastAPI's built-in CORSMiddleware)

### Security Implementation
- **JWT Authentication**: Uses python-jose for token handling
- **Password Hashing**: bcrypt with configurable rounds
- **Environment-based security**: Different security levels for dev/prod
- **CORS Configuration**: Configurable origins via environment variables

### Testing Strategy
- **pytest-asyncio**: For testing async endpoints
- **Markers**: `unit`, `integration`, `slow`, `auth`, `db` for test categorization
- **Test structure**: Separate unit and integration test directories
- **HTTP testing**: Uses httpx for async HTTP client testing

### API Design Patterns
- **Versioned APIs**: `/api/v1/` prefix with room for future versions
- **Clean routing**: Centralized in `app/api/__init__.py`
- **Health checks**: Available at `/api/v1/health`
- **Auto-documentation**: OpenAPI at `/api/v1/docs`

### Environment Management
- **Docker-based development**: PostgreSQL + pgAdmin containers
- **Script automation**: `scripts/dev-setup.sh` for one-command setup
- **Environment isolation**: Separate settings per environment
- **Development ergonomics**: Makefile with helpful commands and documentation

### Deployment Configuration
- **Render.com ready**: `render.yaml` configuration file
- **Production database**: Pre-configured Render PostgreSQL connection
- **Environment variables**: Managed through render.yaml and .env files
- **SSL/Security**: Production-ready security settings