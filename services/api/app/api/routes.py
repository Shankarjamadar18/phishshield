import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..db import check_db, get_db
from ..models import Scan
from ..schemas import HealthOut, ScanCreate, ScanOut

VERSION = "0.1.0"
router = APIRouter()
log = logging.getLogger("phishshield.api")


@router.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    try:
        db_up = check_db()
    except Exception:
        log.exception("database health check failed")
        db_up = False
    return HealthOut(
        status="ok" if db_up else "degraded",
        service=get_settings().app_name,
        version=VERSION,
        database="up" if db_up else "down",
    )


@router.post("/api/v1/scans", response_model=ScanOut, status_code=201)
def create_scan(body: ScanCreate, db: Session = Depends(get_db)) -> Scan:
    # Phase 1: persist the request only. No detector exists yet, so no verdict is produced.
    scan = Scan(scan_type=body.scan_type, input_value=body.input_value, status="pending", details={})
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/api/v1/scans", response_model=list[ScanOut])
def list_scans(limit: int = 20, db: Session = Depends(get_db)) -> list[Scan]:
    limit = max(1, min(limit, 100))
    return list(db.scalars(select(Scan).order_by(Scan.created_at.desc()).limit(limit)))
