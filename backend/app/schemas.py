import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("E-mail inválido.")
    return value


# Lightweight email type (avoids the heavy email-validator dependency)
EmailStr = Annotated[str, AfterValidator(_validate_email)]


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    empresa_url: str = Field(min_length=2, max_length=80)
    admin_name: str = Field(min_length=2, max_length=120)
    admin_email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    company_id: int


# ---------- Customer (end user) ----------
class CustomerRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(default="", max_length=40)
    password: str = Field(min_length=6, max_length=128)


class CustomerLogin(BaseModel):
    email: EmailStr
    password: str


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    phone: str


# ---------- Business hours ----------
class BusinessHourIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    is_closed: bool = False
    open_time: str = "09:00"
    close_time: str = "18:00"


class BusinessHourOut(BusinessHourIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Company ----------
class CompanyUpdate(BaseModel):
    name: str | None = None
    empresa_url: str | None = None
    description: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    address_street: str | None = None
    address_number: str | None = None
    address_complement: str | None = None
    address_neighborhood: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    delivery_enabled: bool | None = None
    pickup_enabled: bool | None = None
    dine_in_enabled: bool | None = None
    delivery_fee: float | None = None
    min_order_value: float | None = None
    estimated_time: str | None = None
    pix_enabled: bool | None = None
    cash_enabled: bool | None = None
    pix_key: str | None = None
    pix_merchant_name: str | None = None
    pix_merchant_city: str | None = None
    hours: list[BusinessHourIn] | None = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    empresa_url: str
    description: str
    logo_url: str | None
    cover_url: str | None
    phone: str
    whatsapp: str
    address_street: str
    address_number: str
    address_complement: str
    address_neighborhood: str
    address_city: str
    address_state: str
    address_zip: str
    delivery_enabled: bool
    pickup_enabled: bool
    dine_in_enabled: bool
    delivery_fee: float
    min_order_value: float
    estimated_time: str
    pix_enabled: bool
    cash_enabled: bool
    pix_key: str
    pix_merchant_name: str
    pix_merchant_city: str
    hours: list[BusinessHourOut] = []


# ---------- Options ----------
class OptionIn(BaseModel):
    id: int | None = None
    name: str
    price_delta: float = 0.0
    sort_order: int = 0


class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    price_delta: float
    sort_order: int


class OptionGroupIn(BaseModel):
    id: int | None = None
    name: str
    min_select: int = 0
    max_select: int = 1
    allow_repeat: bool = False
    sort_order: int = 0
    options: list[OptionIn] = []


class OptionGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    min_select: int
    max_select: int
    allow_repeat: bool
    sort_order: int
    required: bool
    options: list[OptionOut] = []


# ---------- Menu items ----------
class MenuItemIn(BaseModel):
    name: str
    description: str = ""
    base_price: float = 0.0
    is_available: bool = True
    sort_order: int = 0
    option_groups: list[OptionGroupIn] = []


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    name: str
    description: str
    base_price: float
    image_url: str | None
    is_available: bool
    sort_order: int
    option_groups: list[OptionGroupOut] = []


# ---------- Categories ----------
class CategoryIn(BaseModel):
    name: str
    description: str = ""
    sort_order: int = 0


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    sort_order: int
    items: list[MenuItemOut] = []


# ---------- Public storefront ----------
class PublicStore(BaseModel):
    company: CompanyOut
    categories: list[CategoryOut]
    is_open_now: bool


# ---------- Orders ----------
class OrderItemOptionIn(BaseModel):
    option_id: int
    quantity: int = 1


class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, default=1)
    options: list[OrderItemOptionIn] = []
    notes: str = ""


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    customer_phone: str = Field(min_length=1, max_length=40)
    order_type: str  # delivery | pickup | dine_in
    payment_method: str  # pix | cash
    address_street: str = ""
    address_number: str = ""
    address_complement: str = ""
    address_neighborhood: str = ""
    address_reference: str = ""
    table_number: str = ""
    notes: str = ""
    change_for: float = 0.0
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    quantity: int
    unit_price: float
    total_price: float
    options_summary: str


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int | None = None
    customer_name: str
    customer_phone: str
    order_type: str
    payment_method: str
    address_street: str
    address_number: str
    address_complement: str
    address_neighborhood: str
    address_reference: str
    table_number: str
    notes: str
    change_for: float
    subtotal: float
    delivery_fee: float
    total: float
    pix_payload: str | None
    status: str
    created_at: datetime
    items: list[OrderItemOut] = []


class OrderStatusUpdate(BaseModel):
    status: str
