"""Opening a task — the entry point of every feature flow."""

from __future__ import annotations

from dataclasses import dataclass

from ubcworkday.client.endpoints.base import Get


@dataclass(frozen=True)
class Task(Get):
    """Opens a Workday task by id (``GET /ubc/task/{task_id}``) — the entry point of a feature."""

    template: str = "/ubc/task/{task_id}.htmld"


TASK = Task()
