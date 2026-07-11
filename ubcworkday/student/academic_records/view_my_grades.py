"""View My Grades — final grades for an academic period (open → pick period → submit)."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import ACTION, OPTIONS, TASK
from ubcworkday.client.response import Choice, Tokens, find_choices, find_grids, pick
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.academic_records.models import CourseResult

__all__ = ["ViewMyGrades", "CourseResult", "GradesIds", "VIEW_MY_GRADES", "list_terms"]


@dataclass(frozen=True)
class GradesIds:
    """Workday ids for the View My Grades flow."""

    task: str = "2997$11934"
    academic_period_field: str = "71"
    submit_event: str = "77"


VIEW_MY_GRADES = GradesIds()


class ViewMyGrades:
    """Grades for a chosen academic period. Use ``get(term)`` for the one-call path."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: GradesIds = VIEW_MY_GRADES,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday ids (rarely needed)."""
        self._session = session
        self._ids = ids
        self._tokens: Tokens | None = None

    def open(self) -> "ViewMyGrades":
        """Open the task and capture its flow tokens; returns self for chaining."""
        page = self._session.send(TASK, task_id=self._ids.task)
        self._tokens = Tokens.from_page(page)
        return self

    def periods(self) -> list[Choice]:
        """The academic periods you can request grades for (call after ``open``)."""
        field = self._ids.academic_period_field
        assert self._tokens is not None, "call open() first"
        page = self._session.send(OPTIONS, data=OPTIONS.body(field, self._tokens), context_id=self._tokens.context_id, field_id=field)
        return find_choices(page)

    def grades(self, period: Choice) -> list[CourseResult]:
        """Submit ``period`` and return its graded courses."""
        assert self._tokens is not None, "call open() first"
        self._session.send(ACTION, data=ACTION.add_body(self._ids.academic_period_field, period, self._tokens))
        page = self._session.send(ACTION, data=ACTION.submit_body(self._ids.submit_event, self._tokens))
        rows = [row for grid in find_grids(page) for row in grid.rows if "Grade" in row]
        return [CourseResult.from_row(row) for row in rows]

    def get(self, term: str) -> list[CourseResult]:
        """Open and return grades for the academic period matching ``term`` — one call."""
        self.open()
        return self.grades(pick(self.periods(), term))


def list_terms(session: WorkdaySession) -> list[str]:
    """Names of the terms you have grades for — values for the ``term`` argument."""
    grades = ViewMyGrades(session).open()
    return [choice.text for choice in grades.periods()]
