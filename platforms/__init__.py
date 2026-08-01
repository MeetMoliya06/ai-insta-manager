from typing import Any, Dict

from .base import PlatformConnector, NotImplementedConnector
from .instagram import InstagramConnector
from .facebook import FacebookConnector
from .linkedin import LinkedInConnector
from .google_business import GoogleBusinessConnector

PLATFORMS = ["instagram", "facebook", "linkedin", "google_business"]

PLATFORM_LABELS = {
    "instagram": "Instagram",
    "facebook": "Facebook",
    "linkedin": "LinkedIn",
    "google_business": "Google Business Profile",
}

_CONNECTOR_CLASSES = {
    "instagram": InstagramConnector,
    "facebook": FacebookConnector,
    "linkedin": LinkedInConnector,
    "google_business": GoogleBusinessConnector,
}


def get_connector(platform: str, credentials: Dict[str, Any]) -> PlatformConnector:
    connector_cls = _CONNECTOR_CLASSES.get(platform)
    if not connector_cls:
        return NotImplementedConnector(credentials, platform, f"Unknown platform '{platform}'")
    return connector_cls(credentials)
