# Windows Server Deployment Runbook - 10.212.12.201

This runbook deploys the backend and frontend on Windows Server `10.212.12.201`.

Assumptions:

- The application will live at `C:\Apps\DeviationApp`.
- Backend listens on `http://10.212.12.201:8001`.
- Frontend listens on `http://10.212.12.201:5000`.
- SQL Server is reachable from `10.212.12.201`.
- HTTPS is handled by IIS/reverse proxy or another approved gateway in front of the frontend.

## 1. Install Server Prerequisites

Install on `10.212.12.201`:

- Python 3.12 or Python 3.10+.
- Microsoft ODBC Driver 18 for SQL Server.
- Git, or copy the project folder manually.
- Optional but recommended: NSSM or Windows Services for running both apps continuously.
- Optional but recommended: IIS or another reverse proxy for HTTPS.

Verify in PowerShell:

```powershell
python --version
```

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

Do not copy developer cache folders such as `__pycache__`, `.pytest_cache`, or log files.

## 3. Create Backend Environment

```powershell
cd C:\Apps\DeviationApp\Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item env.sample .env
```

Edit `Backend\.env`:

```text
APP_NAME=Port Deviation Management API
DATABASE_URL=mssql+pyodbc:///?odbc_connect=<your-encoded-sql-server-connection>
SECRET_KEY=<generate-a-strong-unique-secret-at-least-32-chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENABLE_API_DOCS=False
AUTO_CREATE_DATABASE=False
RUN_STARTUP_MIGRATIONS=False
```

Generate a strong secret if needed:

```powershell
$bytes = New-Object byte[] 48
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
[Convert]::ToBase64String($bytes)
$rng.Dispose()
```

## 4. Prepare SQL Server Database

Create the production database and SQL login/user outside the app.

Minimum app permissions after schema is initialized:

- Connect to the database.
- Read/write application tables.

Run schema initialization once from the backend folder:

```powershell
cd C:\Apps\DeviationApp\Backend
.\.venv\Scripts\Activate.ps1
.\init-db.ps1
```

Keep `RUN_STARTUP_MIGRATIONS=False` after this. The app should not mutate schema on normal startup.

## 5. Create Frontend Environment

```powershell
cd C:\Apps\DeviationApp\Frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item env.sample .env
```

Edit `Frontend\.env`:

```text
DEBUG=False
FLASK_APP=run.py
FLASK_DEBUG=0
HOST=0.0.0.0
PORT=5000
SECRET_KEY=<generate-a-different-strong-unique-secret>
ASSETS_ROOT=/static/assets
BACKEND_API_URL=http://10.212.12.201:8001
FRONTEND_AUTH_MODE=backend
```

Important: production cookies are marked `Secure`, so real browser sessions require HTTPS in front of the frontend.

## 6. Verify Before Starting Services

From the project root:

```powershell
cd C:\Apps\DeviationApp
python -m pytest Backend\tests
python -m compileall -q Backend\app Frontend\apps Frontend\run.py Backend\tests
```

Verify backend config:

```powershell
cd C:\Apps\DeviationApp\Backend
.\.venv\Scripts\Activate.ps1
python -c "from app.core.config import settings; assert settings.enable_api_docs is False; assert settings.auto_create_database is False; assert settings.run_startup_migrations is False; print('backend settings ok')"
```

Verify frontend config:

```powershell
cd C:\Apps\DeviationApp\Frontend
.\.venv\Scripts\Activate.ps1
python -c "from run import app; assert app.config['DEBUG'] is False; assert app.config['SESSION_COOKIE_SECURE'] is True; print('frontend settings ok')"
```

## 7. Start Backend Manually

```powershell
cd C:\Apps\DeviationApp\Backend
.\.venv\Scripts\Activate.ps1
.\start-production.ps1
```

In another PowerShell window:

```powershell
Invoke-RestMethod http://10.212.12.201:8001/health
Invoke-RestMethod http://10.212.12.201:8001/health/db
```

Expected:

- `/health` returns `status: ok`.
- `/health/db` reports database reachable.
- `/docs`, `/redoc`, and `/openapi.json` are unavailable when `ENABLE_API_DOCS=False`.

## 8. Start Frontend Manually

```powershell
cd C:\Apps\DeviationApp\Frontend
.\.venv\Scripts\Activate.ps1
.\start-production.ps1
```

Open:

```text
http://10.212.12.201:5000
```

If HTTPS/reverse proxy is configured, open the HTTPS URL instead.

## 9. Open Firewall Ports

If users or the reverse proxy connect directly to these app ports:

```powershell
New-NetFirewallRule -DisplayName "Deviation Backend 8001" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
New-NetFirewallRule -DisplayName "Deviation Frontend 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

If IIS/reverse proxy is the only public entrypoint, expose only `80/443` publicly and keep `5000/8001` restricted.

## 10. Run As Windows Services

Manual PowerShell windows are not enough for production. Use NSSM, Windows Services, Task Scheduler, or your approved service runner.

Example NSSM commands:

```powershell
nssm install DeviationBackend powershell.exe
nssm set DeviationBackend AppParameters -ExecutionPolicy Bypass -File C:\Apps\DeviationApp\Backend\start-production.ps1
nssm set DeviationBackend AppDirectory C:\Apps\DeviationApp\Backend
nssm start DeviationBackend

nssm install DeviationFrontend powershell.exe
nssm set DeviationFrontend AppParameters -ExecutionPolicy Bypass -File C:\Apps\DeviationApp\Frontend\start-production.ps1
nssm set DeviationFrontend AppDirectory C:\Apps\DeviationApp\Frontend
nssm start DeviationFrontend
```

After restart:

```powershell
Get-Service DeviationBackend,DeviationFrontend
```

## 11. HTTPS Reverse Proxy

Configure IIS/reverse proxy so users access the frontend through HTTPS.

Recommended external URL:

```text
https://10.212.12.201/
```

Proxy target:

```text
http://127.0.0.1:5000
```

Keep backend `8001` internal unless direct API access is required.

## 12. First Admin And Smoke Test

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

## 13. Operational Rules

- Do not commit `.env` files.
- Do not run `Backend\start.ps1` for production; it uses reload.
- Do not run Flask dev server for production; use `Frontend\start-production.ps1`.
- Keep `RUN_STARTUP_MIGRATIONS=False` for normal app startup.
- Run `Backend\init-db.ps1` only as an explicit deployment/migration step.
- Back up SQL Server before schema changes.
- Keep logs outside git.

## 14. Update Deployment Later

For future releases:

```powershell
Stop-Service DeviationFrontend
Stop-Service DeviationBackend

cd C:\Apps\DeviationApp
# Copy new release files or git pull from the approved branch.

cd Backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

cd ..\Frontend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

cd ..
python -m pytest Backend\tests
python -m compileall -q Backend\app Frontend\apps Frontend\run.py Backend\tests

Start-Service DeviationBackend
Start-Service DeviationFrontend
```

