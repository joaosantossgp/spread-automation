import pytest
from core.exceptions import MappingError
from mapping.registry import _normalize_text

@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("hello world", "hello world"),
        ("HELLO WORLD", "hello world"),
        ("  Leading and trailing  ", "leading and trailing"),
        ("Multiple    spaces", "multiple spaces"),
        ("Mixed   CASE   with spaces", "mixed case with spaces"),
        ("Straße", "strasse"), # test casefold
    ]
)
def test_normalize_text_success(input_val, expected):
    assert _normalize_text(input_val) == expected

@pytest.mark.parametrize(
    "input_val, expected_msg",
    [
        ("   ", "text cannot be empty."),
        ("", "text cannot be empty."),
        (None, "text must be a string."),
        (123, "text must be a string."),
    ]
)
def test_normalize_text_failure(input_val, expected_msg):
    with pytest.raises(MappingError, match=expected_msg):
        _normalize_text(input_val)
