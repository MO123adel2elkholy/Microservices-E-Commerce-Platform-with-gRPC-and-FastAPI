# Repository Guidelines

## Project Structure & Module Organization

This repository contains four Python services: `user_service/` handles accounts and JWT authentication, `product_service/` manages the catalog, `order_service/` creates orders, and `api_gateway/` exposes the unified API. Shared Protocol Buffer schemas live in `proto/`; generated stubs are under each applicable service's `generated/` directory. Tests are in `tests/`, operational scripts in `scripts/`, and Docker orchestration is defined in `docker-compose.yml`. Persistent development data is stored under `data/`.

## Build, Test, and Development Commands

- `pip install -r requirements.txt` installs application and test dependencies.
- `python scripts/generate_proto.py` regenerates gRPC stubs after editing a `.proto` schema.
- `python -m user_service.main` (similarly `product_service.main`, `order_service.main`, or `api_gateway.main`) starts an individual service locally. Start dependencies first when exercising cross-service calls.
- `docker compose up --build` builds and starts the complete stack, including PostgreSQL.
- `pytest -v` runs the test suite; use `pytest tests/test_api_gateway.py -v` to target a module. `pytest.ini` configures automatic asyncio mode.

## Coding Style & Naming Conventions

Use four spaces for Python indentation and follow standard Python conventions: `snake_case` for modules, functions, and variables; `PascalCase` for classes; and uppercase names for constants. Keep service-specific routes and logic in their service package, and use the existing async patterns for HTTP, database, and gRPC operations. No formatter or linter is configured; keep changes consistent with neighboring code.

## Testing Guidelines

Place tests in `tests/` and name files `test_<area>.py`; name test functions `test_<behavior>`. Add or update focused tests for API, persistence, and service-to-service behavior affected by a change. Run the relevant module first, then `pytest -v` for broader coverage. No coverage threshold is configured.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no repository-specific commit convention could be verified. Use a short imperative commit subject, optionally scoped (for example, `order: validate item quantities`). Pull requests should explain the behavior change, list verification commands and outcomes, link related issues when applicable, and include API examples or screenshots when they clarify a user-visible change.

## Security & Configuration

Configure ports, database URLs, and service endpoints through the existing settings/environment variables. Do not commit secrets or production credentials. Keep local database files and generated runtime data out of unrelated changes.
