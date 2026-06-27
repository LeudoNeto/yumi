"""Generate a static PIX "Copia e Cola" payload (BR Code / EMV-MPM).

This builds the standardized BACEN PIX payload string locally — no payment
gateway required. The resulting string can be pasted into any bank app or
encoded as a QR code on the client.
"""
import re


def _emv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def _crc16(payload: str) -> str:
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def _sanitize(text: str, max_len: int) -> str:
    # PIX merchant name/city must be ASCII, uppercase-friendly, no special chars
    text = (text or "").strip()
    text = re.sub(r"[^A-Za-z0-9 ]", "", text)
    return text[:max_len] if text else "NA"


def build_pix_payload(
    *,
    pix_key: str,
    merchant_name: str,
    merchant_city: str,
    amount: float | None = None,
    txid: str = "***",
) -> str:
    """Return the PIX copia-e-cola string for the given key and amount."""
    gui = _emv("00", "br.gov.bcb.pix")
    key = _emv("01", pix_key.strip())
    merchant_account_info = _emv("26", gui + key)

    payload = "000201"  # Payload Format Indicator
    payload += "010212"  # Point of Initiation Method (12 = reusable/static-with-amount)
    payload += merchant_account_info
    payload += _emv("52", "0000")  # Merchant Category Code
    payload += _emv("53", "986")  # Transaction currency = BRL
    if amount is not None and amount > 0:
        payload += _emv("54", f"{amount:.2f}")
    payload += _emv("58", "BR")  # Country code
    payload += _emv("59", _sanitize(merchant_name, 25))
    payload += _emv("60", _sanitize(merchant_city, 15))
    payload += _emv("62", _emv("05", txid))  # Additional data: reference label
    payload += "6304"  # CRC tag + length, value appended below
    payload += _crc16(payload)
    return payload
