"""View Evaluated Academic Requirements — degree progress for a program you choose.

Like View My Academic Progress, but you pick which of your declared programs to evaluate
against. Reuses ``AcademicProgress`` for the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import ACTION, OPTIONS, TASK
from ubcworkday.client.response import Choice, Tokens, find_choices, pick
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.academic_records.models import AcademicProgress, Requirement

__all__ = [
    "ViewEvaluatedAcademicRequirements",
    "AcademicProgress",
    "Requirement",
    "ViewEvaluatedRequirementsIds",
    "VIEW_EVALUATED_ACADEMIC_REQUIREMENTS",
    "list_declared_programs",
]


@dataclass(frozen=True)
class ViewEvaluatedRequirementsIds:
    """Workday ids for the View Evaluated Academic Requirements flow."""

    task: str = "2997$14514"
    program_field: str = "71"
    submit_event: str = "77"


VIEW_EVALUATED_ACADEMIC_REQUIREMENTS = ViewEvaluatedRequirementsIds()


class ViewEvaluatedAcademicRequirements:
    """View the evaluated requirements for a chosen program of study.

    Same result shape as View My Academic Progress (reuses ``AcademicProgress``),
    but you first pick which program to evaluate against via ``programs()``.
    """

    def __init__(
        self,
        session: WorkdaySession,
        ids: ViewEvaluatedRequirementsIds = VIEW_EVALUATED_ACADEMIC_REQUIREMENTS,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday ids (rarely needed)."""
        self._session = session
        self._ids = ids
        self._tokens: Tokens | None = None

    def open(self) -> "ViewEvaluatedAcademicRequirements":
        """Open the task and capture its flow tokens; returns self for chaining."""
        page = self._session.send(TASK, task_id=self._ids.task)
        self._tokens = Tokens.from_page(page)
        return self

    def programs(self) -> list[Choice]:
        """Your declared programs you can evaluate against (call after ``open``)."""
        field = self._ids.program_field
        assert self._tokens is not None, "call open() first"
        page = self._session.send(OPTIONS, data=OPTIONS.body(field, self._tokens), context_id=self._tokens.context_id, field_id=field)
        return find_choices(page)

    def evaluate(self, program: Choice) -> AcademicProgress:
        """Submit ``program`` and return its evaluated requirement progress."""
        assert self._tokens is not None, "call open() first"
        self._session.send(ACTION, data=ACTION.add_body(self._ids.program_field, program, self._tokens))
        page = self._session.send(ACTION, data=ACTION.submit_body(self._ids.submit_event, self._tokens))
        return AcademicProgress.from_page(page)

    def get(self, program: str) -> AcademicProgress:
        """Open and return the evaluated requirements for the program matching ``program``."""
        self.open()
        return self.evaluate(pick(self.programs(), program))


def list_declared_programs(session: WorkdaySession) -> list[str]:
    """Names of your declared programs — values for the ``program`` argument."""
    evaluated = ViewEvaluatedAcademicRequirements(session).open()
    return [choice.text for choice in evaluated.programs()]
