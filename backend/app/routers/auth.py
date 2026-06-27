from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import BusinessHour, Company, User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from ..security import create_access_token, hash_password, verify_password
from ..utils import is_valid_slug, slugify

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _create_default_hours(company_id: int) -> list[BusinessHour]:
    hours = []
    for weekday in range(7):
        hours.append(
            BusinessHour(
                company_id=company_id,
                weekday=weekday,
                is_closed=weekday == 6,  # closed on Sunday by default
                open_time="09:00",
                close_time="22:00",
            )
        )
    return hours


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    slug = slugify(payload.empresa_url)
    if not is_valid_slug(slug):
        raise HTTPException(status_code=400, detail="empresa_url inválida.")

    if db.query(Company).filter(Company.empresa_url == slug).first():
        raise HTTPException(status_code=409, detail="Esse link público (empresa_url) já está em uso.")

    if db.query(User).filter(User.email == payload.admin_email.lower()).first():
        raise HTTPException(status_code=409, detail="Esse e-mail já está cadastrado.")

    company = Company(
        name=payload.company_name,
        empresa_url=slug,
        pix_merchant_name=payload.company_name[:25],
    )
    db.add(company)
    db.flush()  # get company.id

    for hour in _create_default_hours(company.id):
        db.add(hour)

    user = User(
        company_id=company.id,
        name=payload.admin_name,
        email=payload.admin_email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses "username" — we treat it as the email.
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login-json", response_model=TokenResponse)
def login_json(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
