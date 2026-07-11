"""The ``Student`` facade — the public entry point to a student's Workday features."""

from __future__ import annotations

from ubcworkday.client.session import WorkdaySession
from ubcworkday.student.academic_planning.evaluate_academic_requirements import (
    EvaluateAcademicRequirements,
)
from ubcworkday.student.academic_planning.view_evaluated_academic_requirements import (
    ViewEvaluatedAcademicRequirements,
)
from ubcworkday.student.academic_records.models import AcademicProgress, CourseResult
from ubcworkday.student.academic_records.view_my_academic_progress import (
    ViewMyAcademicProgress,
)
from ubcworkday.student.academic_records.view_my_academic_record import ViewMyAcademicRecord
from ubcworkday.student.academic_records.view_my_grades import ViewMyGrades
from ubcworkday.student.contacts.models import SupportContact
from ubcworkday.student.contacts.view_my_support_network import ViewMySupportNetwork
from ubcworkday.student.registration.find_course_sections import FindCourseSections
from ubcworkday.student.registration.models import EnrolledSection, Results, SavedSchedule
from ubcworkday.student.registration.view_my_courses import ViewMyCourses
from ubcworkday.student.registration.view_my_saved_schedules import ViewMySavedSchedules

__all__ = ["Student"]


class Student:
    """The student's Workday, one method per menu feature. Method names mirror the website.

    Example:
        with WorkdaySession() as s:
            me = Student(s)
            me.view_my_courses()
            me.find_course_sections("CPSC 210", term="Winter Term 1")
    """

    def __init__(self, session: WorkdaySession) -> None:
        """Bind the facade to an open ``WorkdaySession``."""
        self._session = session

    def view_my_academic_record(self) -> list[CourseResult]:
        """The student's full enrollment history."""
        return ViewMyAcademicRecord(self._session).open().enrollments()

    def view_my_grades(self, term: str) -> list[CourseResult]:
        """Grades for the academic period matching ``term`` (see ``list_terms``)."""
        return ViewMyGrades(self._session).get(term)

    def view_my_academic_progress(self) -> AcademicProgress:
        """Degree-requirement progress for the student's declared program."""
        return ViewMyAcademicProgress(self._session).open().progress()

    def find_course_sections(
        self,
        keyword: str = "",
        *,
        term: str,
        level: str = "Undergraduate",
        period: str = "Future",
    ) -> Results:
        """Search course sections in ``term``, optionally narrowed by ``keyword``."""
        return FindCourseSections(self._session).find(
            keyword, term=term, level=level, period=period
        )

    def view_my_courses(self) -> list[EnrolledSection]:
        """The student's currently enrolled sections."""
        return ViewMyCourses(self._session).open().sections()

    def view_my_saved_schedules(self) -> list[SavedSchedule]:
        """The student's saved (planned) schedules."""
        return ViewMySavedSchedules(self._session).open().schedules()

    def view_my_support_network(self) -> list[SupportContact]:
        """The student's advisors and other support contacts."""
        return ViewMySupportNetwork(self._session).open().contacts()

    def view_evaluated_academic_requirements(self, program: str) -> AcademicProgress:
        """Evaluated requirement progress for one of the student's declared ``program``s."""
        return ViewEvaluatedAcademicRequirements(self._session).get(program)

    def evaluate_academic_requirements(self, program: str) -> None:
        """Trigger a what-if evaluation against ``program``. MUTATES the account."""
        EvaluateAcademicRequirements(self._session).get(program)

    def apply_for_program_completion(self) -> None:
        """NOT BUILT — always raises ``NotImplementedError``.

        Would file a real graduation application; the flow was never captured because
        the account used to build this library isn't eligible to graduate. See
        ``ubcworkday/student/graduation/apply_for_program_completion.py``.
        """
        raise NotImplementedError(
            "apply_for_program_completion is not built: it files a real graduation "
            "application and its Workday flow was never captured."
        )

    def troubleshoot_registration(self) -> None:
        """NOT BUILT — always raises ``NotImplementedError``.

        Driving this flow needs an open registration window, which wasn't available
        when it was captured. See
        ``ubcworkday/student/registration/troubleshoot_registration.py``.
        """
        raise NotImplementedError(
            "troubleshoot_registration is not built: driving the flow requires an "
            "open registration window."
        )
