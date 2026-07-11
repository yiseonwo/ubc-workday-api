"""View My Academic Progress — degree-requirement progress (open → submit, no input)."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import ACTION, TASK
from ubcworkday.client.response import Tokens
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.academic_records.models import AcademicProgress

__all__ = [
    "ViewMyAcademicProgress",
    "AcademicProgress",
    "AcademicProgressIds",
    "VIEW_MY_ACADEMIC_PROGRESS",
]


@dataclass(frozen=True)
class AcademicProgressIds:
    """Workday ids for the View My Academic Progress flow."""

    task: str = "2998$29782"
    submit_event: str = "24"


VIEW_MY_ACADEMIC_PROGRESS = AcademicProgressIds()


class ViewMyAcademicProgress:
    """Reads degree-requirement progress for the student's declared program."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: AcademicProgressIds = VIEW_MY_ACADEMIC_PROGRESS,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday ids (rarely needed)."""
        self._session = session
        self._ids = ids
        self._tokens: Tokens | None = None

    def open(self) -> "ViewMyAcademicProgress":
        """Open the task and capture its flow tokens; returns self for chaining."""
        page = self._session.send(TASK, task_id=self._ids.task)
        self._tokens = Tokens.from_page(page)
        return self

    def progress(self) -> AcademicProgress:
        """Submit and return the academic-progress results (call after ``open``)."""
        assert self._tokens is not None, "call open() first"
        page = self._session.send(ACTION, data=ACTION.submit_body(self._ids.submit_event, self._tokens))
        return AcademicProgress.from_page(page)
