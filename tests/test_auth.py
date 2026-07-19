import time
import pytest
from playwright.sync_api import Page, expect

def test_registration_and_login(page: Page, base_url: str):
    # 1. Registration Flow
    page.goto(f"{base_url}/register")
    
    timestamp = int(time.time())
    company_name = f"Test Store {timestamp}"
    company_slug = f"test-store-{timestamp}"
    admin_name = "Admin Test User"
    admin_email = f"admin-{timestamp}@yumi.com"
    admin_password = "password123"

    # Fill Company details
    page.locator('label:has-text("Nome da empresa") + input').fill(company_name)
    
    # Check if slug is auto-generated and has the expected value
    expect(page.locator('label:has-text("Link público (empresa_url)") + input')).to_have_value(company_slug)

    # Fill Admin credentials
    page.locator('label:has-text("Seu nome") + input').fill(admin_name)
    page.locator('label:has-text("E-mail") + input').fill(admin_email)
    page.locator('label:has-text("Senha") + input').fill(admin_password)

    # Submit form
    page.locator('button:has-text("Criar minha loja")').click()

    # Assert redirect to admin panel
    page.wait_for_url("**/admin/orders")
    expect(page.locator('aside.admin-side')).to_be_visible()
    expect(page.locator('.admin-brand')).to_contain_text("Painel do admin")
    expect(page.locator('.admin-brand')).to_contain_text(company_name)

    # Logout
    page.locator('button:has-text("Sair")').click()
    page.wait_for_url("**/login")

    # 2. Login Flow with newly created account
    page.locator('label:has-text("E-mail") + input').fill(admin_email)
    page.locator('label:has-text("Senha") + input').fill(admin_password)
    page.locator('button:has-text("Entrar")').click()

    # Assert redirected back to admin panel
    page.wait_for_url("**/admin/orders")
    expect(page.locator('aside.admin-side')).to_be_visible()
