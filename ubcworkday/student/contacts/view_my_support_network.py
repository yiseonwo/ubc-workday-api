"""View My Support Network — the student's advisors/contacts (single-GET grid)."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import TASK
from ubcworkday.client.response import Page, find_first_grid
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.contacts.models import SupportContact

__all__ = ["ViewMySupportNetwork", "SupportContact", "SupportNetworkIds", "VIEW_MY_SUPPORT_NETWORK"]


@dataclass(frozen=True)
class SupportNetworkIds:
    """Workday ids for the View My Support Network task."""

    task: str = "2998$34865"


VIEW_MY_SUPPORT_NETWORK = SupportNetworkIds()


class ViewMySupportNetwork:
    """Reads the student's support network (advisors and other contacts)."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: SupportNetworkIds = VIEW_MY_SUPPORT_NETWORK,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday task id (rarely needed)."""
        self._session = session
        self._ids = ids
        self._page: Page | None = None

    def open(self) -> "ViewMySupportNetwork":
        """Open the task; returns self for chaining."""
        self._page = self._session.send(TASK, task_id=self._ids.task)
        return self

    def contacts(self) -> list[SupportContact]:
        """Every contact in the support network (call after ``open``)."""
        assert self._page is not None, "call open() first"
        grid = find_first_grid(self._page, column="Person")
        return [SupportContact.from_row(row) for row in grid.rows]
