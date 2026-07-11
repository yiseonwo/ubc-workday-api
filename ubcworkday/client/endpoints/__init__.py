"""Endpoint definitions (URL templates + request bodies), grouped by role:

- ``task`` — opening a task (the entry point of every flow)
- ``prompt`` — fetching/choosing a form field's options
- ``flow`` — the form-event verbs (add / remove / validate / submit)
- ``faceted`` — the faceted-search family (search / filter / paginate)

Import endpoint objects (``TASK``, ``ACTION``, ``OPTIONS``, …) from here; import the response
data types (``Page``/``Grid``/``Row``/``Choice``/``Tokens``) from ``ubcworkday.client.response``.
"""

from ubcworkday.client.endpoints.base import Endpoint, Get, Post
from ubcworkday.client.endpoints.faceted import Pagination, Replace, Search
from ubcworkday.client.endpoints.flow import ACTION, Action
from ubcworkday.client.endpoints.prompt import OPTIONS, Options
from ubcworkday.client.endpoints.task import TASK, Task

__all__ = [
    "Endpoint", "Get", "Post",
    "Task", "TASK", "Pagination",
    "Options", "OPTIONS", "Action", "ACTION", "Search", "Replace",
]
