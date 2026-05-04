# Frontend

Local Flask frontend only. Docker is not used.

The frontend is configured to call the FastAPI backend at `http://127.0.0.1:8001`.

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
python run.py
```

Open http://127.0.0.1:5000

You can also run:

```powershell
cd Frontend
.\start.ps1
```
