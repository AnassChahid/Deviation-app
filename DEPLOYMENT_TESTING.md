# Testing Deployment Checklist

This checklist is for deploying the app to a shared testing environment. It is not a production hardening checklist.

## Required Services

- Docker with Docker Compose support.
- SQL Server database reachable from the backend server.
- Backend URL reachable from the frontend server.

## Backend Setup

```powershell
Copy-Item .\deploy\backend.env.sample .\deploy\backend.env
```

Edit `deploy\backend.env`:

- `DATABASE_URL`: SQL Server connection string for the testing database.
- `SECRET_KEY`: strong testing secret, not the sample value.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token lifetime, default `60`.
- `ENABLE_API_DOCS=True`: expose `/docs` during testing if needed.
- `AUTO_CREATE_DATABASE=True`: optional, only when running the manual initializer and the test SQL Server login may create databases.
- `RUN_STARTUP_MIGRATIONS=False`: recommended; run schema initialization explicitly before starting the app.

Build and start backend:

```powershell
docker compose build backend
docker compose up -d backend
```

Backend checks:

- `GET http://<backend-host>:8001/health`
- `GET http://<backend-host>:8001/health/db`
- `GET http://<backend-host>:8001/docs`

## Frontend Setup

```powershell
Copy-Item .\deploy\frontend.env.sample .\deploy\frontend.env
```

Edit `deploy\frontend.env`:

- `DEBUG=False`
- `SECRET_KEY`: strong testing secret, not the sample value.
- `BACKEND_API_URL=http://backend:8001`
- `HOST=0.0.0.0`
- `PORT=5000`

Start frontend:

```powershell
docker compose build frontend
docker compose up -d frontend
```

Frontend check:

- Open `http://<frontend-host>:5000`
- Login page should load without backend configuration errors.

## Smoke Test

Run this before giving the test deployment to users:

1. Open backend `/health` and `/health/db`.
2. Create the first admin through the register page or `POST /auth/bootstrap-admin`.
3. Login as the first admin.
4. Register a new user with an `@apmterminals.com` email.
5. Confirm the new user cannot login until activated.
6. Activate the user from Manage Users.
7. Login as the activated user.
8. Create a deviation with QC, vessel, category, duration, shift, and deviation type.
9. Edit the deviation and set status to `Done`.
10. Open the deviation detail page and confirm the audit trail shows create/update/close.
11. Confirm Deviations filters, pagination, and CSV export work.
12. Confirm Users and Vessels filters, row selector, and pagination work.
13. Confirm Dashboard loads and shows the new deviation in the relevant panels.

## Notes

- Run `docker compose run --rm backend python -m app.db.initialize` to apply the current compatibility initializer.
- For production later, replace the compatibility initializer with versioned migrations such as Alembic.
- Do not reuse the sample `SECRET_KEY` values outside local testing.
- There is no default seeded superuser. The first admin must be created explicitly.
