import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_role
from schemas.dto import (
    AssignmentBulkMarksPayload,
    AssignmentCreate,
    AssignmentOut,
    AssignmentSubmissionCreate,
    AssignmentSubmissionOut,
    AssignmentUpdate,
    BulkMarksPayload,
    BulkOperationResponse,
    ComponentWeightCreate,
    ComponentWeightOut,
    ExamCreate,
    ExamOut,
    ExamSubjectCreate,
    ExamSubjectOut,
    ExamUpdate,
    GenerateReportCardsPayload,
    GradeBandCreate,
    GradeBandOut,
    GradeScaleCreate,
    GradeScaleOut,
    GradeScaleUpdate,
    MessageResponse,
    PagedResponse,
    PublishReportCardsPayload,
    RegisterStudentsPayload,
    ReportCardOut,
    VerifyMarkPayload,
    VerifyAssignmentMarkPayload,
)
from services import assessment_service

router = APIRouter(prefix="/assessment", tags=["Assessment Service"])
logger = logging.getLogger(__name__)


@router.post("/grade-scales", response_model=GradeScaleOut)
def create_grade_scale(
    data: GradeScaleCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.create_grade_scale(db, data, user["user_id"])


@router.get("/grade-scales", response_model=PagedResponse)
def list_grade_scales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    total, rows = assessment_service.list_grade_scales(db, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.put("/grade-scales/{scale_id}", response_model=GradeScaleOut)
def update_grade_scale(
    scale_id: int,
    data: GradeScaleUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.update_grade_scale(db, scale_id, data)


@router.delete("/grade-scales/{scale_id}", response_model=MessageResponse)
def delete_grade_scale(
    scale_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    assessment_service.delete_grade_scale(db, scale_id)
    return {"message": "Grade scale deleted"}


@router.post("/grade-bands", response_model=GradeBandOut)
def create_grade_band(
    data: GradeBandCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.create_grade_band(db, data)


@router.get("/grade-bands", response_model=PagedResponse)
def list_grade_bands(
    scale_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    total, rows = assessment_service.list_grade_bands(db, scale_id, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.post("/component-weights", response_model=ComponentWeightOut)
def create_component_weight(
    data: ComponentWeightCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.create_component_weight(db, data, user["user_id"])


@router.get("/component-weights", response_model=PagedResponse)
def list_component_weights(
    academic_year_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    total, rows = assessment_service.list_component_weights(db, page, page_size, academic_year_id)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.post("/exams", response_model=ExamOut)
def create_exam(
    data: ExamCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.create_exam(db, data, user["user_id"])


@router.get("/exams", response_model=PagedResponse)
def list_exams(
    academic_year_id: int | None = None,
    class_section_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER", "SERVICE"])),
):
    total, rows = assessment_service.list_exams(db, page, page_size, academic_year_id, class_section_id)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    return assessment_service.get_exam(db, exam_id)


@router.put("/exams/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    data: ExamUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.update_exam(db, exam_id, data)


@router.patch("/exams/{exam_id}/publish", response_model=ExamOut)
def publish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.publish_exam(db, exam_id, user["user_id"])


@router.patch("/exams/{exam_id}/cancel", response_model=ExamOut)
def cancel_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.cancel_exam(db, exam_id)


@router.post("/exam-subjects", response_model=ExamSubjectOut)
def create_exam_subject(
    data: ExamSubjectCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.create_exam_subject(db, data)


@router.get("/exam-subjects", response_model=PagedResponse)
def list_exam_subjects(
    exam_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER", "SERVICE"])),
):
    total, rows = assessment_service.list_exam_subjects(db, exam_id, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.post("/assignments", response_model=AssignmentOut)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.create_assignment(db, data, user["user_id"])


@router.get("/assignments", response_model=PagedResponse)
def list_assignments(
    academic_year_id: int | None = None,
    class_section_id: int | None = None,
    subject_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER", "SERVICE"])),
):
    total, rows = assessment_service.list_assignments(
        db,
        page,
        page_size,
        academic_year_id,
        class_section_id,
        subject_id,
    )
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.get("/assignments/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER", "STUDENT"])),
):
    return assessment_service.get_assignment(db, assignment_id)


@router.put("/assignments/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.update_assignment(db, assignment_id, data)


@router.patch("/assignments/{assignment_id}/publish", response_model=AssignmentOut)
def publish_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.publish_assignment(db, assignment_id)


@router.patch("/assignments/{assignment_id}/close", response_model=AssignmentOut)
def close_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    return assessment_service.close_assignment(db, assignment_id)


@router.patch("/assignments/{assignment_id}/cancel", response_model=AssignmentOut)
def cancel_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    return assessment_service.cancel_assignment(db, assignment_id)


@router.post("/assignments/{assignment_id}/submit", response_model=AssignmentSubmissionOut)
def submit_assignment(
    assignment_id: int,
    payload: AssignmentSubmissionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["STUDENT", "ADMIN"])),
):
    student_id = assessment_service.get_student_id_for_user(db, user["user_id"]) if user["role"] == "STUDENT" else None
    if user["role"] == "ADMIN":
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Admin cannot submit on behalf via this endpoint")
    if not student_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Student profile not found")

    return assessment_service.submit_assignment(db, assignment_id, student_id, payload)


@router.post("/assignments/marks/bulk", response_model=BulkOperationResponse)
def bulk_upload_assignment_marks(
    payload: AssignmentBulkMarksPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    count = assessment_service.bulk_upload_assignment_marks(db, payload, user)
    return {"message": "Assignment marks uploaded", "count": count}


@router.patch("/assignment-marks/{submission_id}/verify", response_model=MessageResponse)
def verify_assignment_marks(
    submission_id: int,
    payload: VerifyAssignmentMarkPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    assessment_service.verify_assignment_marks(db, submission_id, user["user_id"], payload.feedback)
    return {"message": "Assignment marks verified"}


@router.post("/exam/register-students", response_model=BulkOperationResponse)
def register_students(
    data: RegisterStudentsPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    result = assessment_service.register_students(db, data.exam_subject_id, data.student_ids)
    return {
        "message": "Student registration processed",
        "count": result["created"],
        "processed": result["processed"],
        "skipped": result["skipped"],
        "errors": result["errors"],
    }


@router.post("/marks/bulk", response_model=BulkOperationResponse)
def bulk_upload_marks(
    payload: BulkMarksPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER"])),
):
    uploaded = assessment_service.bulk_upload_marks(db, payload, user)
    return {"message": "Marks uploaded", "count": uploaded}


@router.patch("/marks/{registration_id}/verify", response_model=MessageResponse)
def verify_marks(
    registration_id: int,
    data: VerifyMarkPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    assessment_service.verify_marks(db, registration_id, user["user_id"], data.remarks)
    return {"message": "Marks verified"}


@router.post("/report-cards/generate", response_model=BulkOperationResponse)
def generate_report_cards(
    payload: GenerateReportCardsPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    count = assessment_service.generate_report_cards(db, payload, user["user_id"])
    return {"message": "Report cards generated", "count": count}


@router.post("/report-cards/publish", response_model=BulkOperationResponse)
def publish_report_cards(
    payload: PublishReportCardsPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN"])),
):
    count = assessment_service.publish_report_cards(db, payload)
    return {"message": "Report cards published", "count": count}


@router.get("/report-cards/student/{student_id}", response_model=PagedResponse)
def get_student_report_cards(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "STUDENT", "SERVICE"])),
):
    if user["role"] == "STUDENT":
        token_student_id = assessment_service.get_student_id_for_user(db, user["user_id"])
        if token_student_id != student_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Students can only view their own report cards")

    total, rows = assessment_service.get_student_report_cards(db, student_id, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.get("/history/student/{student_id}/exam", response_model=PagedResponse)
def student_exam_history(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "STUDENT", "SERVICE"])),
):
    if user["role"] == "STUDENT":
        token_student_id = assessment_service.get_student_id_for_user(db, user["user_id"])
        if token_student_id != student_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Students can only view their own history")

    total, rows = assessment_service.list_exam_history(db, student_id, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.get("/history/student/{student_id}/academic", response_model=PagedResponse)
def student_academic_history(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "STUDENT", "SERVICE"])),
):
    if user["role"] == "STUDENT":
        token_student_id = assessment_service.get_student_id_for_user(db, user["user_id"])
        if token_student_id != student_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Students can only view their own history")

    total, rows = assessment_service.list_academic_history(db, student_id, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


# =====================================================================
# HOLISTIC PROGRESS REPORT
# =====================================================================

@router.get("/progress/student/{student_id}")
def student_holistic_progress(
    student_id: str,
    class_section_id: int = Query(..., description="Current class section ID"),
    academic_term_id: int = Query(..., description="Current academic term ID"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "TEACHER", "STUDENT", "PARENT", "SERVICE"])),
):
    """
    Holistic student progress report combining:
    - Latest published report card (exam performance, subject grades)
    - Assignment submission rate (total assigned vs submitted)
    - Attendance summary (via attendance-service)
    """
    from fastapi import HTTPException
    from services.attendance_client import get_student_attendance_summary

    # --- Guard for STUDENT role ---
    if user["role"] == "STUDENT":
        token_student_id = assessment_service.get_student_id_for_user(db, user["user_id"])
        if token_student_id != student_id:
            raise HTTPException(status_code=403, detail="Students can only view their own progress")

    # --- Latest published report card ---
    from models.sql_models import (
        AssessmentReportCard,
        AssessmentReportCardSubject,
        AssessmentAssignment,
        AssessmentAssignmentSubmission,
        Subject,
    )

    latest_rc = (
        db.query(AssessmentReportCard)
        .filter(
            AssessmentReportCard.student_id == student_id,
            AssessmentReportCard.publish_status == "PUBLISHED",
        )
        .order_by(AssessmentReportCard.generated_at.desc())
        .first()
    )

    report_card_summary = None
    if latest_rc:
        rc_subjects = (
            db.query(AssessmentReportCardSubject)
            .filter(AssessmentReportCardSubject.report_card_id == latest_rc.id)
            .all()
        )
        report_card_summary = {
            "report_card_id": latest_rc.id,
            "academic_year_id": latest_rc.academic_year_id,
            "academic_term_id": latest_rc.academic_term_id,
            "report_type": latest_rc.report_type,
            "total_max_marks": float(latest_rc.total_max_marks) if latest_rc.total_max_marks else None,
            "total_obtained": float(latest_rc.total_obtained) if latest_rc.total_obtained else None,
            "percentage": float(latest_rc.percentage) if latest_rc.percentage else None,
            "overall_grade": latest_rc.overall_grade,
            "result_status": latest_rc.result_status,
            "rank_in_class": latest_rc.rank_in_class,
            "subjects": [
                {
                    "subject_id": s.subject_id,
                    "subject_obtained": float(s.subject_obtained) if s.subject_obtained else None,
                    "subject_max_marks": float(s.subject_max_marks) if s.subject_max_marks else None,
                    "subject_percentage": float(s.subject_percentage) if s.subject_percentage else None,
                    "grade_label": s.grade_label,
                    "result_status": s.result_status,
                }
                for s in rc_subjects
            ],
        }

    # --- Assignment submission rate (for this class-section + term) ---
    total_assignments = (
        db.query(AssessmentAssignment)
        .filter(
            AssessmentAssignment.class_section_id == class_section_id,
            AssessmentAssignment.academic_term_id == academic_term_id,
            AssessmentAssignment.status == "PUBLISHED",
        )
        .count()
    )

    submitted_assignments = (
        db.query(AssessmentAssignmentSubmission)
        .join(
            AssessmentAssignment,
            AssessmentAssignment.id == AssessmentAssignmentSubmission.assignment_id,
        )
        .filter(
            AssessmentAssignment.class_section_id == class_section_id,
            AssessmentAssignment.academic_term_id == academic_term_id,
            AssessmentAssignmentSubmission.student_id == student_id,
            AssessmentAssignmentSubmission.is_latest.is_(True),
            AssessmentAssignmentSubmission.submission_status.in_(["SUBMITTED", "LATE_SUBMITTED"]),
        )
        .count()
    )

    submission_rate = (
        round((submitted_assignments / total_assignments) * 100, 2)
        if total_assignments > 0
        else None
    )

    # --- Attendance (cross-service call) ---
    attendance_summary = get_student_attendance_summary(
        student_id=student_id,
        class_section_id=class_section_id,
        academic_term_id=academic_term_id,
    )

    return {
        "student_id": student_id,
        "class_section_id": class_section_id,
        "academic_term_id": academic_term_id,
        "report_card": report_card_summary,
        "assignment_stats": {
            "total_published_assignments": total_assignments,
            "submitted": submitted_assignments,
            "submission_rate_percent": submission_rate,
        },
        "attendance": attendance_summary,
    }


@router.get("/history/student/{student_id}/assignments", response_model=PagedResponse)
def student_assignment_history(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role(["ADMIN", "STUDENT", "SERVICE"])),
):
    if user["role"] == "STUDENT":
        token_student_id = assessment_service.get_student_id_for_user(db, user["user_id"])
        if token_student_id != student_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Students can only view their own history")

    total, rows = assessment_service.list_assignment_history(db, student_id, page, page_size)
    return {"page": page, "page_size": page_size, "total": total, "data": rows}
