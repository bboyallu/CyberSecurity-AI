# CyberShield AI

CyberShield AI is a lightweight demo of an autonomous cybersecurity command center. It provides:

- **Neural Sentinel UI** for threat scans and incident status.
- **AI chatbot** that supports incident triage conversations.
- **Voice-enabled responses** (browser speech synthesis).
- **Continuous alerting** for risky findings.

> Note: This is a simulation scaffold. Replace the heuristics with your own ML/LLM pipelines, telemetry collectors, and endpoint agents.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Windows `.exe` build

Use PyInstaller to bundle the app and its static assets. Run these commands in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --onefile --name CyberShieldAI --add-data "app/static;app/static" app/run.py

# Alternative if you prefer a flatter bundle layout:
# pyinstaller --onefile --name CyberShieldAI --add-data "app/static;static" app/run.py
```

The executable will be available at `dist\CyberShieldAI.exe`. Launch it and visit
`http://localhost:8000`.

## API

- `POST /api/chat` → conversational assistant
- `POST /api/scan` → simulated scan report
- `GET /api/alerts` → recent alerts

## Next steps

- Connect to EDR/network sensors and stream telemetry.
- Swap the rule-based assistant with a production LLM + tool orchestration stack.
- Emit alerts to SIEM, SOAR, or pager workflows.
