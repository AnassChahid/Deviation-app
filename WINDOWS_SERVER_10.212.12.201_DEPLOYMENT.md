# Docker Deployment Runbook - Windows Server 10.212.12.201

This runbook deploys the Deviation app on Windows Server `10.212.12.201` using Docker Compose.

Assumptions:

- The project lives at `C:\Apps\DeviationApp`.
- Docker runs Linux containers.
- SQL Server is reachable from the Docker containers.
- Backend is exposed on `http://10.212.12.201:8001`.
- Frontend is exposed on `http://10.212.12.201:5000`.
- HTTPS is handled by IIS, a reverse proxy, or another approved gateway in front of the frontend.

## 1. Install Server Prerequisites

Install on `10.212.12.201`:

- Docker Desktop or Docker Engine with Docker Compose support.
- Git, or another approved way to copy the project folder to the server.
- Optional but recommended: IIS or another reverse proxy for HTTPS.

Verify in PowerShell:

```powershell
docker --version
docker compose version
```

Docker must be set to Linux containers.

## 2. Copy The Application

Create the deployment directory:

```powershell
New-Item -ItemType Directory -Force C:\Apps
```

Copy or clone the project to:

```text
C:\Apps\DeviationApp
```

Then:

```powershell
cd C:\Apps\DeviationApp
```

Do not commit or copy real secrets into git. Runtime env files are ignored by `.gitignore`.

## 3. Create Docker Env Files

Create the deploy env folder if it does not exist:

```powershell
New-Item -ItemType Directory -Force .\deploy
Copy-Item .\deploy\backend.env.sample .\deploy\backend.env
Copy-Item .\deploy\frontend.env.sample .\deploy\frontend.env
```

Generate two different strong secrets:

```powershell
$bytes = New-Object byte[] 48
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
[Convert]::ToBase64String($bytes)
$rng.GetBytes($bytes)
[Convert]::ToBase64String($bytes)
$rng.Dispose()
```

Edit `deploy\backend.env`:

```text
APP_NAME=Port Deviation Management API
DATABASE_URL=mssql+pyodbc:///?odbc_connect=<your-encoded-sql-server-connection>
SECRET_KEY=<strong-backend-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENABLE_API_DOCS=False
AUTO_CREATE_DATABASE=False
RUN_STARTUP_MIGRATIONS=False
```

Edit `deploy\frontend.env`:

```text
DEBUG=False
FLASK_APP=run.py
FLASK_DEBUG=0
HOST=0.0.0.0
PORT=5000
SECRET_KEY=<different-strong-frontend-secret>
ASSETS_ROOT=/static/assets
BACKEND_API_URL=http://backend:8001
FRONTEND_AUTH_MODE=backend
```

Important: inside Docker, `localhost` means the container itself. For `DATABASE_URL`, use the real SQL Server host, for example `10.212.12.201` or the SQL Server DNS name.

## 4. Prepare SQL Server

Create the production database and SQL login/user outside the app.

Minimum app permissions after schema is initialized:

- Connect to the database.
- Read/write application tables.

The Docker image includes Microsoft ODBC Driver 18 for SQL Server.

## 5. Build The Containers

From the project root:

```powershell
cd C:\Apps\DeviationApp
docker compose build
```

The first build downloads Python packages and the Microsoft ODBC driver, so it needs internet access.

## 6. Initialize Database Once

Run the controlled initializer once after the database and env files are ready:

```powershell
docker compose run --rm backend python -m app.db.initialize
```

Keep this setting in `deploy\backend.env`:

```text
RUN_STARTUP_MIGRATIONS=False
```

Normal application startup must not mutate the schema.

## 7. Start The App

```powershell
docker compose up -d
```

Check status:

```powershell
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

Health checks:

```powershell
Invoke-RestMethod http://10.212.12.201:8001/health
Invoke-RestMethod http://10.212.12.201:8001/health/db
```

Open the frontend:

```text
http://10.212.12.201:5000
```

Expected:

- `/health` returns `status: ok`.
- `/health/db` reports database reachable.
- `/docs`, `/redoc`, and `/openapi.json` are unavailable when `ENABLE_API_DOCS=False`.

## 8. Open Firewall Ports

If users or the reverse proxy connect directly to these app ports:

```powershell
New-NetFirewallRule -DisplayName "Deviation Backend 8001" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
New-NetFirewallRule -DisplayName "Deviation Frontend 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

If IIS/reverse proxy is the only public entrypoint, expose only `80/443` publicly and keep `5000/8001` restricted to the server.

## 9. Configure HTTPS Reverse Proxy

Production cookies are marked `Secure`, so real browser sessions require HTTPS.

Recommended external URL:

```text
https://10.212.12.201/
```

Proxy target:

```text
http://127.0.0.1:5000
```

Keep backend `8001` internal unless direct API access is required.

## 10. First Admin And Smoke Test

1. Open the frontend.
2. Register the first admin account.
3. Log in as admin.
4. Create required reference data: deviation type, vessel, QC.
5. Register a normal user with an `@apmterminals.com` email.
6. Activate the normal user as admin.
7. Log in as the normal user.
8. Create a deviation.
9. Confirm the admin receives a notification.
10. Edit the deviation as the user.
11. Confirm the admin receives an update notification.
12. Delete a deviation as the user.
13. Confirm the admin receives a delete notification and can mark it read.
14. Confirm dashboard, filters, pagination, and records table work.

## 11. Update Deployment Later

From the project root:

```powershell
cd C:\Apps\DeviationApp

# Copy the new release files or pull from the approved branch.
docker compose build
docker compose up -d
```

Only run the initializer when a release intentionally includes a database change:

```powershell
docker compose run --rm backend python -m app.db.initialize
```

Check logs after every update:

```powershell
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

## 12. Stop Or Restart

```powershell
docker compose restart
docker compose stop
docker compose up -d
```

## 13. Operational Rules

- Do not commit `deploy\backend.env`, `deploy\frontend.env`, `Backend\.env`, or `Frontend\.env`.
- Keep `RUN_STARTUP_MIGRATIONS=False` for normal app startup.
- Run `docker compose run --rm backend python -m app.db.initialize` only as an explicit deployment/migration step.
- Back up SQL Server before schema changes.
- Keep backend API docs disabled in production.
- Use HTTPS for real users because cookies are `Secure`.
- Keep backend port `8001` private if users only need the frontend.
