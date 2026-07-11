"""The HTTP session: the single chokepoint every request goes through."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from ubcworkday.client.auth import WorkdayAuth
from ubcworkday.client.endpoints import Endpoint
from ubcworkday.client.response import Page
from ubcworkday.client.exceptions import SessionExpired, WorkdayRequestError


class WorkdaySession:
    """An authenticated Workday session. Use as a context manager so the client closes.

    Wraps an ``httpx.Client`` carrying the auth cookie and the Workday client header;
    every feature talks to Workday exclusively through :meth:`send`.
    """

    def __init__(self, auth: WorkdayAuth | None = None, timeout: float = 30.0) -> None:
        """Open the session; ``auth`` defaults to the cookie in the ``COOKIE`` env var."""
        self._auth = auth or WorkdayAuth.from_env()
        client_version = "2026.27.27"
        self._client = httpx.Client(
            headers={**self._auth.headers, "x-workday-client": client_version},
            timeout=timeout,
        )

    def __enter__(self) -> "WorkdaySession":
        """Enter the context manager, returning self."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the underlying HTTP client on exit."""
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def send(
        self,
        endpoint: Endpoint,
        data: dict[str, str] | None = None,
        **parts: Any,
    ) -> Page:
        """Send a request for ``endpoint`` (``parts`` fill its URL template) and return the Page.

        Adds a per-request ``clientRequestID`` (query for GET, form body for POST). Raises
        ``SessionExpired`` if Workday redirects to login, or ``WorkdayRequestError`` on an
        HTTP failure or a non-JSON response.
        """
        request_id = uuid4().hex
        params = None
        if endpoint.method == "GET":
            params = {"clientRequestID": request_id}
        else:
            data = {**(data or {}), "clientRequestID": request_id}

        try:
            response = self._client.request(
                endpoint.method, endpoint.url(**parts), params=params, data=data
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WorkdayRequestError(f"request to {endpoint.template} failed: {exc}") from exc

        if self._auth.is_login_redirect(response.text):
            raise SessionExpired(
                "Workday returned its login page — the cookie in COOKIE has "
                "expired. Copy a fresh one from a logged-in browser."
            )
        try:
            return Page(response.json())
        except ValueError as exc:
            raise WorkdayRequestError(
                f"response from {endpoint.template} was not JSON"
            ) from exc
