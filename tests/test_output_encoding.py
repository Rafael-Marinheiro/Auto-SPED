import pytest

from sped_mensal.output_encoding import normalize_output_encoding


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("utf-8", "utf-8"),
        ("UTF8", "utf-8"),
        ("latin-1", "iso-8859-1"),
        ("cp1252", "cp1252"),
    ),
)
def test_normalizes_supported_output_encodings(value, expected):
    assert normalize_output_encoding(value) == expected


def test_rejects_unsupported_output_encoding():
    with pytest.raises(ValueError, match="Codificação"):
        normalize_output_encoding("utf-16")
