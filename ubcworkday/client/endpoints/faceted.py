"""The faceted-search family — keyword search, facet filters, and pagination.

These endpoints have no fixed URL template: Workday hands back the URI to call next
inside the current page's ``endPoints`` list, so each is built via ``from_page``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Self

from ubcworkday.client.endpoints.base import Get, Post
from ubcworkday.client.exceptions import WorkdayError
from ubcworkday.client.response import Page, Tokens


class ServerProvided:
    """Mixin for endpoints whose URI comes from the page's ``endPoints`` list.

    Classes mixing this in must be endpoint dataclasses constructible from a lone
    ``template`` (their ``method`` defaults via :class:`Get`/:class:`Post`).
    """

    TYPE: ClassVar[str] = ""
    SUFFIX: ClassVar[str] = ".htmld"

    if TYPE_CHECKING:
        def __init__(self, template: str) -> None: ...

    @classmethod
    def from_page(cls, page: Page) -> Self:
        """Build the endpoint from the URI on ``page`` matching ``TYPE``."""
        entry = next((e for e in page.body["endPoints"] if e["type"] == cls.TYPE), None)
        if entry is None:
            raise WorkdayError(f"page offers no {cls.TYPE!r} endpoint")
        return cls(entry["uri"] + cls.SUFFIX)


@dataclass(frozen=True)
class Search(ServerProvided, Post):
    """Keyword search within a faceted result set."""

    TYPE = "Search"

    @staticmethod
    def body(keyword: str, tokens: Tokens) -> dict[str, str]:
        """Body for a keyword search."""
        return {"q": keyword, "sessionSecureToken": tokens.secure_token}


@dataclass(frozen=True)
class Replace(ServerProvided, Post):
    """Replaces the active facet selections in a faceted result set."""

    TYPE = "Replace"

    @staticmethod
    def body(selections: dict[str, str], tokens: Tokens) -> dict[str, str]:
        """Body to apply ``selections`` (facet → value) to the search."""
        return {
            "facets": ",".join(selections),
            **selections,
            "sessionSecureToken": tokens.secure_token,
        }


@dataclass(frozen=True)
class Pagination(ServerProvided, Get):
    """Next page of a faceted result set (``{offset}`` filled per request)."""

    TYPE = "Pagination"
    SUFFIX = "/{offset}.htmld"
