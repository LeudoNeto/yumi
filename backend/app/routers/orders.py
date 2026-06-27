from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_optional_customer
from ..models import Customer, MenuItem, Option, Order, OrderItem, User
from ..pix import build_pix_payload
from ..schemas import OrderCreate, OrderOut, OrderStatusUpdate
from .public import get_company_by_slug

router = APIRouter(tags=["orders"])

VALID_TYPES = {"delivery", "pickup", "dine_in"}
VALID_PAYMENTS = {"pix", "cash"}
VALID_STATUSES = {
    "pending",
    "confirmed",
    "preparing",
    "ready",
    "delivering",
    "completed",
    "cancelled",
}


# ---------- public: create an order ----------
@router.post("/api/public/{empresa_url}/orders", response_model=OrderOut, status_code=201)
def create_order(
    empresa_url: str,
    payload: OrderCreate,
    db: Session = Depends(get_db),
    customer: Customer | None = Depends(get_optional_customer),
):
    company = get_company_by_slug(empresa_url, db)

    if payload.order_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de pedido inválido.")
    if payload.payment_method not in VALID_PAYMENTS:
        raise HTTPException(status_code=400, detail="Forma de pagamento inválida.")

    # fulfillment availability
    type_enabled = {
        "delivery": company.delivery_enabled,
        "pickup": company.pickup_enabled,
        "dine_in": company.dine_in_enabled,
    }
    if not type_enabled[payload.order_type]:
        raise HTTPException(status_code=400, detail="Essa forma de recebimento não está disponível.")

    # payment rules: cash only allowed for delivery (pagar na entrega)
    if payload.payment_method == "cash" and payload.order_type != "delivery":
        raise HTTPException(
            status_code=400, detail="Pagamento na entrega só está disponível para delivery."
        )
    if payload.payment_method == "pix" and not company.pix_enabled:
        raise HTTPException(status_code=400, detail="PIX não está habilitado para esta loja.")
    if payload.payment_method == "cash" and not company.cash_enabled:
        raise HTTPException(status_code=400, detail="Pagamento na entrega não está habilitado.")

    if not payload.items:
        raise HTTPException(status_code=400, detail="O carrinho está vazio.")

    if payload.order_type == "delivery" and not (payload.address_street and payload.address_number):
        raise HTTPException(status_code=400, detail="Endereço de entrega é obrigatório.")

    order = Order(
        company_id=company.id,
        customer_id=customer.id if customer else None,
        customer_name=payload.customer_name.strip(),
        customer_phone=payload.customer_phone.strip(),
        order_type=payload.order_type,
        payment_method=payload.payment_method,
        address_street=payload.address_street,
        address_number=payload.address_number,
        address_complement=payload.address_complement,
        address_neighborhood=payload.address_neighborhood,
        address_reference=payload.address_reference,
        table_number=payload.table_number,
        notes=payload.notes,
        change_for=payload.change_for,
    )

    subtotal = 0.0
    order_items: list[OrderItem] = []

    for line in payload.items:
        menu_item = db.get(MenuItem, line.menu_item_id)
        if not menu_item or menu_item.category.company_id != company.id:
            raise HTTPException(status_code=400, detail="Item inválido no pedido.")
        if not menu_item.is_available:
            raise HTTPException(status_code=400, detail=f"'{menu_item.name}' está indisponível.")

        # validate selected options against the item's groups
        valid_option_ids = {
            opt.id: opt for grp in menu_item.option_groups for opt in grp.options
        }
        group_counts: dict[int, int] = {}
        unit_price = menu_item.base_price
        summary_parts: list[str] = []

        for sel in line.options:
            opt: Option | None = valid_option_ids.get(sel.option_id)
            if not opt:
                raise HTTPException(
                    status_code=400, detail=f"Opção inválida para '{menu_item.name}'."
                )
            qty = max(1, sel.quantity)
            if qty > 1 and not opt.group.allow_repeat:
                raise HTTPException(
                    status_code=400,
                    detail=f"A opção '{opt.name}' não pode ser escolhida mais de uma vez.",
                )
            group_counts[opt.group_id] = group_counts.get(opt.group_id, 0) + qty
            unit_price += opt.price_delta * qty
            label = opt.name if qty == 1 else f"{qty}x {opt.name}"
            summary_parts.append(label)

        # validate min/max per group
        for grp in menu_item.option_groups:
            chosen = group_counts.get(grp.id, 0)
            if chosen < grp.min_select:
                raise HTTPException(
                    status_code=400,
                    detail=f"Escolha pelo menos {grp.min_select} em '{grp.name}'.",
                )
            if chosen > grp.max_select:
                raise HTTPException(
                    status_code=400,
                    detail=f"Escolha no máximo {grp.max_select} em '{grp.name}'.",
                )

        line_total = unit_price * line.quantity
        subtotal += line_total
        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                name=menu_item.name,
                quantity=line.quantity,
                unit_price=round(unit_price, 2),
                total_price=round(line_total, 2),
                options_summary=", ".join(summary_parts),
            )
        )

    if company.min_order_value and subtotal < company.min_order_value:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido mínimo de R$ {company.min_order_value:.2f}.",
        )

    delivery_fee = company.delivery_fee if payload.order_type == "delivery" else 0.0
    total = round(subtotal + delivery_fee, 2)

    order.subtotal = round(subtotal, 2)
    order.delivery_fee = round(delivery_fee, 2)
    order.total = total
    order.items = order_items

    if payload.payment_method == "pix" and company.pix_key:
        order.pix_payload = build_pix_payload(
            pix_key=company.pix_key,
            merchant_name=company.pix_merchant_name or company.name,
            merchant_city=company.pix_merchant_city or company.address_city or "BRASIL",
            amount=total,
            txid=f"YUMI{company.id}",
        )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


# ---------- public: track a single order by id (for guests) ----------
@router.get("/api/public/{empresa_url}/orders/{order_id}", response_model=OrderOut)
def track_order(empresa_url: str, order_id: int, db: Session = Depends(get_db)):
    company = get_company_by_slug(empresa_url, db)
    order = db.get(Order, order_id)
    if not order or order.company_id != company.id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return order


# ---------- admin: manage orders ----------
@router.get("/api/orders", response_model=list[OrderOut])
def list_orders(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Order)
        .filter(Order.company_id == current_user.company_id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order or order.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return order


@router.patch("/api/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order or order.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Status inválido.")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
