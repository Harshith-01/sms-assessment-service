import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.sql_models import (
    AcademicTerm,
    AcademicYear,
    AssessmentExam,
    AssessmentExamRegistration,
    AssessmentExamSubject,
    AssessmentGradeBand,
    AssessmentGradeScale,
    AssessmentAssignment,
    AssessmentAssignmentMark,
    AssessmentAssignmentSubmission,
    AssessmentComponent,
    AssessmentMark,
    AssessmentReportCard,
    AssessmentReportCardSubject,
    AssessmentSubjectComponentWeight,
    AssessmentStudentAssignmentHistory,
    AssessmentStudentAcademicHistory,
    AssessmentStudentExamHistory,
    ClassSection,
    ClassSubject,
    Student,
    StudentSubjectEnrollment,
    Subject,
    Teacher,
)
from schemas.dto import (
    AssignmentBulkMarksPayload,
    AssignmentCreate,
    AssignmentSubmissionCreate,
    AssignmentUpdate,
    BulkMarksPayload,
    ExamCreate,
    ExamSubjectCreate,
    ExamUpdate,
    ComponentWeightCreate,
    GenerateReportCardsPayload,
    GradeBandCreate,
    GradeScaleCreate,
    GradeScaleUpdate,
    PublishReportCardsPayload,
)

logger = logging.getLogger(__name__)


def _ensure_year_exists(db: Session, year_id: int) -> None:
    if not db.get(AcademicYear, year_id):
        raise HTTPException(status_code=404, detail="Academic year not found")


def _ensure_term_belongs_to_year(db: Session, term_id: int, year_id: int) -> None:
    term = db.get(AcademicTerm, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Academic term not found")
    if term.academic_year_id != year_id:
        raise HTTPException(status_code=400, detail="Academic term does not belong to academic year")


def _ensure_class_section_exists(db: Session, class_section_id: int) -> ClassSection:
    class_section = db.get(ClassSection, class_section_id)
    if not class_section:
        raise HTTPException(status_code=404, detail="Class section not found")
    return class_section


def get_teacher_id_for_user(db: Session, user_id: str) -> str | None:
    teacher = db.query(Teacher).filter(Teacher.user_id == user_id).first()
    return teacher.id if teacher else None


def get_student_id_for_user(db: Session, user_id: str) -> str | None:
    student = db.query(Student).filter(Student.user_id == user_id).first()
    return student.id if student else None


def create_grade_scale(db: Session, data: GradeScaleCreate, actor_user_id: str):
    if data.academic_year_id is not None:
        _ensure_year_exists(db, data.academic_year_id)

    grade_scale = AssessmentGradeScale(
        **data.model_dump(),
        created_by=actor_user_id,
    )

    try:
        if data.is_default:
            db.query(AssessmentGradeScale).filter(
                AssessmentGradeScale.academic_year_id == data.academic_year_id,
                AssessmentGradeScale.department_id == data.department_id,
                AssessmentGradeScale.is_default.is_(True),
            ).update({"is_default": False})

        db.add(grade_scale)
        db.commit()
        db.refresh(grade_scale)

        logger.info(
            "grade_scale_created",
            extra={
                "event": "grade_scale_created",
                "grade_scale_id": grade_scale.id,
                "actor_user_id": actor_user_id,
            },
        )
        return grade_scale
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Grade scale conflict") from exc


def list_grade_scales(db: Session, page: int, page_size: int):
    query = db.query(AssessmentGradeScale).order_by(AssessmentGradeScale.id.desc())
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records


def update_grade_scale(db: Session, scale_id: int, data: GradeScaleUpdate):
    grade_scale = db.get(AssessmentGradeScale, scale_id)
    if not grade_scale:
        raise HTTPException(status_code=404, detail="Grade scale not found")

    updates = data.model_dump(exclude_unset=True)

    if "academic_year_id" in updates and updates["academic_year_id"] is not None:
        _ensure_year_exists(db, updates["academic_year_id"])

    try:
        if updates.get("is_default") is True:
            target_year = updates.get("academic_year_id", grade_scale.academic_year_id)
            target_department = updates.get("department_id", grade_scale.department_id)
            db.query(AssessmentGradeScale).filter(
                AssessmentGradeScale.id != grade_scale.id,
                AssessmentGradeScale.academic_year_id == target_year,
                AssessmentGradeScale.department_id == target_department,
                AssessmentGradeScale.is_default.is_(True),
            ).update({"is_default": False})

        for key, value in updates.items():
            setattr(grade_scale, key, value)

        db.commit()
        db.refresh(grade_scale)
        return grade_scale
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Grade scale conflict") from exc


def delete_grade_scale(db: Session, scale_id: int):
    grade_scale = db.get(AssessmentGradeScale, scale_id)
    if not grade_scale:
        raise HTTPException(status_code=404, detail="Grade scale not found")

    db.delete(grade_scale)
    db.commit()


def create_grade_band(db: Session, data: GradeBandCreate):
    if not db.get(AssessmentGradeScale, data.grade_scale_id):
        raise HTTPException(status_code=404, detail="Grade scale not found")

    band = AssessmentGradeBand(**data.model_dump())

    try:
        db.add(band)
        db.commit()
        db.refresh(band)
        return band
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Grade band conflict") from exc


def list_grade_bands(db: Session, scale_id: int, page: int, page_size: int):
    query = db.query(AssessmentGradeBand).filter(AssessmentGradeBand.grade_scale_id == scale_id).order_by(
        AssessmentGradeBand.sort_order
    )
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records


def create_exam(db: Session, data: ExamCreate, actor_user_id: str):
    _ensure_year_exists(db, data.academic_year_id)

    if data.academic_term_id is not None:
        _ensure_term_belongs_to_year(db, data.academic_term_id, data.academic_year_id)

    class_section = _ensure_class_section_exists(db, data.class_section_id)
    if class_section.academic_year_id and class_section.academic_year_id != data.academic_year_id:
        raise HTTPException(status_code=400, detail="Class section academic year mismatch")

    exam = AssessmentExam(**data.model_dump(), created_by=actor_user_id)

    try:
        db.add(exam)
        db.commit()
        db.refresh(exam)

        logger.info(
            "exam_created",
            extra={
                "event": "exam_created",
                "exam_id": exam.id,
                "actor_user_id": actor_user_id,
                "class_section_id": exam.class_section_id,
            },
        )
        return exam
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Exam conflict") from exc


def list_exams(db: Session, page: int, page_size: int, academic_year_id: int | None, class_section_id: int | None):
    query = db.query(AssessmentExam)

    if academic_year_id is not None:
        query = query.filter(AssessmentExam.academic_year_id == academic_year_id)

    if class_section_id is not None:
        query = query.filter(AssessmentExam.class_section_id == class_section_id)

    query = query.order_by(AssessmentExam.id.desc())
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records


def get_exam(db: Session, exam_id: int):
    exam = db.get(AssessmentExam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


def update_exam(db: Session, exam_id: int, data: ExamUpdate):
    exam = get_exam(db, exam_id)

    if exam.status in {"PUBLISHED", "IN_PROGRESS", "COMPLETED", "ARCHIVED", "CANCELLED"}:
        raise HTTPException(status_code=400, detail="Exam cannot be updated in current status")

    updates = data.model_dump(exclude_unset=True)

    target_year = updates.get("academic_year_id", exam.academic_year_id)
    target_term = updates.get("academic_term_id", exam.academic_term_id)
    target_class_section = updates.get("class_section_id", exam.class_section_id)

    _ensure_year_exists(db, target_year)

    if target_term is not None:
        _ensure_term_belongs_to_year(db, target_term, target_year)

    class_section = _ensure_class_section_exists(db, target_class_section)
    if class_section.academic_year_id and class_section.academic_year_id != target_year:
        raise HTTPException(status_code=400, detail="Class section academic year mismatch")

    start_date = updates.get("start_date", exam.start_date)
    end_date = updates.get("end_date", exam.end_date)
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Invalid exam date range")

    try:
        for key, value in updates.items():
            setattr(exam, key, value)
        db.commit()
        db.refresh(exam)
        return exam
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Exam update conflict") from exc


def publish_exam(db: Session, exam_id: int, actor_user_id: str):
    exam = get_exam(db, exam_id)

    if exam.status in {"CANCELLED", "ARCHIVED"}:
        raise HTTPException(status_code=400, detail="Cannot publish cancelled or archived exam")

    if exam.status == "PUBLISHED":
        return exam

    has_subjects = db.query(AssessmentExamSubject.id).filter(AssessmentExamSubject.exam_id == exam.id).first()
    if not has_subjects:
        raise HTTPException(status_code=400, detail="Exam subjects must be configured before publishing")

    exam.status = "PUBLISHED"
    exam.approved_by = actor_user_id
    exam.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exam)
    return exam


def cancel_exam(db: Session, exam_id: int):
    exam = get_exam(db, exam_id)
    if exam.status in {"COMPLETED", "ARCHIVED"}:
        raise HTTPException(status_code=400, detail="Completed or archived exams cannot be cancelled")

    exam.status = "CANCELLED"
    db.commit()
    db.refresh(exam)
    return exam


def _ensure_subject_mapped_to_exam_class(db: Session, exam: AssessmentExam, subject_id: int):
    class_section = _ensure_class_section_exists(db, exam.class_section_id)
    mapping = db.query(ClassSubject.id).filter(
        ClassSubject.class_id == class_section.class_id,
        ClassSubject.subject_id == subject_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=400, detail="Subject is not mapped to exam class")


def create_exam_subject(db: Session, data: ExamSubjectCreate):
    exam = get_exam(db, data.exam_id)

    subject = db.get(Subject, data.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    _ensure_subject_mapped_to_exam_class(db, exam, data.subject_id)

    if data.evaluator_teacher_id and not db.get(Teacher, data.evaluator_teacher_id):
        raise HTTPException(status_code=404, detail="Evaluator teacher not found")

    exam_subject = AssessmentExamSubject(**data.model_dump())

    try:
        db.add(exam_subject)
        db.commit()
        db.refresh(exam_subject)
        return exam_subject
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Exam subject conflict") from exc


def list_exam_subjects(db: Session, exam_id: int, page: int, page_size: int):
    query = db.query(AssessmentExamSubject).filter(AssessmentExamSubject.exam_id == exam_id).order_by(AssessmentExamSubject.id)
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records


def register_students(db: Session, exam_subject_id: int, student_ids: list[str]):
    exam_subject = db.get(AssessmentExamSubject, exam_subject_id)
    if not exam_subject:
        raise HTTPException(status_code=404, detail="Exam subject not found")

    exam = get_exam(db, exam_subject.exam_id)

    unique_ids = sorted(set(student_ids))
    if not unique_ids:
        raise HTTPException(status_code=400, detail="No students provided")

    created_count = 0
    for student_id in unique_ids:
        if not db.get(Student, student_id):
            raise HTTPException(status_code=404, detail=f"Student not found: {student_id}")

        enrollment = db.query(StudentSubjectEnrollment.id).filter(
            StudentSubjectEnrollment.student_id == student_id,
            StudentSubjectEnrollment.subject_id == exam_subject.subject_id,
            StudentSubjectEnrollment.academic_year_id == exam.academic_year_id,
            StudentSubjectEnrollment.class_section_id == exam.class_section_id,
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=400,
                detail=f"Student not enrolled for exam subject: {student_id}",
            )

        exists = db.query(AssessmentExamRegistration.id).filter(
            AssessmentExamRegistration.exam_subject_id == exam_subject_id,
            AssessmentExamRegistration.student_id == student_id,
        ).first()
        if exists:
            continue

        db.add(
            AssessmentExamRegistration(
                exam_subject_id=exam_subject_id,
                student_id=student_id,
                enrollment_id=enrollment[0],
                attendance_status="PRESENT",
            )
        )
        created_count += 1

    db.commit()
    return created_count


def _ensure_teacher_can_enter_marks(db: Session, exam_subject_id: int, actor_user: dict):
    if actor_user["role"] == "ADMIN":
        return

    exam_subject = db.get(AssessmentExamSubject, exam_subject_id)
    if not exam_subject:
        raise HTTPException(status_code=404, detail="Exam subject not found")

    teacher_id = get_teacher_id_for_user(db, actor_user["user_id"])
    if not teacher_id:
        raise HTTPException(status_code=403, detail="Teacher profile not found")

    if exam_subject.evaluator_teacher_id and exam_subject.evaluator_teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Only assigned evaluator can upload marks")


def bulk_upload_marks(db: Session, payload: BulkMarksPayload, actor_user: dict):
    _ensure_teacher_can_enter_marks(db, payload.exam_subject_id, actor_user)

    rows = [row.model_dump() for row in payload.rows]

    try:
        db.execute(
            text(
                "SELECT public.assessment_bulk_upsert_marks(:exam_subject_id, CAST(:rows AS jsonb), :actor_user_id)"
            ),
            {
                "exam_subject_id": payload.exam_subject_id,
                "rows": json.dumps(rows),
                "actor_user_id": actor_user["user_id"],
            },
        )
        db.commit()

        logger.info(
            "marks_bulk_uploaded",
            extra={
                "event": "marks_bulk_uploaded",
                "exam_subject_id": payload.exam_subject_id,
                "row_count": len(rows),
                "actor_user_id": actor_user["user_id"],
            },
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Bulk marks upload failed: {exc}") from exc

    return len(rows)


def verify_marks(db: Session, registration_id: int, actor_user_id: str, remarks: str | None):
    mark = db.query(AssessmentMark).filter(AssessmentMark.registration_id == registration_id).first()
    if not mark:
        raise HTTPException(status_code=404, detail="Marks record not found for registration")

    if mark.entry_status == "LOCKED":
        raise HTTPException(status_code=400, detail="Locked marks cannot be verified")

    mark.entry_status = "VERIFIED"
    mark.verified_by = actor_user_id
    mark.verified_at = datetime.now(timezone.utc)
    if remarks:
        mark.remarks = remarks

    db.commit()
    db.refresh(mark)
    return mark


def _grade_point_for_label(db: Session, grade_label: str | None) -> Decimal | None:
    if not grade_label:
        return None
    band = db.query(AssessmentGradeBand).filter(AssessmentGradeBand.grade_label == grade_label).order_by(
        AssessmentGradeBand.id.desc()
    ).first()
    return band.grade_point if band else None


def generate_report_cards(db: Session, payload: GenerateReportCardsPayload, actor_user_id: str):
    _ensure_year_exists(db, payload.academic_year_id)

    if payload.report_type == "TERM" and payload.academic_term_id is None:
        raise HTTPException(status_code=400, detail="academic_term_id is required for TERM report")

    if payload.academic_term_id is not None:
        _ensure_term_belongs_to_year(db, payload.academic_term_id, payload.academic_year_id)

    base_query = (
        db.query(
            AssessmentExamRegistration.student_id,
            AssessmentExam.class_section_id,
            AssessmentExamSubject.subject_id,
            AssessmentExamSubject.max_marks,
            AssessmentExamRegistration.attendance_status,
            AssessmentMark.final_marks,
            AssessmentMark.is_pass,
            AssessmentMark.grade_label,
        )
        .join(AssessmentExamSubject, AssessmentExamSubject.id == AssessmentExamRegistration.exam_subject_id)
        .join(AssessmentExam, AssessmentExam.id == AssessmentExamSubject.exam_id)
        .outerjoin(AssessmentMark, AssessmentMark.registration_id == AssessmentExamRegistration.id)
        .filter(
            AssessmentExam.academic_year_id == payload.academic_year_id,
            AssessmentExam.status.in_(["PUBLISHED", "COMPLETED", "ARCHIVED"]),
        )
    )

    if payload.academic_term_id is not None:
        base_query = base_query.filter(AssessmentExam.academic_term_id == payload.academic_term_id)

    if payload.class_section_id is not None:
        base_query = base_query.filter(AssessmentExam.class_section_id == payload.class_section_id)

    if payload.student_ids:
        base_query = base_query.filter(AssessmentExamRegistration.student_id.in_(payload.student_ids))

    records = base_query.all()

    assignment_query = (
        db.query(
            AssessmentAssignmentSubmission.student_id,
            AssessmentAssignment.class_section_id,
            AssessmentAssignment.subject_id,
            AssessmentAssignment.max_marks,
            AssessmentAssignmentSubmission.submission_status,
            AssessmentAssignmentMark.final_marks,
            AssessmentAssignmentMark.is_pass,
            AssessmentAssignmentMark.grade_label,
        )
        .join(AssessmentAssignment, AssessmentAssignment.id == AssessmentAssignmentSubmission.assignment_id)
        .outerjoin(AssessmentAssignmentMark, AssessmentAssignmentMark.submission_id == AssessmentAssignmentSubmission.id)
        .filter(
            AssessmentAssignment.status.in_(["PUBLISHED", "CLOSED", "ARCHIVED"]),
            AssessmentAssignmentSubmission.is_latest.is_(True),
            AssessmentAssignment.academic_year_id == payload.academic_year_id,
        )
    )

    if payload.academic_term_id is not None:
        assignment_query = assignment_query.filter(AssessmentAssignment.academic_term_id == payload.academic_term_id)

    if payload.class_section_id is not None:
        assignment_query = assignment_query.filter(AssessmentAssignment.class_section_id == payload.class_section_id)

    if payload.student_ids:
        assignment_query = assignment_query.filter(AssessmentAssignmentSubmission.student_id.in_(payload.student_ids))

    assignment_records = assignment_query.all()

    combined_records = [
        SimpleNamespace(
            student_id=r.student_id,
            class_section_id=r.class_section_id,
            subject_id=r.subject_id,
            max_marks=r.max_marks,
            attendance_status=r.attendance_status,
            final_marks=r.final_marks,
            is_pass=r.is_pass,
            grade_label=r.grade_label,
            component_code="EXAM",
        )
        for r in records
    ]

    for r in assignment_records:
        if r.submission_status in {"NOT_SUBMITTED", "MISSING"}:
            attendance_status = "ABSENT"
        elif r.submission_status == "EXCUSED":
            attendance_status = "EXEMPT"
        elif r.submission_status == "PLAGIARIZED":
            attendance_status = "MALPRACTICE"
        else:
            attendance_status = "PRESENT"

        combined_records.append(
            SimpleNamespace(
                student_id=r.student_id,
                class_section_id=r.class_section_id,
                subject_id=r.subject_id,
                max_marks=r.max_marks,
                attendance_status=attendance_status,
                final_marks=r.final_marks,
                is_pass=r.is_pass,
                grade_label=r.grade_label,
                component_code="ASSIGNMENT",
            )
        )

    if not combined_records:
        raise HTTPException(status_code=404, detail="No assessment data found for report generation")

    weight_query = (
        db.query(
            AssessmentSubjectComponentWeight.class_section_id,
            AssessmentSubjectComponentWeight.subject_id,
            AssessmentComponent.component_code,
            AssessmentSubjectComponentWeight.weight_percent,
        )
        .join(AssessmentComponent, AssessmentComponent.id == AssessmentSubjectComponentWeight.component_id)
        .filter(
            AssessmentSubjectComponentWeight.academic_year_id == payload.academic_year_id,
            AssessmentSubjectComponentWeight.is_active.is_(True),
        )
    )

    if payload.academic_term_id is not None:
        weight_query = weight_query.filter(
            AssessmentSubjectComponentWeight.academic_term_id == payload.academic_term_id
        )

    if payload.class_section_id is not None:
        weight_query = weight_query.filter(
            AssessmentSubjectComponentWeight.class_section_id == payload.class_section_id
        )

    weight_rows = weight_query.all()
    weights_map: dict[tuple[int, int, str], Decimal] = {}
    weighted_subject_scope: set[tuple[int, int]] = set()
    for w in weight_rows:
        weights_map[(w.class_section_id, w.subject_id, w.component_code)] = Decimal(w.weight_percent)
        weighted_subject_scope.add((w.class_section_id, w.subject_id))

    grouped: dict[tuple[str, int], list] = defaultdict(list)
    for row in combined_records:
        grouped[(row.student_id, row.class_section_id)].append(row)

    generated_count = 0

    for (student_id, class_section_id), rows in grouped.items():
        subject_map: dict[int, dict] = defaultdict(
            lambda: {
                "max_total": Decimal("0"),
                "obtained_total": Decimal("0"),
                "absent": False,
                "failed": False,
                "grade_labels": [],
            }
        )

        for row in rows:
            bucket = subject_map[row.subject_id]

            raw_max_marks = Decimal(row.max_marks or 0)
            raw_obtained = Decimal(row.final_marks or 0) if row.final_marks is not None else Decimal("0")

            if (class_section_id, row.subject_id) in weighted_subject_scope:
                component_weight = weights_map.get((class_section_id, row.subject_id, row.component_code), Decimal("0"))
                bucket["max_total"] += component_weight
                if raw_max_marks > 0:
                    bucket["obtained_total"] += (raw_obtained * component_weight / raw_max_marks)
            else:
                bucket["max_total"] += raw_max_marks
                bucket["obtained_total"] += raw_obtained

            if row.attendance_status == "ABSENT":
                bucket["absent"] = True
            if row.is_pass is False:
                bucket["failed"] = True
            if row.grade_label:
                bucket["grade_labels"].append(row.grade_label)

        total_max = Decimal("0")
        total_obtained = Decimal("0")
        subject_rows = []
        any_fail = False
        any_absent = False

        for subject_id, values in subject_map.items():
            subject_max = values["max_total"]
            subject_obtained = values["obtained_total"]
            total_max += subject_max
            total_obtained += subject_obtained

            percentage = Decimal("0") if subject_max == 0 else (subject_obtained * Decimal("100") / subject_max)
            percentage = percentage.quantize(Decimal("0.01"))

            if values["absent"]:
                result_status = "ABSENT"
                any_absent = True
            elif values["failed"]:
                result_status = "FAIL"
                any_fail = True
            else:
                result_status = "PASS"

            chosen_grade_label = values["grade_labels"][0] if values["grade_labels"] else None
            grade_point = _grade_point_for_label(db, chosen_grade_label)

            subject_rows.append(
                {
                    "subject_id": subject_id,
                    "subject_max_marks": subject_max,
                    "subject_obtained": subject_obtained,
                    "subject_percentage": percentage,
                    "grade_label": chosen_grade_label,
                    "grade_point": grade_point,
                    "result_status": result_status,
                    "absent_in_any_exam": values["absent"],
                }
            )

        overall_percentage = Decimal("0") if total_max == 0 else (total_obtained * Decimal("100") / total_max)
        overall_percentage = overall_percentage.quantize(Decimal("0.01"))

        if any_fail:
            result_status = "FAIL"
        elif any_absent:
            result_status = "PARTIAL"
        else:
            result_status = "PASS"

        existing_rc = db.query(AssessmentReportCard).filter(
            AssessmentReportCard.student_id == student_id,
            AssessmentReportCard.academic_year_id == payload.academic_year_id,
            AssessmentReportCard.academic_term_id == payload.academic_term_id,
            AssessmentReportCard.report_type == payload.report_type.value,
        ).first()

        if existing_rc:
            report_card = existing_rc
            report_card.class_section_id = class_section_id
            report_card.publish_status = "DRAFT"
            report_card.total_max_marks = total_max
            report_card.total_obtained = total_obtained
            report_card.percentage = overall_percentage
            report_card.result_status = result_status
            report_card.generated_by = actor_user_id
            report_card.generated_at = datetime.now(timezone.utc)
        else:
            report_card = AssessmentReportCard(
                student_id=student_id,
                academic_year_id=payload.academic_year_id,
                academic_term_id=payload.academic_term_id,
                class_section_id=class_section_id,
                report_type=payload.report_type.value,
                publish_status="DRAFT",
                total_max_marks=total_max,
                total_obtained=total_obtained,
                percentage=overall_percentage,
                result_status=result_status,
                generated_by=actor_user_id,
            )
            db.add(report_card)
            db.flush()

        existing_subject_rows = {
            item.subject_id: item
            for item in db.query(AssessmentReportCardSubject).filter(
                AssessmentReportCardSubject.report_card_id == report_card.id
            )
        }

        for row in subject_rows:
            existing_subject = existing_subject_rows.get(row["subject_id"])
            if existing_subject:
                existing_subject.subject_max_marks = row["subject_max_marks"]
                existing_subject.subject_obtained = row["subject_obtained"]
                existing_subject.subject_percentage = row["subject_percentage"]
                existing_subject.grade_label = row["grade_label"]
                existing_subject.grade_point = row["grade_point"]
                existing_subject.result_status = row["result_status"]
                existing_subject.absent_in_any_exam = row["absent_in_any_exam"]
            else:
                db.add(
                    AssessmentReportCardSubject(
                        report_card_id=report_card.id,
                        **row,
                    )
                )

        generated_count += 1

    db.commit()

    logger.info(
        "report_cards_generated",
        extra={
            "event": "report_cards_generated",
            "generated_count": generated_count,
            "academic_year_id": payload.academic_year_id,
            "academic_term_id": payload.academic_term_id,
            "actor_user_id": actor_user_id,
        },
    )

    return generated_count


def publish_report_cards(db: Session, payload: PublishReportCardsPayload):
    query = db.query(AssessmentReportCard).filter(AssessmentReportCard.publish_status != "LOCKED")

    if payload.report_card_ids:
        query = query.filter(AssessmentReportCard.id.in_(payload.report_card_ids))
    else:
        if payload.academic_year_id is not None:
            query = query.filter(AssessmentReportCard.academic_year_id == payload.academic_year_id)
        if payload.academic_term_id is not None:
            query = query.filter(AssessmentReportCard.academic_term_id == payload.academic_term_id)
        if payload.class_section_id is not None:
            query = query.filter(AssessmentReportCard.class_section_id == payload.class_section_id)
        if payload.report_type is not None:
            query = query.filter(AssessmentReportCard.report_type == payload.report_type.value)

    rows = query.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No report cards found for publish")

    now = datetime.now(timezone.utc)
    for row in rows:
        row.publish_status = "PUBLISHED"
        row.published_at = now

    db.commit()
    return len(rows)


def get_student_report_cards(db: Session, student_id: str, page: int, page_size: int):
    query = db.query(AssessmentReportCard).filter(AssessmentReportCard.student_id == student_id).order_by(
        AssessmentReportCard.generated_at.desc()
    )
    total = query.count()
    report_cards = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for report in report_cards:
        subjects = db.query(AssessmentReportCardSubject).filter(
            AssessmentReportCardSubject.report_card_id == report.id
        ).all()

        row = {
            "id": report.id,
            "student_id": report.student_id,
            "academic_year_id": report.academic_year_id,
            "academic_term_id": report.academic_term_id,
            "class_section_id": report.class_section_id,
            "report_type": report.report_type,
            "publish_status": report.publish_status,
            "total_max_marks": report.total_max_marks,
            "total_obtained": report.total_obtained,
            "percentage": report.percentage,
            "overall_grade": report.overall_grade,
            "overall_grade_point": report.overall_grade_point,
            "result_status": report.result_status,
            "rank_in_class": report.rank_in_class,
            "attendance_percent": report.attendance_percent,
            "generated_at": report.generated_at,
            "published_at": report.published_at,
            "subjects": [
                {
                    "subject_id": s.subject_id,
                    "subject_max_marks": s.subject_max_marks,
                    "subject_obtained": s.subject_obtained,
                    "subject_percentage": s.subject_percentage,
                    "grade_label": s.grade_label,
                    "grade_point": s.grade_point,
                    "result_status": s.result_status,
                    "absent_in_any_exam": s.absent_in_any_exam,
                }
                for s in subjects
            ],
        }
        result.append(row)

    return total, result


def list_exam_history(db: Session, student_id: str, page: int, page_size: int):
    query = db.query(AssessmentStudentExamHistory).filter(
        AssessmentStudentExamHistory.student_id == student_id
    ).order_by(AssessmentStudentExamHistory.exam_created_at.desc())

    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records


def list_academic_history(db: Session, student_id: str, page: int, page_size: int):
    query = db.query(AssessmentStudentAcademicHistory).filter(
        AssessmentStudentAcademicHistory.student_id == student_id
    ).order_by(AssessmentStudentAcademicHistory.generated_at.desc())

    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records


def create_component_weight(db: Session, data: ComponentWeightCreate, actor_user_id: str):
    _ensure_year_exists(db, data.academic_year_id)
    _ensure_class_section_exists(db, data.class_section_id)

    if not db.get(Subject, data.subject_id):
        raise HTTPException(status_code=404, detail="Subject not found")

    if data.academic_term_id is not None:
        _ensure_term_belongs_to_year(db, data.academic_term_id, data.academic_year_id)

    component = db.query(AssessmentComponent).filter(
        AssessmentComponent.component_code == data.component_code.upper(),
        AssessmentComponent.is_active.is_(True),
    ).first()
    if not component:
        raise HTTPException(status_code=404, detail="Assessment component not found")

    model = AssessmentSubjectComponentWeight(
        academic_year_id=data.academic_year_id,
        academic_term_id=data.academic_term_id,
        class_section_id=data.class_section_id,
        subject_id=data.subject_id,
        component_id=component.id,
        weight_percent=data.weight_percent,
        created_by=actor_user_id,
    )
    try:
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Component weight conflict") from exc


def list_component_weights(db: Session, page: int, page_size: int, academic_year_id: int | None):
    query = db.query(AssessmentSubjectComponentWeight)
    if academic_year_id is not None:
        query = query.filter(AssessmentSubjectComponentWeight.academic_year_id == academic_year_id)
    query = query.order_by(AssessmentSubjectComponentWeight.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, rows


def create_assignment(db: Session, data: AssignmentCreate, actor_user_id: str):
    _ensure_year_exists(db, data.academic_year_id)
    _ensure_class_section_exists(db, data.class_section_id)

    if data.academic_term_id is not None:
        _ensure_term_belongs_to_year(db, data.academic_term_id, data.academic_year_id)

    if not db.get(Subject, data.subject_id):
        raise HTTPException(status_code=404, detail="Subject not found")

    if not db.get(Teacher, data.assigned_by_teacher_id):
        raise HTTPException(status_code=404, detail="Teacher not found")

    assignment = AssessmentAssignment(
        **data.model_dump(exclude={"grading_rubric_json"}),
        grading_rubric_json=json.dumps(data.grading_rubric_json) if data.grading_rubric_json else None,
        created_by=actor_user_id,
        status="DRAFT",
    )
    try:
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Assignment conflict") from exc


def list_assignments(
    db: Session,
    page: int,
    page_size: int,
    academic_year_id: int | None,
    class_section_id: int | None,
    subject_id: int | None,
):
    query = db.query(AssessmentAssignment)
    if academic_year_id is not None:
        query = query.filter(AssessmentAssignment.academic_year_id == academic_year_id)
    if class_section_id is not None:
        query = query.filter(AssessmentAssignment.class_section_id == class_section_id)
    if subject_id is not None:
        query = query.filter(AssessmentAssignment.subject_id == subject_id)

    query = query.order_by(AssessmentAssignment.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, rows


def get_assignment(db: Session, assignment_id: int):
    assignment = db.get(AssessmentAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


def update_assignment(db: Session, assignment_id: int, data: AssignmentUpdate):
    assignment = get_assignment(db, assignment_id)
    if assignment.status in {"CLOSED", "CANCELLED", "ARCHIVED"}:
        raise HTTPException(status_code=400, detail="Assignment cannot be updated in current status")

    updates = data.model_dump(exclude_unset=True)
    if "grading_rubric_json" in updates:
        updates["grading_rubric_json"] = (
            json.dumps(updates["grading_rubric_json"])
            if updates["grading_rubric_json"] is not None
            else None
        )

    if "due_date" in updates and updates["due_date"] < assignment.assigned_date:
        raise HTTPException(status_code=400, detail="due_date must be on or after assigned_date")

    if "pass_marks" in updates and updates["pass_marks"] is not None and updates["pass_marks"] > assignment.max_marks:
        raise HTTPException(status_code=400, detail="pass_marks cannot exceed max_marks")

    for key, value in updates.items():
        setattr(assignment, key, value)

    db.commit()
    db.refresh(assignment)
    return assignment


def publish_assignment(db: Session, assignment_id: int):
    assignment = get_assignment(db, assignment_id)
    if assignment.status in {"CANCELLED", "ARCHIVED"}:
        raise HTTPException(status_code=400, detail="Cannot publish cancelled or archived assignment")
    assignment.status = "PUBLISHED"
    assignment.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assignment)
    return assignment


def close_assignment(db: Session, assignment_id: int):
    assignment = get_assignment(db, assignment_id)
    if assignment.status in {"CANCELLED", "ARCHIVED"}:
        raise HTTPException(status_code=400, detail="Cannot close cancelled or archived assignment")
    assignment.status = "CLOSED"
    assignment.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assignment)
    return assignment


def cancel_assignment(db: Session, assignment_id: int):
    assignment = get_assignment(db, assignment_id)
    if assignment.status == "CLOSED":
        raise HTTPException(status_code=400, detail="Closed assignment cannot be cancelled")
    assignment.status = "CANCELLED"
    db.commit()
    db.refresh(assignment)
    return assignment


def submit_assignment(db: Session, assignment_id: int, student_id: str, payload: AssignmentSubmissionCreate):
    assignment = get_assignment(db, assignment_id)
    if assignment.status != "PUBLISHED":
        raise HTTPException(status_code=400, detail="Assignment is not open for submissions")

    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    prev = db.query(AssessmentAssignmentSubmission).filter(
        AssessmentAssignmentSubmission.assignment_id == assignment_id,
        AssessmentAssignmentSubmission.student_id == student_id,
        AssessmentAssignmentSubmission.is_latest.is_(True),
    ).first()

    attempt_no = 1
    if prev:
        prev.is_latest = False
        attempt_no = prev.attempt_no + 1

    now_utc = datetime.now(timezone.utc)
    status = "SUBMITTED"
    if now_utc.date() > assignment.due_date:
        status = "LATE_SUBMITTED"

    submission = AssessmentAssignmentSubmission(
        assignment_id=assignment_id,
        student_id=student_id,
        attempt_no=attempt_no,
        is_latest=True,
        submission_status=status,
        submitted_at=now_utc,
        submission_text=payload.submission_text,
        attachment_url=payload.attachment_url,
        word_count=payload.word_count,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def bulk_upload_assignment_marks(db: Session, payload: AssignmentBulkMarksPayload, actor_user: dict):
    assignment = db.get(AssessmentAssignment, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if actor_user["role"] == "TEACHER":
        teacher_id = get_teacher_id_for_user(db, actor_user["user_id"])
        if not teacher_id or teacher_id != assignment.assigned_by_teacher_id:
            raise HTTPException(status_code=403, detail="Only assignment owner can upload marks")

    try:
        db.execute(
            text(
                "SELECT public.assessment_bulk_upsert_assignment_marks(:assignment_id, CAST(:rows AS jsonb), :actor_user_id)"
            ),
            {
                "assignment_id": payload.assignment_id,
                "rows": json.dumps([r.model_dump() for r in payload.rows]),
                "actor_user_id": actor_user["user_id"],
            },
        )
        db.commit()
        return len(payload.rows)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Bulk assignment marks upload failed: {exc}") from exc


def verify_assignment_marks(db: Session, submission_id: int, actor_user_id: str, feedback: str | None):
    mark = db.query(AssessmentAssignmentMark).filter(AssessmentAssignmentMark.submission_id == submission_id).first()
    if not mark:
        raise HTTPException(status_code=404, detail="Assignment marks not found for submission")

    if mark.marking_status == "LOCKED":
        raise HTTPException(status_code=400, detail="Locked assignment marks cannot be verified")

    mark.marking_status = "VERIFIED"
    mark.verified_by = actor_user_id
    mark.verified_at = datetime.now(timezone.utc)
    if feedback:
        mark.feedback = feedback
    db.commit()
    db.refresh(mark)
    return mark


def list_assignment_history(db: Session, student_id: str, page: int, page_size: int):
    query = db.query(AssessmentStudentAssignmentHistory).filter(
        AssessmentStudentAssignmentHistory.student_id == student_id
    ).order_by(AssessmentStudentAssignmentHistory.assignment_id.desc())
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, records
