"""Return models of the registration flows."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, computed_field

from ubcworkday.client.exceptions import WorkdayError
from ubcworkday.client.response import Page, Row

__all__ = [
    "MeetingPattern",
    "CourseSection",
    "Results",
    "EnrolledSection",
    "SavedSchedule",
]


class MeetingPattern(BaseModel):
    """One meeting pattern of a section, parsed from its pipe-delimited detail string."""

    raw: str
    campus: str | None
    location: str | None
    days: str | None
    time: str | None
    dates: str | None

    @classmethod
    def parse(cls, text: str) -> "MeetingPattern":
        """Parse a ``"campus | days | time | dates | location"`` string into its parts."""
        parts = [p.strip() for p in text.split("|")]
        days = next((p for p in parts if re.search(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b", p)), None)
        time = next((p for p in parts if re.search(r"[ap]\.m\.", p)), None)
        dates = next((p for p in parts if re.search(r"\d{4}-\d{2}-\d{2}", p)), None)
        campus = parts[0] if parts and parts[0] else None
        located = [p for p in parts[1:] if p and p not in (days, time, dates)]
        return cls(
            raw=text,
            campus=campus,
            location=" ".join(located) or None,
            days=days,
            time=time,
            dates=dates,
        )


class CourseSection(BaseModel):
    """A course section from search results: code/name, seats, delivery, and meetings.

    ``raw`` holds the untouched Workday item for debugging; it's excluded from JSON output.
    """

    id: str
    code: str
    name: str
    format: str | None
    status: str | None
    delivery_mode: str | None
    credits: float | None
    enrolled: int | None
    capacity: int | None
    waitlisted: int | None
    waitlist_capacity: int | None
    meetings: list[MeetingPattern]
    raw: dict[str, Any] = Field(exclude=True)

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> "CourseSection":
        """Parse one search-result list item into a ``CourseSection``."""
        title = item["title"]["instances"][0]
        code, _, name = title["text"].partition(" - ")
        subs = {
            s["label"]: s["value"] if "value" in s else s["instances"][0]["text"]
            for s in item.get("subtitles", [])
        }
        credits = subs.get("zCF - CT - Maximum Credits")
        seats = subs.get("zCF - CT - Enrolled/Capacity")
        wait = subs.get("zCF - EE - Waitlisted / Waitlist Capacity")

        return cls(
            id=title["instanceId"],
            code=code,
            name=name,
            format=subs.get("Instructional Format"),
            status=subs.get("Section Status"),
            delivery_mode=subs.get("Delivery Mode"),
            credits=float(credits.split()[0]) if credits else None,
            enrolled=int(seats.split(":")[1].split("/")[0]) if seats else None,
            capacity=int(seats.split(":")[1].split("/")[1]) if seats else None,
            waitlisted=int(wait.split(":")[1].split("/")[0]) if wait else None,
            waitlist_capacity=int(wait.split(":")[1].split("/")[1]) if wait else None,
            meetings=[
                MeetingPattern.parse(instance["text"])
                for field in item.get("detailResultFields", [])
                if field["label"] == "Section Details"
                for instance in field.get("instances", [])
            ],
            raw=item,
        )


class Results(BaseModel):
    """One page of search results: the ``total`` match count, this page's ``offset``, sections."""

    total: int
    offset: int
    sections: list[CourseSection]

    @computed_field  # type: ignore[prop-decorator]  # pydantic's documented pattern; mypy can't model it
    @property
    def size(self) -> int:
        """Number of sections on this page."""
        return len(self.sections)

    @classmethod
    def from_page(cls, page: Page) -> "Results":
        """Parse a faceted-search results page into ``Results``."""
        facets = page.body["facetContainer"]
        listing = next((c for c in page.body["children"] if "listItems" in c), None)
        if listing is None:
            raise WorkdayError("results page has no listItems — the page layout may have changed")
        return cls(
            total=facets["paginationCount"]["value"],
            offset=facets["offset"]["value"],
            sections=[CourseSection.from_item(item) for item in listing["listItems"]],
        )


class EnrolledSection(BaseModel):
    """One enrolled section: its course, meeting patterns, dates, credits and status."""

    course: str | None
    section: str | None
    status: str | None
    credits: float | None
    grading_basis: str | None
    instructional_format: str | None
    delivery_mode: str | None
    meetings: list[str]
    start_date: str | None
    end_date: str | None

    @staticmethod
    def from_row(row: Row) -> "EnrolledSection":
        """Build an ``EnrolledSection`` from a parsed grid row (course-level fields carried in)."""
        return EnrolledSection(
            course=row.text("Course Listing"),
            section=row.text("Section"),
            status=row.text("Registration Status"),
            credits=row.number("Credits"),
            grading_basis=row.text("Grading Basis"),
            instructional_format=row.text("Instructional Format"),
            delivery_mode=row.text("Delivery Mode"),
            meetings=row.strings("Meeting Patterns"),
            start_date=row.date("Start Date"),
            end_date=row.date("End Date"),
        )


class SavedSchedule(BaseModel):
    """One saved schedule: its term, the course sections in it, and any alert count."""

    term: str | None
    courses: list[str]
    alerts: int | None

    @staticmethod
    def from_row(row: Row) -> "SavedSchedule":
        """Build a ``SavedSchedule`` from a parsed grid row."""
        return SavedSchedule(
            term=row.text("Saved Schedule"),
            courses=row.strings("Course Sections"),
            alerts=row.integer("Alerts"),
        )
