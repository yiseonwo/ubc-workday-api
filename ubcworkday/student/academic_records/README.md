# Academic Records

Your academic history: full enrollment record, final grades per term, and
degree-requirement progress for your declared program. Mirrors the **Academic Records**
menu in Workday.

> Methods return pydantic models; the JSON below is what `result.model_dump()` looks like (samples are illustrative).

## Methods available

![Academics tab in Workday](../../../docs/img/academics_homepage.png)

> 🟥 available as a method · 🟦 external link (leaves Workday) · 🟩 no method yet

| Method |
| --- |
| `view_my_academic_record()` |
| `view_my_grades(term)` |
| `view_my_academic_progress()` |
| `list_terms(session)` |

## `view_my_academic_record()`

```python
from ubcworkday import WorkdaySession, Student

with WorkdaySession() as session:
    student = Student(session)
    record = student.view_my_academic_record()

print([c.model_dump() for c in record])
```

Returns `list[CourseResult]` — every course you've ever been enrolled in:

```json
[
  {"course": "CPSC 110 - Computation, Programs, and Programming", "grade": "A", "percentage": 86.0, "credits": 4.0},
  {"course": "MATH 100 - Differential Calculus", "grade": "B+", "percentage": 78.0, "credits": 3.0}
]
```

## `view_my_grades(term)`

```python
from ubcworkday import WorkdaySession, Student

with WorkdaySession() as session:
    student = Student(session)
    grades = student.view_my_grades(term="Winter Term 1")

print([c.model_dump() for c in grades])
```

Returns `list[CourseResult]` — final grades for that term:

```json
[
  {"course": "CPSC 110 - Computation, Programs, and Programming", "grade": "A", "percentage": 86.0, "credits": 4.0}
]
```

### `list_terms(session)` — values for `term`

```python
from ubcworkday import WorkdaySession
from ubcworkday.student.academic_records.view_my_grades import list_terms

with WorkdaySession() as session:
    terms = list_terms(session)

print(terms)
```

Returns `list[str]`:

```json
["2024-25 Winter Term 1 (UBC-V)", "2024-25 Winter Term 2 (UBC-V)"]
```

## `view_my_academic_progress()`

```python
from ubcworkday import WorkdaySession, Student

with WorkdaySession() as session:
    student = Student(session)
    progress = student.view_my_academic_progress()

print(progress.model_dump())
```

Returns `AcademicProgress` — degree progress for your declared program:

```json
{
  "credits_defined": 120,
  "credits_in_progress": 12,
  "credits_satisfying": 78,
  "remaining": "30 Credits",
  "status": "In Progress",
  "requirements": [
    {"name": "Communication Requirement", "status": "Satisfied", "remaining": null},
    {"name": "Upper-level Credits", "status": "Not Satisfied", "remaining": "18 Credits"}
  ]
}
```
