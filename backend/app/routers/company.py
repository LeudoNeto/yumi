import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..database import get_db
from ..deps import get_current_user
from ..models import BusinessHour, Company, User
from ..schemas import CompanyOut, CompanyUpdate
from ..utils import is_valid_slug, slugify

router = APIRouter(prefix="/api/company", tags=["company"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
EXT_BY_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _get_company(current_user: User, db: Session) -> Company:
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return company


def _save_upload(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")
    ext = EXT_BY_TYPE.get(file.content_type, ".png")
    filename = f"{secrets.token_hex(16)}{ext}"
    dest = UPLOAD_DIR / filename
    contents = file.file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagem muito grande (máx 5MB).")
    dest.write_bytes(contents)
    return f"/uploads/{filename}"


@router.get("", response_model=CompanyOut)
def get_my_company(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_company(current_user, db)


@router.patch("", response_model=CompanyOut)
def update_my_company(
    payload: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = _get_company(current_user, db)
    data = payload.model_dump(exclude_unset=True)

    hours = data.pop("hours", None)

    if "empresa_url" in data and data["empresa_url"] is not None:
        slug = slugify(data["empresa_url"])
        if not is_valid_slug(slug):
            raise HTTPException(status_code=400, detail="empresa_url inválida.")
        existing = db.query(Company).filter(Company.empresa_url == slug, Company.id != company.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Esse link público já está em uso.")
        data["empresa_url"] = slug

    for key, value in data.items():
        setattr(company, key, value)

    if hours is not None:
        # replace all business hours
        for existing in list(company.hours):
            db.delete(existing)
        db.flush()
        for h in hours:
            db.add(BusinessHour(company_id=company.id, **h))

    db.commit()
    db.refresh(company)
    return company


@router.post("/logo", response_model=CompanyOut)
def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = _get_company(current_user, db)
    company.logo_url = _save_upload(file)
    db.commit()
    db.refresh(company)
    return company


@router.post("/cover", response_model=CompanyOut)
def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = _get_company(current_user, db)
    company.cover_url = _save_upload(file)
    db.commit()
    db.refresh(company)
    return company
