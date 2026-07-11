"""Unofficial Python client for UBC's Workday tenant.

Public API — everything you need is here:
    from ubcworkday import WorkdaySession, Student

    with WorkdaySession() as session:
        me = Student(session)
        me.view_my_courses()
"""

from ubcworkday.client.exceptions import (
    OptionNotFound,
    SessionExpired,
    SubmitRejected,
    WorkdayError,
    WorkdayRequestError,
)
from ubcworkday.client.session import WorkdaySession
from ubcworkday.student import Student

__all__ = [
    "WorkdaySession",
    "Student",
    "WorkdayError",
    "SessionExpired",
    "WorkdayRequestError",
    "OptionNotFound",
    "SubmitRejected",
]
