"""View My Academic Record — your full enrollment history (single-GET grid)."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import TASK
from ubcworkday.client.response import Page, find_first_grid
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.academic_records.models import CourseResult

__all__ = ["ViewMyAcademicRecord", "CourseResult", "AcademicRecordIds", "VIEW_MY_ACADEMIC_RECORD"]


@dataclass(frozen=True)
class AcademicRecordIds:
    """Workday ids for the View My Academic Record task."""

    task: str = "2998$30300"


VIEW_MY_ACADEMIC_RECORD = AcademicRecordIds()


class ViewMyAcademicRecord:
    """Reads the student's academic record (enrollments)."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: AcademicRecordIds = VIEW_MY_ACADEMIC_RECORD,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday task id (rarely needed)."""
        self._session = session
        self._ids = ids
        self._page: Page | None = None

    def open(self) -> "ViewMyAcademicRecord":
        """Open the task; returns self for chaining."""
        self._page = self._session.send(TASK, task_id=self._ids.task)
        return self

    def enrollments(self) -> list[CourseResult]:
        """Every enrolled course on the record (call after ``open``)."""
        assert self._page is not None, "call open() first"
        grid = find_first_grid(self._page, label="Enrollments")
        return [CourseResult.from_row(row) for row in grid.rows]
