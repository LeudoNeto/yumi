from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_customer
from ..models import Company, Customer, Order
from ..schemas import (
    CustomerLogin,
    CustomerOut,
    CustomerRegister,
    OrderOut,
    TokenResponse,
)
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/customer", tags=["customer"])


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: CustomerRegister, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(Customer).filter(Customer.email == email).first():
        raise HTTPException(status_code=409, detail="Esse e-mail já tem uma conta.")
    customer = Customer(
        name=payload.name,
        email=email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return TokenResponse(access_token=create_access_token(customer.id, "customer"))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: CustomerLogin, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.email == payload.email.lower()).first()
    if not customer or not verify_password(payload.password, customer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos."
        )
    return TokenResponse(access_token=create_access_token(customer.id, "customer"))


@router.get("/auth/me", response_model=CustomerOut)
def me(customer: Customer = Depends(get_current_customer)):
    return customer


@router.get("/orders", response_model=list[OrderOut])
def my_orders(
    empresa_url: str | None = None,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    """Orders for the logged-in customer, optionally scoped to one store."""
    query = db.query(Order).filter(Order.customer_id == customer.id)
    if empresa_url:
        company = db.query(Company).filter(Company.empresa_url == empresa_url.lower()).first()
        if not company:
            return []
        query = query.filter(Order.company_id == company.id)
    return query.order_by(Order.created_at.desc()).all()
