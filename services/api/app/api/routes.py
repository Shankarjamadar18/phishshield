import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db import check_db, get_db
from ..models import Scan
from ..detection.url import InvalidURL, analyze_url
from ..schemas import DependencyStatus, HealthOut, ReadyOut, ScanCreate, ScanOut

VERSION = "0.2.0"
router = APIRouter()
log = logging.getLogger("phishshield.api")


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Liveness: the process is running. Does not touch dependencies."""
    return HealthOut(status="ok", service=get_settings().app_name, version=VERSION)


@router.get("/health/live", include_in_schema=False)
def live() -> HealthOut:
    return health()


@router.get("/ready", response_model=ReadyOut)
def ready(response: Response) -> ReadyOut:
    """Readiness: checks every required dependency. 503 when any is down."""
    try:
        check_db()
        db = DependencyStatus(status="up")
    except Exception as exc:
        log.exception("database readiness check failed")
        db = DependencyStatus(status="down", error=type(exc).__name__)
    is_ready = db.status == "up"
    if not is_ready:
        response.status_code = 503
    return ReadyOut(status="ready" if is_ready else "not_ready", dependencies={"database": db})


@router.post("/api/v1/scans", response_model=ScanOut, status_code=201)
def create_scan(body: ScanCreate, db: Session = Depends(get_db)) -> Scan:
    details = {}
    if body.scan_type == "url":
        try:
            details = analyze_url(body.input_value)
        except InvalidURL as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    scan = Scan(scan_type=body.scan_type, input_value=body.input_value.strip(),
                status="completed" if details else "pending",
                verdict=details.get("verdict"), risk_score=None, details=details)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/api/v1/scans", response_model=list[ScanOut])
def list_scans(limit: int = 20, db: Session = Depends(get_db)) -> list[Scan]:
    limit = max(1, min(limit, 100))
    return list(db.scalars(select(Scan).order_by(Scan.created_at.desc()).limit(limit)))


@router.get("/api/v1/scans/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: uuid.UUID, db: Session = Depends(get_db)) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
