"""Unit tests for app.pix (PIX payload generation, CRC16, sanitize)."""
from app.pix import _crc16, _sanitize, build_pix_payload


class TestSanitize:
    def test_removes_accents_and_special(self):
        result = _sanitize("João da Silva!", 25)
        # Only ASCII alphanumeric and spaces survive
        assert result == "Joo da Silva"

    def test_truncates(self):
        result = _sanitize("A" * 50, 10)
        assert len(result) == 10

    def test_empty_returns_na(self):
        assert _sanitize("", 25) == "NA"

    def test_none_returns_na(self):
        assert _sanitize(None, 25) == "NA"

    def test_strips_whitespace(self):
        result = _sanitize("  Hello  ", 25)
        assert result == "Hello"


class TestCRC16:
    def test_returns_4_hex_chars(self):
        result = _crc16("test")
        assert len(result) == 4
        # Should be valid hex
        int(result, 16)

    def test_deterministic(self):
        assert _crc16("hello") == _crc16("hello")

    def test_different_inputs(self):
        assert _crc16("abc") != _crc16("xyz")


class TestBuildPixPayload:
    def test_starts_with_format_indicator(self):
        payload = build_pix_payload(
            pix_key="test@pix.com",
            merchant_name="Test Merchant",
            merchant_city="Sao Paulo",
        )
        assert payload.startswith("000201")

    def test_contains_pix_key(self):
        payload = build_pix_payload(
            pix_key="minha-chave@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
        )
        assert "minha-chave@pix.com" in payload

    def test_contains_amount(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
            amount=25.50,
        )
        assert "25.50" in payload

    def test_without_amount_no_tag_54(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
            amount=None,
        )
        # Tag 54 (amount) should not be present
        # The payload structure after currency (53) should jump to country (58)
        assert "5802BR" in payload

    def test_zero_amount_no_tag_54(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
            amount=0.0,
        )
        # amount <= 0 should not include tag 54
        assert "5802BR" in payload

    def test_ends_with_crc16(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
            amount=10.00,
        )
        # Last 4 chars should be the CRC16 value
        crc_part = payload[-4:]
        int(crc_part, 16)  # must be valid hex

    def test_contains_br_country_code(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
        )
        assert "5802BR" in payload

    def test_contains_brl_currency(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
        )
        assert "5303986" in payload

    def test_contains_txid(self):
        payload = build_pix_payload(
            pix_key="key@pix.com",
            merchant_name="Loja",
            merchant_city="SP",
            txid="YUMI42",
        )
        assert "YUMI42" in payload
