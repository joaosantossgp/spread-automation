import pytest
from core.exceptions import SchemaError
from core.schema import _expect_dict, _expect_list

def test_expect_dict_success():
    data = {"key": "value"}
    assert _expect_dict(data, field_name="test_field") == data

@pytest.mark.parametrize("invalid_value", [
    [],
    "string",
    123,
    1.23,
    None,
    True
])
def test_expect_dict_failure(invalid_value):
    with pytest.raises(SchemaError, match="test_field must be an object."):
        _expect_dict(invalid_value, field_name="test_field")

def test_expect_list_success():
    data = [1, 2, 3]
    assert _expect_list(data, field_name="test_field") == data

@pytest.mark.parametrize("invalid_value", [
    {},
    "string",
    123,
    1.23,
    None,
    True
])
def test_expect_list_failure(invalid_value):
    with pytest.raises(SchemaError, match="test_field must be a list."):
        _expect_list(invalid_value, field_name="test_field")
