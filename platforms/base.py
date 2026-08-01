"""Common interface every social platform connector implements.

Each connector is responsible for one platform's account connection, live
stats, recent-post history (for the anti-repetition engine), and publishing.
`fetch_stats`/`fetch_recent_posts`/`publish` should raise `NotImplementedError`
until that platform's official API integration is wired up (see Phase 2 in the
project plan) rather than silently no-op.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class PlatformConnector(ABC):
    platform_id: str

    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials or {}

    @abstractmethod
    def fetch_stats(self) -> Dict[str, Any]:
        """Return live profile/page stats (followers, posts, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def fetch_recent_posts(self, amount: int = 15) -> List[Dict[str, Any]]:
        """Return recent posts in the shared history shape used for anti-repetition context."""
        raise NotImplementedError

    @abstractmethod
    def publish(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a scheduled post to the platform."""
        raise NotImplementedError


class NotImplementedConnector(PlatformConnector):
    """Placeholder for platforms whose official API integration isn't wired up yet."""

    def __init__(self, credentials: Dict[str, Any], platform_id: str, reason: str):
        super().__init__(credentials)
        self.platform_id = platform_id
        self.reason = reason

    def fetch_stats(self):
        raise NotImplementedError(self.reason)

    def fetch_recent_posts(self, amount: int = 15):
        raise NotImplementedError(self.reason)

    def publish(self, post: Dict[str, Any]):
        raise NotImplementedError(self.reason)
