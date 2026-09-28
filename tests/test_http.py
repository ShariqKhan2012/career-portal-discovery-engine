"""Tests for the HTTP layer."""

import pytest

from src.http import DiskCache, HttpError, ErrorClass
from src.models import ErrorClass as ModelErrorClass


def test_error_class_matches_model():
    """HTTP layer error classes match the model taxonomy."""
    assert ErrorClass.NETWORK == ModelErrorClass.NETWORK
    assert ErrorClass.TIMEOUT == ModelErrorClass.TIMEOUT
    assert ErrorClass.BLOCKED == ModelErrorClass.BLOCKED
    assert ErrorClass.ROBOTS_DISALLOWED == ModelErrorClass.ROBOTS_DISALLOWED


def test_disk_cache_roundtrip(tmp_path):
    cache = DiskCache(tmp_path)
    url = "https://example.com/test"
    data = {"url": url, "status_code": 200, "text": "hello"}
    cache.put(url, data)
    result = cache.get(url)
    assert result is not None
    assert result["url"] == url
    assert result["status_code"] == 200


def test_disk_cache_miss(tmp_path):
    cache = DiskCache(tmp_path)
    assert cache.get("https://nonexistent.com") is None


def test_http_error_attributes():
    err = HttpError("test error", ErrorClass.TIMEOUT, "https://example.com", 408)
    assert err.error_class == ErrorClass.TIMEOUT
    assert err.url == "https://example.com"
    assert err.status_code == 408
    assert str(err) == "test error"
