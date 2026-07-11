"""Authentication: a browser cookie is the only credential Workday needs from us."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ubcworkday.client.exceptions import SessionExpired


@dataclass(frozen=True)
class WorkdayAuth:
    """Holds the Workday session cookie and knows how to detect an expired session."""

    cookie: str

    @classmethod
    def from_env(cls, var: str = "COOKIE") -> "WorkdayAuth":
        """Build from the ``COOKIE`` environment variable; raise if it isn't set."""
        cookie = os.environ.get(var)
        if not cookie:
            raise SessionExpired(
                f"{var} is not set — copy your Workday Cookie header from a "
                f"logged-in browser and set {var} to it."
            )
        return cls(cookie)

    @property
    def headers(self) -> dict[str, str]:
        """The request headers carrying the cookie."""
        return {"Cookie": self.cookie}

    @staticmethod
    def is_login_redirect(body: str) -> bool:
        """True if a response body is Workday's login page (i.e. the session expired)."""
        login_path = "/wday/authgwy/ubc/login.htmld"
        return login_path in body
