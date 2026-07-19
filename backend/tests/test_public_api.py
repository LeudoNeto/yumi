"""API tests for /api/public/* endpoints and is_open_now logic."""
from datetime import datetime

from app.routers.public import is_open_now


class _FakeHour:
    """Minimal stand-in for BusinessHour to test is_open_now without a DB."""

    def __init__(self, weekday, is_closed=False, open_time="09:00", close_time="18:00"):
        self.weekday = weekday
        self.is_closed = is_closed
        self.open_time = open_time
        self.close_time = close_time


class _FakeCompany:
    """Minimal stand-in for Company."""

    def __init__(self, hours):
        self.hours = hours


class TestIsOpenNow:
    def test_open_during_hours(self):
        # Monday at 12:00, store open 09:00-18:00
        company = _FakeCompany([_FakeHour(0, open_time="09:00", close_time="18:00")])
        ref = datetime(2026, 7, 20, 12, 0)  # Monday
        assert is_open_now(company, ref) is True

    def test_closed_outside_hours(self):
        company = _FakeCompany([_FakeHour(0, open_time="09:00", close_time="18:00")])
        ref = datetime(2026, 7, 20, 20, 0)  # Monday 20:00
        assert is_open_now(company, ref) is False

    def test_closed_day(self):
        company = _FakeCompany([_FakeHour(0, is_closed=True)])
        ref = datetime(2026, 7, 20, 12, 0)  # Monday
        assert is_open_now(company, ref) is False

    def test_no_hours_defined(self):
        company = _FakeCompany([])
        ref = datetime(2026, 7, 20, 12, 0)
        assert is_open_now(company, ref) is False

    def test_crosses_midnight_inside(self):
        # Store open 18:00-02:00, check at 23:00
        company = _FakeCompany([_FakeHour(0, open_time="18:00", close_time="02:00")])
        ref = datetime(2026, 7, 20, 23, 0)  # Monday 23:00
        assert is_open_now(company, ref) is True

    def test_crosses_midnight_before_open(self):
        company = _FakeCompany([_FakeHour(0, open_time="18:00", close_time="02:00")])
        ref = datetime(2026, 7, 20, 15, 0)  # Monday 15:00
        assert is_open_now(company, ref) is False

    def test_crosses_midnight_early_morning(self):
        # 01:00 is within 18:00-02:00 range
        company = _FakeCompany([_FakeHour(0, open_time="18:00", close_time="02:00")])
        ref = datetime(2026, 7, 20, 1, 0)  # Monday 01:00
        assert is_open_now(company, ref) is True

    def test_exactly_at_open_time(self):
        company = _FakeCompany([_FakeHour(0, open_time="09:00", close_time="18:00")])
        ref = datetime(2026, 7, 20, 9, 0)
        assert is_open_now(company, ref) is True

    def test_exactly_at_close_time(self):
        # close_time is exclusive (< not <=)
        company = _FakeCompany([_FakeHour(0, open_time="09:00", close_time="18:00")])
        ref = datetime(2026, 7, 20, 18, 0)
        assert is_open_now(company, ref) is False


class TestPublicStoreEndpoint:
    def test_get_store(self, client, auth_headers, empresa_url):
        resp = client.get(f"/api/public/{empresa_url}")
        assert resp.status_code == 200
        data = resp.json()
        assert "company" in data
        assert "categories" in data
        assert "is_open_now" in data
        assert data["company"]["empresa_url"] == empresa_url

    def test_store_not_found(self, client):
        resp = client.get("/api/public/nonexistent-slug-xyz")
        assert resp.status_code == 404

    def test_store_includes_menu(self, client, auth_headers, seed_menu):
        url = seed_menu["empresa_url"]
        resp = client.get(f"/api/public/{url}")
        assert resp.status_code == 200
        categories = resp.json()["categories"]
        assert len(categories) >= 1
        # Find our seeded category
        bebidas = next((c for c in categories if c["name"] == "Bebidas"), None)
        assert bebidas is not None
        assert len(bebidas["items"]) >= 1
        assert bebidas["items"][0]["name"] == "Guaraná Antarctica"
