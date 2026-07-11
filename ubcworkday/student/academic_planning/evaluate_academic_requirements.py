"""Evaluate Academic Requirements — a what-if degree audit against ANY catalog program.

This is a MUTATION: it triggers an async background evaluation on the student's record.
The finished result is delivered to Workday notifications (a subsystem we don't model),
NOT returned here — so the flow only reports success/failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import ACTION, OPTIONS, TASK
from ubcworkday.client.exceptions import SubmitRejected, WorkdayError
from ubcworkday.client.response import Choice, Tokens, find_choices, pick
from ubcworkday.client.session import WorkdaySession

__all__ = [
    "EvaluateAcademicRequirements",
    "EvaluateRequirementsIds",
    "EVALUATE_ACADEMIC_REQUIREMENTS",
    "list_offered_programs",
]


@dataclass(frozen=True)
class EvaluateRequirementsIds:
    """Workday ids for the Evaluate Academic Requirements flow."""

    task: str = "2997$14471"
    program_field: str = "196"
    is_primary_field: str = "216/wd:Is_Primary_Program_of_Study"
    submit_event: str = "224"


EVALUATE_ACADEMIC_REQUIREMENTS = EvaluateRequirementsIds()


class EvaluateAcademicRequirements:
    """Triggers a what-if requirement evaluation. ``get(program)`` is the one-call path."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: EvaluateRequirementsIds = EVALUATE_ACADEMIC_REQUIREMENTS,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday ids (rarely needed)."""
        self._session = session
        self._ids = ids
        self._tokens: Tokens | None = None
        self._default_program: str | None = None

    def open(self) -> "EvaluateAcademicRequirements":
        """Open the task, capture tokens, and note the pre-filled default program."""
        page = self._session.send(TASK, task_id=self._ids.task)
        self._tokens = Tokens.from_page(page)
        field_id = self._ids.program_field
        field = next(
            (n for n in page.walk() if n.get("id") == field_id and n.get("widget") == "monikerListInput"),
            None,
        )
        instances = field.get("instances") if field else None
        self._default_program = instances[0]["instanceId"] if instances else None
        return self

    def programs(self) -> list[Choice]:
        """Every program in the catalog (~1100), via the hierarchical picker's 'All' node."""
        field = self._ids.program_field
        assert self._tokens is not None, "call open() first"
        top = self._session.send(OPTIONS, data=OPTIONS.body(field, self._tokens), context_id=self._tokens.context_id, field_id=field)
        all_node = next((c for c in find_choices(top) if c.text == "All"), None)
        if all_node is None:
            raise WorkdayError("program picker has no 'All' node — the prompt shape may have changed")
        full = self._session.send(OPTIONS, data=OPTIONS.body(field, self._tokens, prompt_id=all_node.id), context_id=self._tokens.context_id, field_id=field)
        return find_choices(full)

    def evaluate(self, program: Choice) -> None:
        """Fire an evaluation against ``program`` (async; result goes to notifications).

        MUTATES the account. Raises ``SubmitRejected`` if Workday rejects the submit.
        """
        assert self._tokens is not None, "call open() first"
        field = self._ids.program_field
        if self._default_program is not None:
            self._session.send(ACTION, data=ACTION.remove_body(field, self._default_program, self._tokens))
        self._session.send(ACTION, data=ACTION.add_body(field, program, self._tokens, pv=True))
        self._session.send(ACTION, data=ACTION.check_body(self._ids.is_primary_field, self._tokens))
        page = self._session.send(ACTION, data=ACTION.submit_body(self._ids.submit_event, self._tokens))
        error = next((n.get("message") for n in page.walk() if n.get("widget") == "error"), None)
        if error:
            raise SubmitRejected(error)

    def get(self, program: str) -> None:
        """Open and fire an evaluation against the program matching ``program``.

        MUTATES the account (triggers an async background job); returns nothing.
        """
        self.open()
        self.evaluate(pick(self.programs(), program))


def list_offered_programs(session: WorkdaySession) -> list[str]:
    """Names of every program UBC offers (~1100) — values for the ``program`` argument."""
    evaluate = EvaluateAcademicRequirements(session).open()
    return [choice.text for choice in evaluate.programs()]
