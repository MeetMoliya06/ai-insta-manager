"""Facebook connector — Phase 2.

Requires a Meta developer app (developers.facebook.com) with "Facebook Login
for Business" and the pages_manage_posts / pages_read_engagement permissions,
approved via Meta App Review. Not implemented until those credentials exist.
"""

from typing import Any, Dict, List

from .base import PlatformConnector

SETUP_INSTRUCTIONS = (
    "Facebook isn't connected yet. To enable it: create a Meta app at "
    "developers.facebook.com, add 'Facebook Login for Business', request the "
    "pages_manage_posts and pages_read_engagement permissions, and provide "
    "the resulting App ID/Secret and Page access token."
)


class FacebookConnector(PlatformConnector):
    platform_id = "facebook"

    def fetch_stats(self) -> Dict[str, Any]:
        raise NotImplementedError(SETUP_INSTRUCTIONS)

    def fetch_recent_posts(self, amount: int = 15) -> List[Dict[str, Any]]:
        raise NotImplementedError(SETUP_INSTRUCTIONS)

    def publish(self, post: Dict[str, Any]):
        raise NotImplementedError(SETUP_INSTRUCTIONS)
