# Port Deviation Management Backend

FastAPI backend for the class diagram in `class2.png`, using SQL Server, JWT authentication, and role-based access.

## Features

- Users have role `admin` or `user`.
- Any authenticated user can create deviations.
- Admin users can create users.
- Admin users can create and manage selectable deviation types.
- Deviation records link to creator user, selected deviation type, QC, and vessel.

## Project Structure

```text
app/
  api/
    router.py              # Registers all API route modules
    routes/                # HTTP controllers grouped by feature
  core/
    config.py              # Environment settings
    security.py            # Password hashing and JWT helpers
  db/
    base.py                # SQLAlchemy Base
    session.py             # SQL Server engine and DB session dependency
  models/                  # SQLAlchemy models, one class per file
  schemas/                 # Pydantic request/response models
  services/                # Business logic separated from HTTP routes
  dependencies.py          # Authentication and role dependencies
  main.py                  # FastAPI application factory
```

This structure keeps the backend easy to reuse from another app: import the service layer for business operations, the routers for HTTP integration, or the models/schemas independently when needed.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item env.sample .env
```

Edit `.env` and set `DATABASE_URL` and `SECRET_KEY` for your environment.

Create the configured SQL Server database before starting the app:

```sql
CREATE DATABASE DeviationDb;
```

Initialize or update the schema with the controlled initializer:

```powershell
python -m app.db.initialize
```

For local or testing only, `AUTO_CREATE_DATABASE=True` allows the initializer to create the database if the SQL Server login has permission.

The API does not mutate the schema on startup unless `RUN_STARTUP_MIGRATIONS=True` is explicitly set. Keep this disabled for production.

Start the API:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Production-style start without reload:

```powershell
.\start-production.ps1
```

Run backend tests from the repository root:

```powershell
python -m pytest Backend/tests
```

Open:

- API docs when `ENABLE_API_DOCS=True`: `http://127.0.0.1:8001/docs`
- API health check: `http://127.0.0.1:8001/health`
- Database health check: `http://127.0.0.1:8001/health/db`

## First Admin User

Create an admin through the bootstrap endpoint once:

```http
POST /auth/bootstrap-admin
```

Body:

```json
{
  "firstName": "Admin",
  "lastName": "User",
  "email": "admin@example.com",
  "password": "admin123"
}
```

After the first user exists, this endpoint is disabled. The backend does not seed a default admin or reset any password on startup.

## Production Notes

- Use a unique `SECRET_KEY` with at least 32 characters.
- Keep `ENABLE_API_DOCS=False` unless docs are intentionally exposed.
- Keep `AUTO_CREATE_DATABASE=False` and `RUN_STARTUP_MIGRATIONS=False`; create, grant, and migrate the database explicitly.
- Run `start-production.ps1` under a process manager or service account instead of `--reload`.
- Keep `.env` and runtime logs out of source control.

## Testing Deployment

Use the repository-level `DEPLOYMENT_TESTING.md` checklist before handing the app to testers.
