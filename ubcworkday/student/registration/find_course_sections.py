"""Find Course Sections — the faceted course-section search (the most involved feature).

Flow: open → set term + academic level → search → optionally narrow by keyword/facets and
page through results. ``find()`` wraps the whole happy path in one call.
"""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import (
    ACTION,
    OPTIONS,
    TASK,
    Pagination,
    Replace,
    Search,
)
from ubcworkday.client.exceptions import WorkdayError
from ubcworkday.client.response import Choice, Page, Tokens, find_choices, find_next_level, pick
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.registration.models import CourseSection, MeetingPattern, Results

__all__ = [
    "FindCourseSections",
    "CourseSection",
    "MeetingPattern",
    "Results",
    "CourseSearchIds",
    "FIND_COURSE_SECTIONS",
    "list_terms",
    "list_levels",
]


@dataclass(frozen=True)
class CourseSearchIds:
    """Workday ids for the Find Course Sections flow."""

    task: str = "1422$5132"
    start_date_field: str = "152"
    academic_level_field: str = "153"
    submit_event: str = "156"


FIND_COURSE_SECTIONS = CourseSearchIds()


class FindCourseSections:
    """The course-section search. ``find()`` is the one-call path; the rest are the steps."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: CourseSearchIds = FIND_COURSE_SECTIONS,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday ids (rarely needed)."""
        self._session = session
        self._ids = ids
        self._tokens: Tokens | None = None
        self._page: Page | None = None

    def open(self) -> "FindCourseSections":
        """Open the task and capture its flow tokens; returns self for chaining."""
        page = self._session.send(TASK, task_id=self._ids.task)
        self._tokens = Tokens.from_page(page)
        return self

    def prompt(
        self,
        field_id: str,
        prompt_id: str | None = None,
        filters: dict[str, str] | None = None,
    ) -> Page:
        """Fetch a field's prompt page; ``prompt_id``/``filters`` drill a hierarchical picker."""
        assert self._tokens is not None, "call open() first"
        return self._session.send(OPTIONS, data=OPTIONS.body(field_id, self._tokens, prompt_id, filters), context_id=self._tokens.context_id, field_id=field_id)

    def academic_levels(self) -> list[Choice]:
        """The academic-level options (Undergraduate, Graduate, …)."""
        return find_choices(self.prompt(self._ids.academic_level_field))

    def terms(self, period: str = "Future") -> list[Choice]:
        """All academic terms in a period bucket (Future / Current / Past)."""
        field = self._ids.start_date_field
        bucket = pick(find_choices(self.prompt(field)), period)
        years = self.prompt(field, prompt_id=bucket.id)
        deeper = find_next_level(years)
        if deeper is None:
            raise WorkdayError("term picker offered no deeper level — the prompt shape may have changed")
        parent, prop = deeper
        return [
            choice
            for year in find_choices(years)
            for choice in find_choices(
                self.prompt(field, prompt_id=parent, filters={prop: year.id})
            )
        ]

    def find(
        self,
        keyword: str = "",
        *,
        term: str,
        level: str = "Undergraduate",
        period: str = "Future",
    ) -> Results:
        """Open, pick term/level by name, search, and optionally narrow by keyword — one call."""
        self.open()
        results = self.search(
            pick(self.terms(period), term),
            pick(self.academic_levels(), level),
        )
        return self.keyword(keyword) if keyword else results

    def search(self, term: Choice, level: Choice) -> Results:
        """Run the search for a specific ``term`` + ``level`` and return the first page."""
        assert self._tokens is not None, "call open() first"
        self._session.send(ACTION, data=ACTION.add_body(self._ids.start_date_field, term, self._tokens))
        self._session.send(ACTION, data=ACTION.add_body(self._ids.academic_level_field, level, self._tokens))
        page = self._session.send(ACTION, data=ACTION.submit_body(self._ids.submit_event, self._tokens))
        self._page = page
        return Results.from_page(page)

    def keyword(self, text: str) -> Results:
        """Narrow the current results by a free-text keyword (call after ``search``)."""
        assert self._tokens is not None, "call open() first"
        assert self._page is not None, "call open() first"
        page = self._session.send(Search.from_page(self._page), data=Search.body(text, self._tokens))
        self._page = page
        return Results.from_page(page)

    def filter(self, selections: dict[str, str]) -> Results:
        """Replace the active facet selections (facet → value) on the current results."""
        assert self._tokens is not None, "call open() first"
        assert self._page is not None, "call open() first"
        page = self._session.send(Replace.from_page(self._page), data=Replace.body(selections, self._tokens))
        self._page = page
        return Results.from_page(page)

    def next_page(self) -> Results | None:
        """The next page of results, or ``None`` if the current page is the last."""
        assert self._page is not None, "call open() first"
        current = Results.from_page(self._page)
        offset = current.offset + current.size
        if offset >= current.total:
            return None
        page = self._session.send(Pagination.from_page(self._page), offset=offset)
        self._page = page
        return Results.from_page(page)


def list_terms(session: WorkdaySession, period: str = "Future") -> list[str]:
    """Names of the terms you can search in — values for the ``term`` argument."""
    finder = FindCourseSections(session).open()
    return [choice.text for choice in finder.terms(period)]


def list_levels(session: WorkdaySession) -> list[str]:
    """Names of the academic levels — values for the ``level`` argument."""
    finder = FindCourseSections(session).open()
    return [choice.text for choice in finder.academic_levels()]
