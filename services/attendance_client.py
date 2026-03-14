"""HTTP client for calling attendance-service from assessment-service."""
import os

import requests
from fastapi import HTTPException

ATTENDANCE_SERVICE_URL = os.getenv("ATTENDANCE_SERVICE_URL", "").rstrip("/")
INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN", "")
INTERNAL_SERVICE_NAME = os.getenv("INTERNAL_SERVICE_NAME", "assessment-service")
TIMEOUT = 5


def _headers():
    return {
        "Authorization": f"Bearer {INTERNAL_SERVICE_TOKEN}",
        "X-Internal-Service": INTERNAL_SERVICE_NAME,
    }


def get_student_attendance_summary(
    student_id: str,
    class_section_id: int,
    academic_term_id: int,
) -> dict | None:
    """
    Returns attendance summary dict from attendance-service, or None if
    ATTENDANCE_SERVICE_URL is not configured (integration disabled).
    """
    if not ATTENDANCE_SERVICE_URL:
        return None
    try:
        r = requests.get(
            f"{ATTENDANCE_SERVICE_URL}/timetable-attendance/attendance/students/{student_id}/summary",
            params={
                "class_section_id": class_section_id,
                "academic_term_id": academic_term_id,
            },
            headers=_headers(),
            timeout=TIMEOUT,
        )
        if r.status_code == 404:
            return {"student_id": student_id, "total_sessions": 0, "absences": 0, "attendance_percent": None}
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Attendance service error")
        return r.json()
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Attendance service connection error")
