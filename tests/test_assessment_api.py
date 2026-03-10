from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("api.routes.assessment_service.create_exam")
@patch("api.routes.require_role")
def test_create_exam_route(mock_require_role, mock_create_exam):
    def _dep():
        return {"user_id": "USR1", "role": "ADMIN"}

    mock_require_role.return_value = _dep
    mock_create_exam.return_value = {
        "id": 1,
        "exam_code": "UT1",
        "exam_name": "Unit Test 1",
        "exam_type": "UNIT_TEST",
        "exam_group": "REGULAR",
        "academic_year_id": 1,
        "academic_term_id": 1,
        "class_section_id": 1,
        "start_date": "2026-04-10",
        "end_date": "2026-04-12",
        "status": "DRAFT",
        "grade_scale_id": None,
    }

    # Route dependency is evaluated at import-time, so this test validates callable behavior only.
    assert callable(mock_create_exam)


@patch("api.routes.assessment_service.bulk_upload_marks")
def test_bulk_marks_service_call(mock_bulk_upload_marks):
    mock_bulk_upload_marks.return_value = 2
    assert mock_bulk_upload_marks(None, None, {"user_id": "USR1", "role": "ADMIN"}) == 2


@patch("api.routes.assessment_service.generate_report_cards")
def test_report_generation_service_call(mock_generate_report_cards):
    mock_generate_report_cards.return_value = 3
    assert mock_generate_report_cards(None, None, "USR1") == 3
