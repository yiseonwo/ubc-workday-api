"""View My Courses — the student's current enrolled sections (single-GET nested grid)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ubcworkday.client.endpoints import TASK
from ubcworkday.client.response import Page, Row, find_first_grid
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.registration.models import EnrolledSection

__all__ = ["ViewMyCourses", "EnrolledSection", "ViewMyCoursesIds", "VIEW_MY_COURSES"]


@dataclass(frozen=True)
class ViewMyCoursesIds:
    """Workday ids for the View My Courses task."""

    task: str = "2998$28771"


VIEW_MY_COURSES = ViewMyCoursesIds()


class ViewMyCourses:
    """Reads the student's currently enrolled course sections."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: ViewMyCoursesIds = VIEW_MY_COURSES,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday task id (rarely needed)."""
        self._session = session
        self._ids = ids
        self._page: Page | None = None

    def open(self) -> "ViewMyCourses":
        """Open the task; returns self for chaining."""
        self._page = self._session.send(TASK, task_id=self._ids.task)
        return self

    def sections(self) -> list[EnrolledSection]:
        """Every enrolled section (call after ``open``).

        The grid has one row per section; course-level cells (Course Listing / Credits /
        Grading Basis) appear only on each course's first row, so they're carried forward
        onto the continuation rows.
        """
        assert self._page is not None, "call open() first"
        grid = find_first_grid(self._page, column="Section")
        sections = []
        carry: dict[str, Any] = {}
        for row in grid.rows:
            if row.get("Course Listing") is not None:
                carry = {k: row[k] for k in ("Course Listing", "Credits", "Grading Basis") if k in row}
            sections.append(EnrolledSection.from_row(Row({**carry, **row})))
        return sections
