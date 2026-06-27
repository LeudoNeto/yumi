from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company
from ..schemas import PublicStore

router = APIRouter(prefix="/api/public", tags=["public"])


def is_open_now(company: Company, ref: datetime | None = None) -> bool:
    ref = ref or datetime.now()
    weekday = ref.weekday()  # Monday=0
    today = next((h for h in company.hours if h.weekday == weekday), None)
    if not today or today.is_closed:
        return False
    try:
        oh, om = map(int, today.open_time.split(":"))
        ch, cm = map(int, today.close_time.split(":"))
    except ValueError:
        return False
    now_minutes = ref.hour * 60 + ref.minute
    open_minutes = oh * 60 + om
    close_minutes = ch * 60 + cm
    if close_minutes <= open_minutes:
        # crosses midnight (e.g. 18:00 -> 02:00)
        return now_minutes >= open_minutes or now_minutes < close_minutes
    return open_minutes <= now_minutes < close_minutes


def get_company_by_slug(empresa_url: str, db: Session) -> Company:
    company = db.query(Company).filter(Company.empresa_url == empresa_url.lower()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")
    return company


@router.get("/{empresa_url}", response_model=PublicStore)
def get_store(empresa_url: str, db: Session = Depends(get_db)):
    company = get_company_by_slug(empresa_url, db)
    # only expose available items / non-empty categories on the public view
    categories = sorted(company.categories, key=lambda c: (c.sort_order, c.id))
    return PublicStore(
        company=company,
        categories=categories,
        is_open_now=is_open_now(company),
    )
