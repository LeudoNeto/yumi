from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Customer, User
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
customer_scheme = OAuth2PasswordBearer(tokenUrl="api/customer/auth/login")

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        # tokens without a type are legacy admin tokens
        if user_id is None or payload.get("type", "admin") != "admin":
            raise _credentials_exc
    except InvalidTokenError:
        raise _credentials_exc

    user = db.get(User, int(user_id))
    if user is None:
        raise _credentials_exc
    return user


def get_current_customer(
    token: str = Depends(customer_scheme), db: Session = Depends(get_db)
) -> Customer:
    try:
        payload = decode_token(token)
        customer_id = payload.get("sub")
        if customer_id is None or payload.get("type") != "customer":
            raise _credentials_exc
    except InvalidTokenError:
        raise _credentials_exc

    customer = db.get(Customer, int(customer_id))
    if customer is None:
        raise _credentials_exc
    return customer


def get_optional_customer(request: Request, db: Session = Depends(get_db)) -> Customer | None:
    """Return the logged-in customer if a valid customer token is present, else None.

    Used on the public order endpoint so a logged-in customer's order links to them,
    while guests can still order anonymously.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    try:
        payload = decode_token(token)
        if payload.get("type") != "customer":
            return None
        customer_id = payload.get("sub")
        if customer_id is None:
            return None
        return db.get(Customer, int(customer_id))
    except (InvalidTokenError, ValueError):
        return None
