from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Category, MenuItem, Option, OptionGroup, User
from ..schemas import (
    CategoryIn,
    CategoryOut,
    MenuItemIn,
    MenuItemOut,
)
from .company import _save_upload

router = APIRouter(prefix="/api/menu", tags=["menu"])


# ---------- helpers ----------
def _own_category(category_id: int, user: User, db: Session) -> Category:
    cat = db.get(Category, category_id)
    if not cat or cat.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return cat


def _own_item(item_id: int, user: User, db: Session) -> MenuItem:
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    if item.category.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return item


def _apply_option_groups(item: MenuItem, groups_in, db: Session):
    """Replace all option groups/options of an item with the provided structure."""
    for grp in list(item.option_groups):
        db.delete(grp)
    db.flush()
    for gi, grp in enumerate(groups_in):
        group = OptionGroup(
            item_id=item.id,
            name=grp.name,
            min_select=grp.min_select,
            max_select=max(grp.max_select, 1),
            allow_repeat=grp.allow_repeat,
            sort_order=grp.sort_order or gi,
        )
        db.add(group)
        db.flush()
        for oi, opt in enumerate(grp.options):
            db.add(
                Option(
                    group_id=group.id,
                    name=opt.name,
                    price_delta=opt.price_delta,
                    sort_order=opt.sort_order or oi,
                )
            )


# ---------- categories ----------
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Category)
        .filter(Category.company_id == current_user.company_id)
        .order_by(Category.sort_order, Category.id)
        .all()
    )


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.query(Category).filter(Category.company_id == current_user.company_id).count()
    cat = Category(
        company_id=current_user.company_id,
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order or count,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = _own_category(category_id, current_user, db)
    cat.name = payload.name
    cat.description = payload.description
    cat.sort_order = payload.sort_order
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = _own_category(category_id, current_user, db)
    db.delete(cat)
    db.commit()


# ---------- items ----------
@router.post("/categories/{category_id}/items", response_model=MenuItemOut, status_code=201)
def create_item(
    category_id: int,
    payload: MenuItemIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cat = _own_category(category_id, current_user, db)
    count = db.query(MenuItem).filter(MenuItem.category_id == cat.id).count()
    item = MenuItem(
        category_id=cat.id,
        name=payload.name,
        description=payload.description,
        base_price=payload.base_price,
        is_available=payload.is_available,
        sort_order=payload.sort_order or count,
    )
    db.add(item)
    db.flush()
    _apply_option_groups(item, payload.option_groups, db)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=MenuItemOut)
def update_item(
    item_id: int,
    payload: MenuItemIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _own_item(item_id, current_user, db)
    item.name = payload.name
    item.description = payload.description
    item.base_price = payload.base_price
    item.is_available = payload.is_available
    item.sort_order = payload.sort_order
    _apply_option_groups(item, payload.option_groups, db)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _own_item(item_id, current_user, db)
    db.delete(item)
    db.commit()


@router.post("/items/{item_id}/image", response_model=MenuItemOut)
def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _own_item(item_id, current_user, db)
    item.image_url = _save_upload(file)
    db.commit()
    db.refresh(item)
    return item
