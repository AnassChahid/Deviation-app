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
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` for your SQL Server instance.

Create the database in SQL Server first, for example:

```sql
CREATE DATABASE DeviationDb;
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

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

After the first user exists, this endpoint is disabled.
