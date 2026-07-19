"""API tests for /api/auth/* endpoints (register, login, me)."""


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "company_name": "Sushi Place",
            "empresa_url": "sushi-place",
            "admin_name": "Admin Sushi",
            "admin_email": "sushi@test.com",
            "password": "pass1234",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_slug(self, client):
        payload = {
            "company_name": "Loja A",
            "empresa_url": "unique-slug-dup",
            "admin_name": "Admin",
            "admin_email": "a-dup@test.com",
            "password": "pass1234",
        }
        resp1 = client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 201

        payload2 = {**payload, "admin_email": "b-dup@test.com"}
        resp2 = client.post("/api/auth/register", json=payload2)
        assert resp2.status_code == 409
        assert "empresa_url" in resp2.json()["detail"].lower() or "link" in resp2.json()["detail"].lower()

    def test_register_duplicate_email(self, client):
        payload = {
            "company_name": "Loja X",
            "empresa_url": "loja-x-email",
            "admin_name": "Admin",
            "admin_email": "dup-email@test.com",
            "password": "pass1234",
        }
        resp1 = client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 201

        payload2 = {**payload, "empresa_url": "loja-x-email-2"}
        resp2 = client.post("/api/auth/register", json=payload2)
        assert resp2.status_code == 409
        assert "e-mail" in resp2.json()["detail"].lower()

    def test_register_invalid_slug(self, client):
        resp = client.post("/api/auth/register", json={
            "company_name": "Test",
            "empresa_url": "---",
            "admin_name": "Admin",
            "admin_email": "bad-slug@test.com",
            "password": "pass1234",
        })
        assert resp.status_code == 400

    def test_register_creates_business_hours(self, client):
        resp = client.post("/api/auth/register", json={
            "company_name": "Hours Store",
            "empresa_url": "hours-store",
            "admin_name": "Admin",
            "admin_email": "hours@test.com",
            "password": "pass1234",
        })
        assert resp.status_code == 201
        token = resp.json()["access_token"]

        company = client.get("/api/company", headers={
            "Authorization": f"Bearer {token}"
        })
        assert company.status_code == 200
        hours = company.json()["hours"]
        assert len(hours) == 7  # one per weekday


class TestLoginJson:
    def test_login_success(self, client):
        # First register
        client.post("/api/auth/register", json={
            "company_name": "Login Store",
            "empresa_url": "login-store",
            "admin_name": "Admin",
            "admin_email": "login@test.com",
            "password": "pass1234",
        })
        # Then login
        resp = client.post("/api/auth/login-json", json={
            "email": "login@test.com",
            "password": "pass1234",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "company_name": "Wrong PW Store",
            "empresa_url": "wrong-pw-store",
            "admin_name": "Admin",
            "admin_email": "wrongpw@test.com",
            "password": "correctpass",
        })
        resp = client.post("/api/auth/login-json", json={
            "email": "wrongpw@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = client.post("/api/auth/login-json", json={
            "email": "nobody@test.com",
            "password": "anything",
        })
        assert resp.status_code == 401


class TestMe:
    def test_me_authenticated(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "name" in data
        assert "email" in data
        assert "company_id" in data

    def test_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token-here"
        })
        assert resp.status_code == 401
