"""LinkedIn connector — Phase 2.

Posting as an Organization Page requires LinkedIn's Community Management API,
which is access-gated behind LinkedIn's own approval process. Not implemented
until an approved app + credentials exist.
"""

from typing import Any, Dict, List

from .base import PlatformConnector

SETUP_INSTRUCTIONS = (
    "LinkedIn isn't connected yet. To enable it: create an app at "
    "linkedin.com/developers and request Community Management API access "
    "(needed to post as your Company Page, not just a personal profile), "
    "then provide the resulting Client ID/Secret."
)


class LinkedInConnector(PlatformConnector):
    platform_id = "linkedin"

    def fetch_stats(self) -> Dict[str, Any]:
        raise NotImplementedError(SETUP_INSTRUCTIONS)

    def fetch_recent_posts(self, amount: int = 15) -> List[Dict[str, Any]]:
        raise NotImplementedError(SETUP_INSTRUCTIONS)

    def publish(self, post: Dict[str, Any]):
        raise NotImplementedError(SETUP_INSTRUCTIONS)
