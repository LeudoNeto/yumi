"""API tests for /api/customer/* endpoints (register, login, me, orders)."""


class TestCustomerRegister:
    def test_register_success(self, client):
        resp = client.post("/api/customer/auth/register", json={
            "name": "Maria Santos",
            "email": "maria-cust@test.com",
            "phone": "11988887777",
            "password": "custpass1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        payload = {
            "name": "First",
            "email": "dup-cust@test.com",
            "phone": "11999",
            "password": "custpass1",
        }
        resp1 = client.post("/api/customer/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = client.post("/api/customer/auth/register", json={
            **payload, "name": "Second",
        })
        assert resp2.status_code == 409


class TestCustomerLogin:
    def test_login_success(self, client):
        client.post("/api/customer/auth/register", json={
            "name": "Login Customer",
            "email": "cust-login@test.com",
            "phone": "11999",
            "password": "mypass123",
        })
        resp = client.post("/api/customer/auth/login", json={
            "email": "cust-login@test.com",
            "password": "mypass123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post("/api/customer/auth/register", json={
            "name": "Wrong PW",
            "email": "cust-wrongpw@test.com",
            "phone": "11999",
            "password": "correct123",
        })
        resp = client.post("/api/customer/auth/login", json={
            "email": "cust-wrongpw@test.com",
            "password": "incorrect",
        })
        assert resp.status_code == 401

    def test_login_nonexistent(self, client):
        resp = client.post("/api/customer/auth/login", json={
            "email": "ghost@test.com",
            "password": "anything",
        })
        assert resp.status_code == 401


class TestCustomerMe:
    def test_me(self, client, customer_headers):
        resp = client.get("/api/customer/auth/me", headers=customer_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "name" in data
        assert "email" in data
        assert "phone" in data

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/customer/auth/me")
        assert resp.status_code == 401

    def test_admin_token_cannot_access_customer_me(self, client, auth_headers):
        """Admin tokens should not work on customer endpoints."""
        resp = client.get("/api/customer/auth/me", headers=auth_headers)
        assert resp.status_code == 401


class TestCustomerOrders:
    def test_list_orders_empty(self, client, customer_headers):
        resp = client.get("/api/customer/orders", headers=customer_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_orders_with_order(self, client, auth_headers, seed_menu, customer_headers):
        """Customer order is linked to account and shows in /customer/orders."""
        url = seed_menu["empresa_url"]
        # Place order as authenticated customer
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Customer Order",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }, headers=customer_headers)
        assert resp.status_code == 201

        # Now list customer orders
        orders = client.get("/api/customer/orders", headers=customer_headers)
        assert orders.status_code == 200
        data = orders.json()
        assert len(data) >= 1
        assert data[0]["customer_name"] == "Customer Order"

    def test_list_orders_filtered_by_store(self, client, auth_headers, seed_menu, customer_headers):
        url = seed_menu["empresa_url"]
        # Place order
        client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Filtered Order",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }, headers=customer_headers)

        # Filter by empresa_url
        resp = client.get(f"/api/customer/orders?empresa_url={url}", headers=customer_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Filter by nonexistent store returns empty
        resp2 = client.get("/api/customer/orders?empresa_url=nope-store", headers=customer_headers)
        assert resp2.status_code == 200
        assert resp2.json() == []
