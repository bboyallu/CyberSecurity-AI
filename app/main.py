from __future__ import annotations

from datetime import datetime, timezone
import random
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="CyberShield AI", version="0.1.0")


def _static_dir() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        candidates = [
            base_dir / "app" / "static",
            base_dir / "static",
        ]
    else:
        candidates = [Path(__file__).resolve().parent / "static"]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    raise RuntimeError(
        "Static assets directory not found. Ensure the build bundles app/static."
    )


app.mount("/", StaticFiles(directory=_static_dir(), html=True), name="static")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: dict[str, Any] | None = None


class ScanRequest(BaseModel):
    target: str = Field(..., min_length=2, max_length=200)
    depth: str = Field("standard", pattern="^(quick|standard|deep)$")


ALERTS: list[dict[str, Any]] = []

THREAT_LIBRARY = [
    "Suspicious outbound DNS tunneling detected",
    "Unusual privilege escalation on endpoint",
    "Unauthorized login attempts spiked",
    "Known malware signature flagged in temp directory",
    "Possible lateral movement via SMB",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _add_alert(summary: str, severity: str = "high") -> dict[str, Any]:
    alert = {
        "id": f"ALERT-{len(ALERTS) + 1:04d}",
        "summary": summary,
        "severity": severity,
        "timestamp": _utc_now(),
    }
    ALERTS.insert(0, alert)
    return alert


@app.post("/api/chat")
async def chat(request: ChatRequest) -> JSONResponse:
    message = request.message.strip().lower()
    if "scan" in message:
        response = (
            "I can run a threat scan. Tell me the target (endpoint, subnet, or log path) "
            "and the depth: quick, standard, or deep."
        )
    elif "alert" in message or "compromise" in message:
        response = (
            "I am monitoring live telemetry. You can fetch recent alerts or launch an immediate scan."
        )
    else:
        response = (
            "CyberShield AI is ready. I correlate endpoint, network, and log signals to flag risks. "
            "Ask for scans, mitigation steps, or incident summaries."
        )
    return JSONResponse({"response": response, "timestamp": _utc_now()})


@app.post("/api/scan")
async def scan(request: ScanRequest) -> JSONResponse:
    findings = random.sample(THREAT_LIBRARY, k=2)
    if request.depth == "deep":
        findings.append("Zero-day heuristic anomaly detected in memory")
    risk_score = random.randint(68, 94) if request.depth != "quick" else random.randint(40, 70)
    if risk_score > 80:
        _add_alert(f"{request.target}: {findings[0]}", severity="critical")
    return JSONResponse(
        {
            "target": request.target,
            "depth": request.depth,
            "risk_score": risk_score,
            "findings": findings,
            "timestamp": _utc_now(),
        }
    )


@app.get("/api/alerts")
async def alerts() -> JSONResponse:
    if not ALERTS:
        _add_alert("No active compromises, baseline monitoring active", severity="low")
    return JSONResponse({"alerts": ALERTS[:5], "timestamp": _utc_now()})
