"""Unit tests for app.schemas (Pydantic validation)."""
import pytest
from pydantic import ValidationError

from app.schemas import (
    OrderCreate,
    OrderItemIn,
    RegisterRequest,
    CustomerRegister,
)


class TestEmailValidation:
    def test_valid_email(self):
        req = RegisterRequest(
            company_name="Test",
            empresa_url="test",
            admin_name="Admin",
            admin_email="user@example.com",
            password="123456",
        )
        assert req.admin_email == "user@example.com"

    def test_email_normalized_lowercase(self):
        req = RegisterRequest(
            company_name="Test",
            empresa_url="test",
            admin_name="Admin",
            admin_email="USER@EXAMPLE.COM",
            password="123456",
        )
        assert req.admin_email == "user@example.com"

    def test_email_stripped(self):
        req = RegisterRequest(
            company_name="Test",
            empresa_url="test",
            admin_name="Admin",
            admin_email="  user@example.com  ",
            password="123456",
        )
        assert req.admin_email == "user@example.com"

    def test_invalid_email_no_at(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                company_name="Test",
                empresa_url="test",
                admin_name="Admin",
                admin_email="invalid-email",
                password="123456",
            )

    def test_invalid_email_no_domain(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                company_name="Test",
                empresa_url="test",
                admin_name="Admin",
                admin_email="user@",
                password="123456",
            )

    def test_invalid_email_spaces(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                company_name="Test",
                empresa_url="test",
                admin_name="Admin",
                admin_email="user @example.com",
                password="123456",
            )


class TestRegisterRequest:
    def test_company_name_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                company_name="A",
                empresa_url="test",
                admin_name="Admin",
                admin_email="a@b.com",
                password="123456",
            )

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                company_name="Test Company",
                empresa_url="test",
                admin_name="Admin",
                admin_email="a@b.com",
                password="12345",  # min 6
            )

    def test_admin_name_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                company_name="Test Company",
                empresa_url="test",
                admin_name="A",
                admin_email="a@b.com",
                password="123456",
            )

    def test_valid_request(self):
        req = RegisterRequest(
            company_name="My Store",
            empresa_url="my-store",
            admin_name="John Doe",
            admin_email="john@example.com",
            password="secure123",
        )
        assert req.company_name == "My Store"


class TestCustomerRegister:
    def test_valid(self):
        c = CustomerRegister(
            name="Maria",
            email="maria@test.com",
            phone="11999",
            password="123456",
        )
        assert c.name == "Maria"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            CustomerRegister(
                name="Maria",
                email="maria@test.com",
                password="123",
            )


class TestOrderCreate:
    def test_quantity_must_be_positive(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                customer_name="Test",
                customer_phone="11999",
                order_type="delivery",
                payment_method="pix",
                items=[OrderItemIn(menu_item_id=1, quantity=0)],
            )

    def test_valid_order(self):
        order = OrderCreate(
            customer_name="Test User",
            customer_phone="11999",
            order_type="delivery",
            payment_method="pix",
            items=[OrderItemIn(menu_item_id=1, quantity=2)],
        )
        assert order.items[0].quantity == 2

    def test_empty_items_accepted_at_schema_level(self):
        # Schema doesn't enforce non-empty items; that's a router-level check
        order = OrderCreate(
            customer_name="Test",
            customer_phone="11999",
            order_type="pickup",
            payment_method="pix",
            items=[],
        )
        assert len(order.items) == 0
