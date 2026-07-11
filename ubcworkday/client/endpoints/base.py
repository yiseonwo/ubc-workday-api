"""Base endpoint types: a URL template + HTTP method, filled in per request."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Endpoint:
    """A Workday endpoint: an HTTP ``method`` plus a URL ``template`` with ``{placeholders}``."""

    BASE_URL = "https://wd10.myworkday.com"

    template: str
    method: str

    def url(self, **parts: Any) -> str:
        """The full absolute URL: ``BASE_URL`` + the template with ``parts`` filled in."""
        return self.BASE_URL + self.template.format(**parts)


@dataclass(frozen=True)
class Get(Endpoint):
    """An endpoint served over HTTP GET."""

    method: str = "GET"


@dataclass(frozen=True)
class Post(Endpoint):
    """An endpoint served over HTTP POST."""

    method: str = "POST"
