# Frontend

Flask frontend for the deviation application. Docker is not used.

For local development, the frontend is configured to call the FastAPI backend at `http://127.0.0.1:8001`.

## Start the backend first

```powershell
cd ..\Backend
python -m uvicorn app.main:app --reload --port 8001
```

## Run locally

```powershell
cd Frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item env.sample .env
python run.py
```

Open http://127.0.0.1:5000

You can also run:

```powershell
cd Frontend
.\start.ps1
```

For production-style hosting on Windows, install requirements and run:

```powershell
cd Frontend
.\start-production.ps1
```

## Testing Deployment

For a shared testing server, set these values in `Frontend\.env`:

```text
DEBUG=False
SECRET_KEY=<strong testing secret>
HOST=0.0.0.0
PORT=5000
BACKEND_API_URL=http://<backend-host>:8001
```

Use the repository-level `DEPLOYMENT_TESTING.md` checklist before handing the app to testers.

## Production Notes

- Use `DEBUG=False` and `FLASK_DEBUG=0`.
- Set a unique `SECRET_KEY` with at least 32 characters.
- Point `BACKEND_API_URL` at the deployed backend URL.
- Serve the frontend over HTTPS; production cookies are marked `Secure`.
- Run `start-production.ps1` behind a production process manager or reverse proxy instead of the Flask development server.
- Keep `.env` and runtime logs out of source control.
