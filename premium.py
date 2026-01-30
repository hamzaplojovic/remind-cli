"""Premium feature management for Remind."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from remind.config import get_license_path
from remind.models import License


class PremiumRequired(Exception):
    """Raised when a premium feature is accessed without a license."""

    pass


class LicenseManager:
    """Manages license tokens and premium feature access."""

    def __init__(self, license_path: Optional[Path] = None):
        """Initialize license manager."""
        self.license_path = license_path or get_license_path()
        self._license: Optional[License] = None

    def has_license(self) -> bool:
        """Check if a valid license exists."""
        if self._license:
            return True

        if not self.license_path.exists():
            return False

        try:
            self._load_license()
            return self._license is not None
        except Exception:
            return False

    def get_license(self) -> Optional[License]:
        """Get the current license if it exists."""
        if self._license:
            return self._license

        if self.has_license():
            self._load_license()

        return self._license

    def _load_license(self) -> None:
        """Load license from file."""
        try:
            with open(self.license_path, "r") as f:
                data = json.load(f)
                # Validate basic structure
                if "token" not in data:
                    raise ValueError("Invalid license format: missing token")
                self._license = License(**data)
        except Exception as e:
            raise ValueError(f"Could not load license: {e}")

    def create_license(
        self, token: str, email: Optional[str] = None
    ) -> License:
        """Create and save a new license."""
        from datetime import timezone
        license_obj = License(token=token, created_at=datetime.now(timezone.utc), email=email)

        # Ensure directory exists
        self.license_path.parent.mkdir(parents=True, exist_ok=True)

        # Save license
        with open(self.license_path, "w") as f:
            json.dump(license_obj.model_dump(mode="python"), f, indent=2, default=str)

        self._license = license_obj
        return license_obj

    def require_premium(self) -> None:
        """Raise error if premium license not present."""
        if not self.has_license():
            raise PremiumRequired(
                "This feature requires a premium license. "
                "Visit https://github.com/sponsors/yourname to upgrade."
            )


# Global license manager instance
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get the global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def requires_premium(func):
    """Decorator to require premium license for a function."""

    def wrapper(*args, **kwargs):
        manager = get_license_manager()
        manager.require_premium()
        return func(*args, **kwargs)

    return wrapper
