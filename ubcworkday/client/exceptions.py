"""Exception hierarchy for the client. All errors derive from ``WorkdayError``."""

from __future__ import annotations


class WorkdayError(Exception):
    """Base class for every error raised by this library."""


class SessionExpired(WorkdayError):
    """The cookie is missing or expired — Workday served its login page instead of data."""


class WorkdayRequestError(WorkdayError):
    """A request failed at the transport level (HTTP error or a non-JSON response)."""


class OptionNotFound(WorkdayError):
    """A name you passed (term/program/level) matched none of the available options.

    Carries ``query`` (what you asked for) and ``available`` (the option names that
    exist) so callers can suggest or retry with a valid name.
    """

    def __init__(self, query: str, available: list[str]) -> None:
        """Build from the failed ``query`` and the ``available`` option names."""
        super().__init__(f"no option matching {query!r}; available: {available}")
        self.query = query
        self.available = available


class SubmitRejected(WorkdayError):
    """Workday understood the request but refused the action (a validation error)."""
