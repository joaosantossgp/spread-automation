import pytest
from pathlib import Path

from mapping.registry import _ensure_unique_lookup_key
from core.exceptions import MappingError

def test_ensure_unique_lookup_key_collision():
    payload = {"normalized_key_1": "some_value"}
    path = Path("test_file.json")

    with pytest.raises(MappingError, match="test_file.json contains conflicting keys after normalization for 'Raw Key 2'."):
        _ensure_unique_lookup_key(
            payload=payload,
            normalized_key="normalized_key_1",
            raw_key="Raw Key 2",
            path=path,
        )

def test_ensure_unique_lookup_key_success():
    payload = {"normalized_key_1": "some_value"}
    path = Path("test_file.json")

    # Should not raise any error
    _ensure_unique_lookup_key(
        payload=payload,
        normalized_key="normalized_key_2",
        raw_key="Raw Key 2",
        path=path,
    )
