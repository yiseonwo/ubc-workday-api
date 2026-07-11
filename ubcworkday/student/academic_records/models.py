"""Shared return models of the academic-records flows."""

from __future__ import annotations

from pydantic import BaseModel

from ubcworkday.client.response import Page, Row, find_first_grid, find_grids

__all__ = ["CourseResult", "Requirement", "AcademicProgress"]


class CourseResult(BaseModel):
    """A completed/enrolled course row — shared by View My Grades and View My Academic Record."""

    course: str | None
    grade: str | None
    percentage: float | None
    credits: float | None

    @staticmethod
    def from_row(row: Row) -> "CourseResult":
        """Build a ``CourseResult`` from a parsed grid row."""
        return CourseResult(
            course=row.text("Course"),
            grade=row.text("Grade"),
            percentage=row.number("Percentage Grades"),
            credits=row.number("Credits"),
        )


class Requirement(BaseModel):
    """One degree requirement and how far along it is."""

    name: str | None
    status: str | None
    remaining: str | None

    @staticmethod
    def from_row(row: Row) -> "Requirement":
        """Build a ``Requirement`` from a parsed grid row."""
        return Requirement(
            name=row.text("Requirement"),
            status=row.text("Status"),
            remaining=row.text("Remaining"),
        )


class AcademicProgress(BaseModel):
    """Overall degree progress: credit totals, status, and the per-requirement breakdown."""

    credits_defined: int | None
    credits_in_progress: int | None
    credits_satisfying: int | None
    remaining: str | None
    status: str | None
    requirements: list[Requirement]

    @staticmethod
    def from_page(page: Page) -> "AcademicProgress":
        """Parse the results page: the 'Overall Academic Progress' row + requirement rows."""
        grids = find_grids(page)
        overall = find_first_grid(page, label="Overall Academic Progress").rows[0]
        requirements = [
            Requirement.from_row(row)
            for grid in grids
            if grid.label is None
            for row in grid.rows
            if "Requirement" in row
        ]
        return AcademicProgress(
            credits_defined=overall.integer("Credits Defined"),
            credits_in_progress=overall.integer("Credits in Progress"),
            credits_satisfying=overall.integer("Credits Satisfying"),
            remaining=overall.text("Remaining"),
            status=overall.text("Status"),
            requirements=requirements,
        )
