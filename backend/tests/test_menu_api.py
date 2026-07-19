"""API tests for /api/menu/* endpoints (categories, items, options)."""


class TestCategories:
    def test_create_category(self, client, auth_headers):
        resp = client.post("/api/menu/categories", json={
            "name": "Lanches",
            "description": "Hamburgers e sanduíches",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Lanches"
        assert data["description"] == "Hamburgers e sanduíches"
        assert "id" in data

    def test_list_categories(self, client, auth_headers):
        # Create two categories
        client.post("/api/menu/categories", json={"name": "Cat A"}, headers=auth_headers)
        client.post("/api/menu/categories", json={"name": "Cat B"}, headers=auth_headers)

        resp = client.get("/api/menu/categories", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = [c["name"] for c in data]
        assert "Cat A" in names
        assert "Cat B" in names

    def test_update_category(self, client, auth_headers):
        cat = client.post("/api/menu/categories", json={
            "name": "Old Name",
        }, headers=auth_headers).json()

        resp = client.patch(f"/api/menu/categories/{cat['id']}", json={
            "name": "New Name",
            "description": "Updated",
            "sort_order": 5,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_category(self, client, auth_headers):
        cat = client.post("/api/menu/categories", json={
            "name": "To Delete",
        }, headers=auth_headers).json()

        resp = client.delete(f"/api/menu/categories/{cat['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_category(self, client, auth_headers):
        resp = client.delete("/api/menu/categories/999999", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, client):
        resp = client.get("/api/menu/categories")
        assert resp.status_code == 401


class TestItems:
    def test_create_item(self, client, auth_headers):
        cat = client.post("/api/menu/categories", json={
            "name": "Drinks",
        }, headers=auth_headers).json()

        resp = client.post(f"/api/menu/categories/{cat['id']}/items", json={
            "name": "Coca-Cola",
            "description": "Lata 350ml",
            "base_price": 6.00,
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Coca-Cola"
        assert data["base_price"] == 6.00
        assert data["category_id"] == cat["id"]

    def test_create_item_with_options(self, client, auth_headers):
        cat = client.post("/api/menu/categories", json={
            "name": "Açaí",
        }, headers=auth_headers).json()

        resp = client.post(f"/api/menu/categories/{cat['id']}/items", json={
            "name": "Açaí 500ml",
            "base_price": 18.00,
            "option_groups": [
                {
                    "name": "Complementos",
                    "min_select": 0,
                    "max_select": 3,
                    "allow_repeat": False,
                    "options": [
                        {"name": "Granola", "price_delta": 2.00},
                        {"name": "Leite em pó", "price_delta": 2.50},
                        {"name": "Banana", "price_delta": 1.50},
                    ],
                },
                {
                    "name": "Tamanho do copo",
                    "min_select": 1,
                    "max_select": 1,
                    "options": [
                        {"name": "300ml", "price_delta": -3.00},
                        {"name": "500ml", "price_delta": 0.00},
                        {"name": "700ml", "price_delta": 5.00},
                    ],
                },
            ],
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["option_groups"]) == 2
        # First group: Complementos
        grp = data["option_groups"][0]
        assert grp["name"] == "Complementos"
        assert grp["max_select"] == 3
        assert len(grp["options"]) == 3
        # Second group: required
        grp2 = data["option_groups"][1]
        assert grp2["required"] is True
        assert grp2["min_select"] == 1

    def test_update_item(self, client, auth_headers):
        cat = client.post("/api/menu/categories", json={
            "name": "Update Category",
        }, headers=auth_headers).json()

        item = client.post(f"/api/menu/categories/{cat['id']}/items", json={
            "name": "Old Item",
            "base_price": 10.00,
        }, headers=auth_headers).json()

        resp = client.patch(f"/api/menu/items/{item['id']}", json={
            "name": "Updated Item",
            "description": "New description",
            "base_price": 15.00,
            "is_available": False,
            "sort_order": 0,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Item"
        assert data["base_price"] == 15.00
        assert data["is_available"] is False

    def test_delete_item(self, client, auth_headers):
        cat = client.post("/api/menu/categories", json={
            "name": "Delete Category",
        }, headers=auth_headers).json()

        item = client.post(f"/api/menu/categories/{cat['id']}/items", json={
            "name": "To Remove",
            "base_price": 5.00,
        }, headers=auth_headers).json()

        resp = client.delete(f"/api/menu/items/{item['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_cross_company_category_access(self, client, auth_headers, second_auth_headers):
        # Create category in second company
        cat = client.post("/api/menu/categories", json={
            "name": "Other Company Cat",
        }, headers=second_auth_headers).json()

        # First company tries to add item to second company's category
        resp = client.post(f"/api/menu/categories/{cat['id']}/items", json={
            "name": "Intruder Item",
            "base_price": 10.00,
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_cross_company_item_access(self, client, auth_headers, second_auth_headers):
        # Create item in second company
        cat = client.post("/api/menu/categories", json={
            "name": "Protected Cat",
        }, headers=second_auth_headers).json()
        item = client.post(f"/api/menu/categories/{cat['id']}/items", json={
            "name": "Protected Item",
            "base_price": 10.00,
        }, headers=second_auth_headers).json()

        # First company tries to update second company's item
        resp = client.patch(f"/api/menu/items/{item['id']}", json={
            "name": "Hacked",
            "base_price": 0.01,
            "sort_order": 0,
        }, headers=auth_headers)
        assert resp.status_code == 404
