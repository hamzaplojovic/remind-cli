"""Tests for premium features."""

import pytest

from remind.premium import LicenseManager, PremiumRequired


def test_license_manager_no_license(tmp_path):
    """Test license manager when no license exists."""
    manager = LicenseManager(license_path=tmp_path / "license.json")
    assert not manager.has_license()


def test_license_manager_create_and_load(tmp_path):
    """Test creating and loading a license."""
    license_path = tmp_path / "license.json"
    manager = LicenseManager(license_path=license_path)

    # Create license
    manager.create_license("test-token-12345", email="user@example.com")
    assert manager.has_license()

    # Create new manager and verify it loads
    manager2 = LicenseManager(license_path=license_path)
    assert manager2.has_license()
    license_obj = manager2.get_license()
    assert license_obj.token == "test-token-12345"
    assert license_obj.email == "user@example.com"


def test_require_premium_decorator(tmp_path):
    """Test premium requirement decorator."""
    from remind.premium import requires_premium

    @requires_premium
    def premium_feature():
        return "premium result"

    # Should raise without license
    with pytest.raises(PremiumRequired):
        premium_feature()
