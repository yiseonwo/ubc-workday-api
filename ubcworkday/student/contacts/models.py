"""Return models of the contacts flows."""

from __future__ import annotations

from pydantic import BaseModel

from ubcworkday.client.response import Row

__all__ = ["SupportContact"]


class SupportContact(BaseModel):
    """A person in the student's support network: their name, role, email, and cohorts."""

    name: str | None
    role: str | None
    email: str | None
    cohorts: list[str]

    @staticmethod
    def from_row(row: Row) -> "SupportContact":
        """Build a ``SupportContact`` from a parsed grid row."""
        return SupportContact(
            name=row.text("Person"),
            role=row.text("Role"),
            email=row.text("Public Work Email"),
            cohorts=row.strings("Student Cohorts"),
        )
