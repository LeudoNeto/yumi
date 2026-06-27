"""Seed the database with a demo company so you can try the storefront quickly.

Run from the backend directory:  python seed.py
Demo admin login:  admin@yumi.com / yumi1234
Storefront:        http://localhost:5173/yumi-sushi
"""
from app.database import SessionLocal, init_db
from app.models import (
    BusinessHour,
    Category,
    Company,
    MenuItem,
    Option,
    OptionGroup,
    User,
)
from app.security import hash_password

init_db()


def run():
    db = SessionLocal()
    try:
        if db.query(Company).filter(Company.empresa_url == "yumi-sushi").first():
            print("Demo company already exists, skipping.")
            return

        company = Company(
            name="Yumi Sushi & Bowls",
            empresa_url="yumi-sushi",
            description="Comida japonesa fresquinha, bowls e poke feitos na hora. 🍜",
            phone="(11) 4002-8922",
            whatsapp="(11) 94002-8922",
            address_street="Rua das Cerejeiras",
            address_number="123",
            address_neighborhood="Liberdade",
            address_city="São Paulo",
            address_state="SP",
            address_zip="01000-000",
            delivery_fee=7.90,
            min_order_value=25.0,
            estimated_time="30-45 min",
            pix_enabled=True,
            cash_enabled=True,
            pix_key="yumi-sushi@example.com",
            pix_merchant_name="YUMI SUSHI",
            pix_merchant_city="SAO PAULO",
        )
        db.add(company)
        db.flush()

        for wd in range(7):
            db.add(
                BusinessHour(
                    company_id=company.id,
                    weekday=wd,
                    is_closed=False,
                    open_time="11:00",
                    close_time="23:00",
                )
            )

        db.add(
            User(
                company_id=company.id,
                name="Administrador Yumi",
                email="admin@yumi.com",
                hashed_password=hash_password("yumi1234"),
            )
        )

        # ---- Categories & items ----
        bowls = Category(company_id=company.id, name="Bowls", description="Nossos famosos bowls", sort_order=0)
        temaki = Category(company_id=company.id, name="Temaki", sort_order=1)
        bebidas = Category(company_id=company.id, name="Bebidas", sort_order=2)
        db.add_all([bowls, temaki, bebidas])
        db.flush()

        # Bowl with options
        poke = MenuItem(
            category_id=bowls.id,
            name="Poke Bowl",
            description="Base de arroz, proteína à escolha, vegetais e molho especial.",
            base_price=32.90,
            sort_order=0,
        )
        db.add(poke)
        db.flush()

        g_base = OptionGroup(item_id=poke.id, name="Escolha a base", min_select=1, max_select=1, allow_repeat=False, sort_order=0)
        g_prot = OptionGroup(item_id=poke.id, name="Proteína", min_select=1, max_select=2, allow_repeat=False, sort_order=1)
        g_add = OptionGroup(item_id=poke.id, name="Adicionais", min_select=0, max_select=5, allow_repeat=True, sort_order=2)
        db.add_all([g_base, g_prot, g_add])
        db.flush()

        db.add_all([
            Option(group_id=g_base.id, name="Arroz japonês", price_delta=0.0, sort_order=0),
            Option(group_id=g_base.id, name="Mix de folhas", price_delta=0.0, sort_order=1),
            Option(group_id=g_prot.id, name="Salmão", price_delta=0.0, sort_order=0),
            Option(group_id=g_prot.id, name="Atum", price_delta=4.0, sort_order=1),
            Option(group_id=g_prot.id, name="Frango", price_delta=0.0, sort_order=2),
            Option(group_id=g_add.id, name="Cream cheese", price_delta=3.5, sort_order=0),
            Option(group_id=g_add.id, name="Abacate", price_delta=4.0, sort_order=1),
            Option(group_id=g_add.id, name="Gergelim", price_delta=1.5, sort_order=2),
        ])

        hot = MenuItem(
            category_id=bowls.id,
            name="Hot Bowl Salmão",
            description="Salmão empanado, arroz, cream cheese e molho tarê.",
            base_price=36.90,
            sort_order=1,
        )
        db.add(hot)

        # Temaki with single-choice option
        tmk = MenuItem(
            category_id=temaki.id,
            name="Temaki Salmão",
            description="Cone de alga recheado com arroz e salmão fresco.",
            base_price=24.90,
            sort_order=0,
        )
        db.add(tmk)
        db.flush()
        g_size = OptionGroup(item_id=tmk.id, name="Tamanho", min_select=1, max_select=1, allow_repeat=False, sort_order=0)
        db.add(g_size)
        db.flush()
        db.add_all([
            Option(group_id=g_size.id, name="Tradicional", price_delta=0.0, sort_order=0),
            Option(group_id=g_size.id, name="Jumbo", price_delta=8.0, sort_order=1),
        ])

        db.add_all([
            MenuItem(category_id=bebidas.id, name="Refrigerante lata", base_price=6.0, sort_order=0),
            MenuItem(category_id=bebidas.id, name="Suco natural", base_price=9.0, sort_order=1),
            MenuItem(category_id=bebidas.id, name="Água sem gás", base_price=4.0, sort_order=2),
        ])

        db.commit()
        print("Seed completed!")
        print("  Admin login:  admin@yumi.com / yumi1234")
        print("  Storefront:   http://localhost:5173/yumi-sushi")
    finally:
        db.close()


if __name__ == "__main__":
    run()
