"""Unit tests for app.utils (slugify, is_valid_slug)."""
from app.utils import is_valid_slug, slugify


class TestSlugify:
    def test_basic(self):
        assert slugify("Meu Restaurante") == "meu-restaurante"

    def test_accents(self):
        assert slugify("Café & Açaí") == "cafe-acai"

    def test_special_chars(self):
        assert slugify("Loja #1 — Best!") == "loja-1-best"

    def test_extra_spaces(self):
        assert slugify("  muitos   espaços  ") == "muitos-espacos"

    def test_already_slug(self):
        assert slugify("my-store") == "my-store"

    def test_numbers(self):
        assert slugify("Loja 123") == "loja-123"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_uppercase(self):
        assert slugify("ABC DEF") == "abc-def"


class TestIsValidSlug:
    def test_valid_simple(self):
        assert is_valid_slug("my-store") is True

    def test_valid_numbers(self):
        assert is_valid_slug("store-123") is True

    def test_valid_single_word(self):
        assert is_valid_slug("store") is True

    def test_invalid_uppercase(self):
        assert is_valid_slug("My-Store") is False

    def test_invalid_spaces(self):
        assert is_valid_slug("my store") is False

    def test_invalid_special(self):
        assert is_valid_slug("my_store!") is False

    def test_invalid_empty(self):
        assert is_valid_slug("") is False

    def test_invalid_leading_dash(self):
        assert is_valid_slug("-store") is False

    def test_invalid_trailing_dash(self):
        assert is_valid_slug("store-") is False

    def test_invalid_double_dash(self):
        assert is_valid_slug("my--store") is False

    def test_too_long(self):
        assert is_valid_slug("a" * 81) is False

    def test_max_length(self):
        assert is_valid_slug("a" * 80) is True
