"""API tests for /api/company endpoints (CRUD, logo upload, business hours)."""


class TestGetCompany:
    def test_get_company(self, client, auth_headers):
        resp = client.get("/api/company", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "name" in data
        assert "empresa_url" in data
        assert "hours" in data

    def test_unauthenticated(self, client):
        resp = client.get("/api/company")
        assert resp.status_code == 401


class TestUpdateCompany:
    def test_update_name(self, client, auth_headers):
        resp = client.patch("/api/company", json={
            "name": "New Name",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_empresa_url(self, client, auth_headers):
        resp = client.patch("/api/company", json={
            "empresa_url": "My New Slug",
        }, headers=auth_headers)
        assert resp.status_code == 200
        # Should be slugified
        assert resp.json()["empresa_url"] == "my-new-slug"

    def test_update_empresa_url_duplicate(self, client, auth_headers, second_auth_headers):
        # Get the second company's slug
        other = client.get("/api/company", headers=second_auth_headers).json()
        other_slug = other["empresa_url"]

        # Try to set first company's slug to second company's slug
        resp = client.patch("/api/company", json={
            "empresa_url": other_slug,
        }, headers=auth_headers)
        assert resp.status_code == 409

    def test_update_delivery_settings(self, client, auth_headers):
        resp = client.patch("/api/company", json={
            "delivery_fee": 5.50,
            "min_order_value": 15.00,
            "estimated_time": "40-60 min",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["delivery_fee"] == 5.50
        assert data["min_order_value"] == 15.00
        assert data["estimated_time"] == "40-60 min"

    def test_update_payment_settings(self, client, auth_headers):
        resp = client.patch("/api/company", json={
            "pix_enabled": True,
            "cash_enabled": False,
            "pix_key": "minha-chave@pix.com",
            "pix_merchant_name": "Minha Loja",
            "pix_merchant_city": "Sao Paulo",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["pix_key"] == "minha-chave@pix.com"
        assert data["cash_enabled"] is False

    def test_update_business_hours(self, client, auth_headers):
        new_hours = [
            {"weekday": i, "is_closed": i == 0, "open_time": "10:00", "close_time": "20:00"}
            for i in range(7)
        ]
        resp = client.patch("/api/company", json={
            "hours": new_hours,
        }, headers=auth_headers)
        assert resp.status_code == 200
        hours = resp.json()["hours"]
        assert len(hours) == 7
        # Monday (0) should be closed
        monday = next(h for h in hours if h["weekday"] == 0)
        assert monday["is_closed"] is True
        # Tuesday (1) should be open 10:00-20:00
        tuesday = next(h for h in hours if h["weekday"] == 1)
        assert tuesday["open_time"] == "10:00"
        assert tuesday["close_time"] == "20:00"

    def test_update_address(self, client, auth_headers):
        resp = client.patch("/api/company", json={
            "address_street": "Rua das Flores",
            "address_number": "100",
            "address_city": "São Paulo",
            "address_state": "SP",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["address_street"] == "Rua das Flores"
        assert data["address_city"] == "São Paulo"
