"""View My Saved Schedules — the schedules you've saved while planning (single-GET grid)."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints import TASK
from ubcworkday.client.response import Page, find_first_grid
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.registration.models import SavedSchedule

__all__ = ["ViewMySavedSchedules", "SavedSchedule", "SavedSchedulesIds", "VIEW_MY_SAVED_SCHEDULES"]


@dataclass(frozen=True)
class SavedSchedulesIds:
    """Workday ids for the View My Saved Schedules task."""

    task: str = "2998$45124"


VIEW_MY_SAVED_SCHEDULES = SavedSchedulesIds()


class ViewMySavedSchedules:
    """Reads the student's saved (planned) schedules."""

    def __init__(
        self,
        session: WorkdaySession,
        ids: SavedSchedulesIds = VIEW_MY_SAVED_SCHEDULES,
    ) -> None:
        """Bind to a session; ``ids`` overrides the Workday task id (rarely needed)."""
        self._session = session
        self._ids = ids
        self._page: Page | None = None

    def open(self) -> "ViewMySavedSchedules":
        """Open the task; returns self for chaining."""
        self._page = self._session.send(TASK, task_id=self._ids.task)
        return self

    def schedules(self) -> list[SavedSchedule]:
        """Every saved schedule (call after ``open``)."""
        assert self._page is not None, "call open() first"
        grid = find_first_grid(self._page, label="Saved Schedules")
        return [SavedSchedule.from_row(row) for row in grid.rows]
