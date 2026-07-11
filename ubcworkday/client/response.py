"""The Workday response primitives — the foundation the whole library reads through.

Everything Workday sends back is a deeply-nested "widget" JSON tree. These types decode it:
``Page`` wraps a response, ``Grid``/``Row`` extract tabular widgets, ``Choice`` is a prompt
option, ``Tokens`` are the session/flow tokens carried between requests. The module-level
``find_*``/``pick`` functions are the queries that read these types out of a page.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from ubcworkday.client.exceptions import OptionNotFound, WorkdayError


@dataclass(frozen=True)
class Page:
    """A parsed Workday response (the raw widget-tree dict), with convenient access helpers."""

    raw: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        """Index into the raw top-level response dict."""
        return self.raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        """``dict.get`` on the raw top-level response dict."""
        return self.raw.get(key, default)

    @property
    def body(self) -> dict[str, Any]:
        """The ``body`` sub-tree if present, else the whole response."""
        body: dict[str, Any] = self.raw.get("body", self.raw)
        return body

    def walk(self) -> Iterator[dict[str, Any]]:
        """Yield every dict (widget) node in the page tree, depth-first."""
        stack: list[Any] = [self.raw]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                yield node
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)


@dataclass(frozen=True)
class Tokens:
    """Session/flow tokens pulled from an opened page, required to POST form events."""

    secure_token: str
    flow_key: str
    context_id: str

    @classmethod
    def from_page(cls, page: Page) -> "Tokens":
        """Extract the session/flow tokens from a freshly opened task page."""
        return cls(
            secure_token=page["sessionSecureToken"],
            flow_key=page["flowExecutionKey"],
            context_id=page["pageContextId"],
        )


@dataclass(frozen=True)
class Choice:
    """A selectable option from a prompt: its Workday instance ``id`` and display ``text``."""

    id: str
    text: str


class Row(dict[str, Any]):
    """A grid row (``{column_label: value}``) with typed, null-safe accessors.

    Subclasses ``dict``, so ``"Col" in row`` and ``row.get(...)`` still work; the accessors
    below coerce a cell value to the type you want, returning ``None`` when it's missing.
    """

    def text(self, label: str) -> str | None:
        """The cell's value if it's a string, else ``None``."""
        value = self.get(label)
        return value if isinstance(value, str) else None

    def number(self, label: str) -> float | None:
        """The cell's value as a ``float``, or ``None`` if absent."""
        value: Any = self.get(label)
        if value is None:
            return None
        return float(value)

    def integer(self, label: str) -> int | None:
        """The cell's value as an ``int``, or ``None`` if absent."""
        value: Any = self.get(label)
        if value is None:
            return None
        return int(value)

    def strings(self, label: str) -> list[str]:
        """The cell as a list of strings, normalizing single/multi/absent to a list."""
        value = self.get(label)
        if value is None:
            return []
        values = value if isinstance(value, list) else [value]
        return [str(v) for v in values]

    def date(self, label: str) -> str | None:
        """A Workday ``{Y, M, D}`` date cell formatted ``"YYYY-MM-DD"``, else ``None``."""
        value = self.get(label)
        if isinstance(value, dict) and {"Y", "M", "D"} <= value.keys():
            return f"{value['Y']}-{value['M']}-{value['D']}"
        return None


def _cell_value(cell: dict[str, Any]) -> Any:
    """A grid cell's value: a scalar ``value``, one/many instance texts, or ``None``."""
    if "value" in cell:
        return cell["value"]
    instances: Any = cell.get("instances")
    if not instances:
        return None
    texts = [instance["text"] for instance in instances]
    return texts[0] if len(texts) == 1 else texts


@dataclass(frozen=True)
class Grid:
    """A parsed grid widget: its ``label`` and its ``rows`` (each a :class:`Row`)."""

    label: str | None
    rows: list[Row]

    @staticmethod
    def read(grid: dict[str, Any]) -> "Grid":
        """Parse one raw grid-widget dict into a ``Grid``.

        Column labels come from the grid's ``columns``; a cell whose columnId isn't listed
        (nested grids, e.g. View My Courses) falls back to the cell's own ``label``.
        """
        labels = {c["columnId"]: c.get("label") for c in grid.get("columns", [])}
        rows = []
        for row in grid.get("rows", []):
            values = Row()
            for column_id, cell in row.get("cellsMap", {}).items():
                label = labels.get(column_id) or cell.get("label")
                if label is not None:
                    values[label] = _cell_value(cell)
            rows.append(values)
        return Grid(grid.get("label"), rows)


def find_grids(page: Page) -> list[Grid]:
    """Every grid widget anywhere in ``page``."""
    return [Grid.read(node) for node in page.walk() if node.get("widget") == "grid"]


def find_first_grid(page: Page, label: str | None = None, column: str | None = None) -> Grid:
    """The first grid in ``page`` matching ``label`` (or containing ``column``).

    Raises ``WorkdayError`` if none matches — usually meaning the page layout changed.
    """
    for grid in find_grids(page):
        if label is not None and grid.label == label:
            return grid
        if column is not None and any(column in row for row in grid.rows):
            return grid
    raise WorkdayError(
        f"no grid matching label={label!r} column={column!r} — the page layout may have changed"
    )


def find_choices(page: Page) -> list[Choice]:
    """Read a prompt response into a list of ``Choice`` options."""
    entries = [*page.get("instances", []), *page.get("items", [])]
    return [Choice(entry["instanceId"], entry["text"]) for entry in entries]


def find_next_level(page: Page) -> tuple[str, str] | None:
    """For a hierarchical prompt, the (prompt_id, property_name) needed to drill deeper."""
    deeper = page.get("nextLevelPrompt")
    return (deeper["instanceId"], deeper["propertyName"]) if deeper else None


def pick(choices: list[Choice], query: str) -> Choice:
    """First choice whose text contains ``query`` (case-insensitive).

    Raises ``OptionNotFound`` (with the available names) if nothing matches.
    """
    lowered = query.lower()
    for choice in choices:
        if lowered in choice.text.lower():
            return choice
    raise OptionNotFound(query, [c.text for c in choices])
