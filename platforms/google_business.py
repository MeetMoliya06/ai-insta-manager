"""Google Business Profile connector — Phase 2.

Requires a Google Cloud project with the Business Profile APIs enabled and
production quota approved via Google's access request form (default quota is
0 requests/day until granted). Not implemented until that access exists.
"""

from typing import Any, Dict, List

from .base import PlatformConnector

SETUP_INSTRUCTIONS = (
    "Google Business Profile isn't connected yet. To enable it: create a "
    "Google Cloud project, enable the Business Profile APIs, and request "
    "production access via Google's access request form, then provide the "
    "resulting OAuth Client ID/Secret."
)


class GoogleBusinessConnector(PlatformConnector):
    platform_id = "google_business"

    def fetch_stats(self) -> Dict[str, Any]:
        raise NotImplementedError(SETUP_INSTRUCTIONS)

    def fetch_recent_posts(self, amount: int = 15) -> List[Dict[str, Any]]:
        raise NotImplementedError(SETUP_INSTRUCTIONS)

    def publish(self, post: Dict[str, Any]):
        raise NotImplementedError(SETUP_INSTRUCTIONS)
