"""API tests for order creation, validation, pricing, and admin management."""


class TestCreateOrder:
    def test_delivery_cash(self, client, auth_headers, seed_menu):
        """Create a delivery order paying on delivery."""
        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "João Silva",
            "customer_phone": "11999990000",
            "order_type": "delivery",
            "payment_method": "cash",
            "address_street": "Rua das Flores",
            "address_number": "42",
            "items": [
                {"menu_item_id": seed_menu["item_id"], "quantity": 2},
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["customer_name"] == "João Silva"
        assert data["order_type"] == "delivery"
        assert data["payment_method"] == "cash"
        assert data["status"] == "pending"
        assert data["subtotal"] == 14.00  # 7.00 × 2
        assert data["pix_payload"] is None  # cash, no PIX

    def test_pickup_pix_with_options(self, client, auth_headers, seed_menu):
        """Create a pickup order with PIX payment and selected option."""
        # Enable PIX key for this company
        client.patch("/api/company", json={
            "pix_key": "test@pix.com",
            "pix_merchant_name": "Test",
            "pix_merchant_city": "SP",
        }, headers=auth_headers)

        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Maria",
            "customer_phone": "11888880000",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [
                {
                    "menu_item_id": seed_menu["item_id"],
                    "quantity": 1,
                    "options": [
                        {"option_id": seed_menu["option_ids"][1], "quantity": 1},  # Garrafa 600ml (+3)
                    ],
                },
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["subtotal"] == 10.00  # 7.00 base + 3.00 option
        assert data["delivery_fee"] == 0.0  # pickup
        assert data["total"] == 10.00
        assert data["pix_payload"] is not None
        assert "test@pix.com" in data["pix_payload"]

    def test_empty_cart(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [],
        })
        assert resp.status_code == 400
        assert "vazio" in resp.json()["detail"].lower()

    def test_invalid_order_type(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "drone",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })
        assert resp.status_code == 400

    def test_invalid_payment_method(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "bitcoin",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })
        assert resp.status_code == 400

    def test_cash_not_delivery(self, client, auth_headers, seed_menu):
        """Cash (pagar na entrega) is only allowed for delivery orders."""
        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "cash",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })
        assert resp.status_code == 400
        assert "delivery" in resp.json()["detail"].lower()

    def test_delivery_no_address(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "delivery",
            "payment_method": "cash",
            "address_street": "",
            "address_number": "",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })
        assert resp.status_code == 400
        assert "endereço" in resp.json()["detail"].lower()

    def test_below_minimum_order(self, client, auth_headers, seed_menu):
        # Set high minimum order
        client.patch("/api/company", json={
            "min_order_value": 100.00,
        }, headers=auth_headers)

        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })
        assert resp.status_code == 400
        assert "mínimo" in resp.json()["detail"].lower()

    def test_price_calculation_with_quantity_and_options(self, client, auth_headers, seed_menu):
        """Verify the price is calculated correctly: (base + option_deltas) * qty."""
        url = seed_menu["empresa_url"]
        # Reset min order
        client.patch("/api/company", json={"min_order_value": 0}, headers=auth_headers)

        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [
                {
                    "menu_item_id": seed_menu["item_id"],
                    "quantity": 3,
                    "options": [
                        # Garrafa 600ml: +3.00
                        {"option_id": seed_menu["option_ids"][1], "quantity": 1},
                    ],
                },
            ],
        })
        assert resp.status_code == 201
        data = resp.json()
        # unit_price = 7.00 (base) + 3.00 (option) = 10.00
        # total = 10.00 × 3 = 30.00
        assert data["items"][0]["unit_price"] == 10.00
        assert data["items"][0]["total_price"] == 30.00
        assert data["subtotal"] == 30.00
        assert data["total"] == 30.00

    def test_delivery_fee_added(self, client, auth_headers, seed_menu):
        """Delivery fee is added to the total for delivery orders."""
        client.patch("/api/company", json={
            "delivery_fee": 8.50,
            "min_order_value": 0,
        }, headers=auth_headers)

        url = seed_menu["empresa_url"]
        resp = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "delivery",
            "payment_method": "cash",
            "address_street": "Rua A",
            "address_number": "1",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["subtotal"] == 7.00
        assert data["delivery_fee"] == 8.50
        assert data["total"] == 15.50

    def test_store_not_found(self, client):
        resp = client.post("/api/public/nonexistent-store/orders", json={
            "customer_name": "Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": 1, "quantity": 1}],
        })
        assert resp.status_code == 404


class TestTrackOrder:
    def test_track_existing_order(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        order = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Tracker",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }).json()

        resp = client.get(f"/api/public/{url}/orders/{order['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == order["id"]
        assert resp.json()["customer_name"] == "Tracker"

    def test_track_nonexistent_order(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        resp = client.get(f"/api/public/{url}/orders/999999")
        assert resp.status_code == 404


class TestAdminOrders:
    def test_list_orders(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        # Create an order first
        client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Admin List Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        })

        resp = client.get("/api/orders", headers=auth_headers)
        assert resp.status_code == 200
        orders = resp.json()
        assert len(orders) >= 1
        assert any(o["customer_name"] == "Admin List Test" for o in orders)

    def test_advance_status(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        order = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Status Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }).json()

        # Advance: pending → confirmed
        resp = client.patch(f"/api/orders/{order['id']}/status", json={
            "status": "confirmed",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

        # Advance: confirmed → preparing
        resp = client.patch(f"/api/orders/{order['id']}/status", json={
            "status": "preparing",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "preparing"

    def test_invalid_status(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        order = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Invalid Status",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }).json()

        resp = client.patch(f"/api/orders/{order['id']}/status", json={
            "status": "flying",
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_cancel_order(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        order = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Cancel Test",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }).json()

        resp = client.patch(f"/api/orders/{order['id']}/status", json={
            "status": "cancelled",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    def test_get_single_order(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        order = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Single Order",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }).json()

        resp = client.get(f"/api/orders/{order['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["customer_name"] == "Single Order"

    def test_admin_cannot_see_other_company_order(self, client, auth_headers, second_auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        order = client.post(f"/api/public/{url}/orders", json={
            "customer_name": "Private Order",
            "customer_phone": "11999",
            "order_type": "pickup",
            "payment_method": "pix",
            "items": [{"menu_item_id": seed_menu["item_id"], "quantity": 1}],
        }).json()

        # Second admin tries to access first company's order
        resp = client.get(f"/api/orders/{order['id']}", headers=second_auth_headers)
        assert resp.status_code == 404
