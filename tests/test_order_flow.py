import time
import pytest
from playwright.sync_api import Page, expect

def test_complete_order_flow(page: Page, base_url: str):
    # 1. Register a new store
    page.goto(f"{base_url}/register")
    
    timestamp = int(time.time())
    company_name = f"E2E Order Shop {timestamp}"
    company_slug = f"e2e-order-shop-{timestamp}"
    admin_name = "E2E Admin"
    admin_email = f"e2e-admin-{timestamp}@yumi.com"
    admin_password = "password123"

    page.locator('label:has-text("Nome da empresa") + input').fill(company_name)
    page.locator('label:has-text("Seu nome") + input').fill(admin_name)
    page.locator('label:has-text("E-mail") + input').fill(admin_email)
    page.locator('label:has-text("Senha") + input').fill(admin_password)
    page.locator('button:has-text("Criar minha loja")').click()

    page.wait_for_url("**/admin/orders")

    # 2. Add Category and Product
    page.locator('aside.admin-side nav.admin-nav a:has-text("Cardápio")').click()
    page.wait_for_url("**/admin/menu")

    # Click first category button (or general "+ Nova categoria" button)
    page.locator('button:has-text("Nova categoria"), button:has-text("Criar primeira categoria")').first.click()
    page.locator('form label:has-text("Nome") + input').fill("Bebidas")
    page.locator('.modal-foot button:has-text("Salvar")').click()

    # Wait for the category header to appear
    expect(page.locator('h3:has-text("Bebidas")')).to_be_visible()

    # Add product "Guaraná Antarctica"
    page.locator('button:has-text("+ Adicionar item em Bebidas")').click()
    page.locator('label:has-text("Nome do item") + input').fill("Guaraná Antarctica")
    # Base price input uses cents-shifting MoneyInput (typing "700" generates R$ 7,00)
    page.locator('label:has-text("Preço base") + input').fill("700")
    page.locator('label:has-text("Descrição") + textarea').fill("Lata 350ml bem gelada")
    page.locator('button:has-text("Salvar item")').click()

    # Wait for item row to appear
    expect(page.locator('strong:has-text("Guaraná Antarctica")')).to_be_visible()

    # 3. Log out of admin
    page.locator('button:has-text("Sair")').click()
    page.wait_for_url("**/login")

    # 4. Open public storefront
    page.goto(f"{base_url}/{company_slug}")
    page.wait_for_load_state("networkidle")

    # Click the product card
    page.locator(f'button.product-card:has(strong:has-text("Guaraná Antarctica"))').click()
    
    # Assert modal opens and click "Adicionar"
    expect(page.locator('.modal-head h3:has-text("Guaraná Antarctica")')).to_be_visible()
    page.locator('.product-foot button:has-text("Adicionar")').click()

    # 5. Open Cart and proceed to checkout
    expect(page.locator('button.cart-fab')).to_be_visible()
    page.locator('button.cart-fab').click()

    expect(page.locator('.checkout-head h2:has-text("Seu carrinho")')).to_be_visible()
    page.locator('.checkout-foot button:has-text("Continuar")').click()

    # 6. Fill checkout details
    expect(page.locator('h2:has-text("Finalizar pedido")')).to_be_visible()
    page.locator('label:has-text("Nome") + input').fill("Cliente Teste E2E")
    page.locator('label:has-text("Telefone") + input').fill("11999999999")

    # Under Delivery (default), fill address details
    page.locator('label:has-text("Rua") + input').fill("Rua das Rosas")
    page.locator('label:has-text("Número") + input').fill("123")

    # Select payment option "Pagar na entrega"
    page.locator('.seg button:has-text("Pagar na entrega")').click()

    # Submit Order
    page.locator('button:has-text("Fazer pedido")').click()

    # Assert checkout is done and order placed
    page.wait_for_selector('.checkout-done', timeout=10000)
    expect(page.locator('h2:has-text("Pedido enviado!")')).to_be_visible()

    # Go to "Acompanhar pedido"
    page.locator('button:has-text("Acompanhar pedido")').click()

    # Verify redirected to track page
    page.wait_for_url(f"**/{company_slug}/pedidos")
    expect(page.locator('.order-track-card')).to_be_visible()
    expect(page.locator('.order-track-card')).to_contain_text("Pendente")

    # 7. Log back in as admin to verify order in store terminal
    page.goto(f"{base_url}/login")
    page.locator('label:has-text("E-mail") + input').fill(admin_email)
    page.locator('label:has-text("Senha") + input').fill(admin_password)
    page.locator('button:has-text("Entrar")').click()
    page.wait_for_url("**/admin/orders")

    # Verify the order card is visible on the admin orders page with status "Pendente"
    order_card = page.locator('.order-card', has_text="Cliente Teste E2E")
    expect(order_card).to_be_visible()
    expect(order_card).to_contain_text("Pendente")

    # Advance order status (Avançar → Confirmado)
    order_card.locator('button:has-text("Avançar → Confirmado")').click()
    
    # Assert status changes to "Confirmado" in the admin dashboard
    expect(order_card).to_contain_text("Confirmado")

