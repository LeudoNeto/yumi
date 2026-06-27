from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    # public slug used in the storefront url: /{empresa_url}
    empresa_url: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    phone: Mapped[str] = mapped_column(String(40), default="")
    whatsapp: Mapped[str] = mapped_column(String(40), default="")

    # Address
    address_street: Mapped[str] = mapped_column(String(160), default="")
    address_number: Mapped[str] = mapped_column(String(20), default="")
    address_complement: Mapped[str] = mapped_column(String(120), default="")
    address_neighborhood: Mapped[str] = mapped_column(String(120), default="")
    address_city: Mapped[str] = mapped_column(String(120), default="")
    address_state: Mapped[str] = mapped_column(String(40), default="")
    address_zip: Mapped[str] = mapped_column(String(20), default="")

    # Order / fulfillment settings
    delivery_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pickup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    dine_in_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    delivery_fee: Mapped[float] = mapped_column(Float, default=0.0)
    min_order_value: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_time: Mapped[str] = mapped_column(String(60), default="30-45 min")

    # Payment settings
    pix_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cash_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pix_key: Mapped[str] = mapped_column(String(160), default="")
    pix_merchant_name: Mapped[str] = mapped_column(String(60), default="")
    pix_merchant_city: Mapped[str] = mapped_column(String(60), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    users: Mapped[list["User"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    hours: Mapped[list["BusinessHour"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", order_by="BusinessHour.weekday"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", order_by="Category.sort_order"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    company: Mapped[Company] = relationship(back_populates="users")


class Customer(Base):
    """End customer account — global (works across all stores), like iFood."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(40), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class BusinessHour(Base):
    __tablename__ = "business_hours"
    __table_args__ = (UniqueConstraint("company_id", "weekday", name="uq_company_weekday"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Monday ... 6=Sunday
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    open_time: Mapped[str] = mapped_column(String(5), default="09:00")  # "HH:MM"
    close_time: Mapped[str] = mapped_column(String(5), default="18:00")

    company: Mapped[Company] = relationship(back_populates="hours")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    company: Mapped[Company] = relationship(back_populates="categories")
    items: Mapped[list["MenuItem"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", order_by="MenuItem.sort_order"
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    base_price: Mapped[float] = mapped_column(Float, default=0.0)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    category: Mapped[Category] = relationship(back_populates="items")
    option_groups: Mapped[list["OptionGroup"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="OptionGroup.sort_order"
    )


class OptionGroup(Base):
    """A section of options for an item, e.g. 'Choose your size' or 'Add-ons'."""

    __tablename__ = "option_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    min_select: Mapped[int] = mapped_column(Integer, default=0)
    max_select: Mapped[int] = mapped_column(Integer, default=1)
    # if true, the same option can be picked more than once (quantity stepper)
    allow_repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    item: Mapped[MenuItem] = relationship(back_populates="option_groups")
    options: Mapped[list["Option"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", order_by="Option.sort_order"
    )

    @property
    def required(self) -> bool:
        return self.min_select > 0


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("option_groups.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    price_delta: Mapped[float] = mapped_column(Float, default=0.0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    group: Mapped[OptionGroup] = relationship(back_populates="options")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )

    customer_name: Mapped[str] = mapped_column(String(120))
    customer_phone: Mapped[str] = mapped_column(String(40))

    order_type: Mapped[str] = mapped_column(String(20))  # delivery | pickup | dine_in
    payment_method: Mapped[str] = mapped_column(String(20))  # pix | cash

    # delivery address (only for delivery)
    address_street: Mapped[str] = mapped_column(String(160), default="")
    address_number: Mapped[str] = mapped_column(String(20), default="")
    address_complement: Mapped[str] = mapped_column(String(120), default="")
    address_neighborhood: Mapped[str] = mapped_column(String(120), default="")
    address_reference: Mapped[str] = mapped_column(String(160), default="")

    # dine-in
    table_number: Mapped[str] = mapped_column(String(20), default="")

    notes: Mapped[str] = mapped_column(Text, default="")
    change_for: Mapped[float] = mapped_column(Float, default=0.0)  # troco para (cash)

    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_fee: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)

    pix_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | confirmed | preparing | ready | delivering | completed | cancelled

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    company: Mapped[Company] = relationship(back_populates="orders")
    customer: Mapped["Customer | None"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)  # base + options, per unit
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    # snapshot of selected options: [{group, name, quantity, price_delta}, ...]
    options_summary: Mapped[str] = mapped_column(Text, default="")

    order: Mapped[Order] = relationship(back_populates="items")
