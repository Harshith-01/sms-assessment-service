from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaginationParams(StrictBase):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class PagedResponse(BaseModel):
    page: int
    page_size: int
    total: int
    data: list[Any]


class GradeScaleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ExamType(str, Enum):
    UNIT_TEST = "UNIT_TEST"
    MIDTERM = "MIDTERM"
    FINAL = "FINAL"
    PRACTICAL = "PRACTICAL"
    ASSIGNMENT = "ASSIGNMENT"
    QUIZ = "QUIZ"
    PROJECT = "PROJECT"
    OTHER = "OTHER"


class ExamGroup(str, Enum):
    REGULAR = "REGULAR"
    REEXAM = "REEXAM"
    SUPPLEMENTARY = "SUPPLEMENTARY"
    IMPROVEMENT = "IMPROVEMENT"


class ExamStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class AssessmentMode(str, Enum):
    THEORY = "THEORY"
    PRACTICAL = "PRACTICAL"
    COMBINED = "COMBINED"
    PROJECT = "PROJECT"
    VIVA = "VIVA"
    OTHER = "OTHER"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    EXEMPT = "EXEMPT"
    MALPRACTICE = "MALPRACTICE"


class MarksEntryStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    LOCKED = "LOCKED"


class ReportType(str, Enum):
    TERM = "TERM"
    ANNUAL = "ANNUAL"


class ReportPublishStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    LOCKED = "LOCKED"


class AssignmentStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class AssignmentSubmissionStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    LATE_SUBMITTED = "LATE_SUBMITTED"
    EXCUSED = "EXCUSED"
    MISSING = "MISSING"
    PLAGIARIZED = "PLAGIARIZED"


class GradeScaleCreate(StrictBase):
    scale_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    academic_year_id: int | None = None
    department_id: int | None = None
    is_default: bool = False
    status: GradeScaleStatus = GradeScaleStatus.ACTIVE


class GradeScaleUpdate(StrictBase):
    scale_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    academic_year_id: int | None = None
    department_id: int | None = None
    is_default: bool | None = None
    status: GradeScaleStatus | None = None


class GradeScaleOut(BaseModel):
    id: int
    scale_name: str
    description: str | None
    academic_year_id: int | None
    department_id: int | None
    is_default: bool
    status: str

    model_config = ConfigDict(from_attributes=True)


class GradeBandCreate(StrictBase):
    grade_scale_id: int
    grade_label: str = Field(..., min_length=1, max_length=10)
    min_percent: Decimal = Field(..., ge=0, le=100)
    max_percent: Decimal = Field(..., ge=0, le=100)
    grade_point: Decimal | None = Field(default=None, ge=0)
    is_fail: bool = False
    remarks: str | None = Field(default=None, max_length=200)
    sort_order: int = Field(..., ge=1)

    @field_validator("max_percent")
    @classmethod
    def validate_range(cls, max_percent: Decimal, info):
        min_percent = info.data.get("min_percent")
        if min_percent is not None and max_percent < min_percent:
            raise ValueError("max_percent must be greater than or equal to min_percent")
        return max_percent


class GradeBandOut(BaseModel):
    id: int
    grade_scale_id: int
    grade_label: str
    min_percent: Decimal
    max_percent: Decimal
    grade_point: Decimal | None
    is_fail: bool
    remarks: str | None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ExamCreate(StrictBase):
    exam_code: str | None = Field(default=None, max_length=40)
    exam_name: str = Field(..., min_length=2, max_length=120)
    exam_type: ExamType
    exam_group: ExamGroup = ExamGroup.REGULAR
    academic_year_id: int
    academic_term_id: int | None = None
    class_section_id: int
    start_date: date
    end_date: date
    grade_scale_id: int | None = None
    remarks: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be after or equal to start_date")
        return end_date


class ExamUpdate(StrictBase):
    exam_code: str | None = Field(default=None, max_length=40)
    exam_name: str | None = Field(default=None, min_length=2, max_length=120)
    exam_type: ExamType | None = None
    exam_group: ExamGroup | None = None
    academic_year_id: int | None = None
    academic_term_id: int | None = None
    class_section_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    grade_scale_id: int | None = None
    remarks: str | None = None


class ExamOut(BaseModel):
    id: int
    exam_code: str | None
    exam_name: str
    exam_type: str
    exam_group: str
    academic_year_id: int
    academic_term_id: int | None
    class_section_id: int
    start_date: date
    end_date: date
    status: str
    grade_scale_id: int | None

    model_config = ConfigDict(from_attributes=True)


class ExamSubjectCreate(StrictBase):
    exam_id: int
    subject_id: int
    max_marks: Decimal = Field(..., gt=0)
    pass_marks: Decimal | None = Field(default=None, ge=0)
    weightage_percent: Decimal | None = Field(default=None, ge=0, le=100)
    assessment_mode: AssessmentMode = AssessmentMode.THEORY
    evaluator_teacher_id: str | None = Field(default=None, min_length=2, max_length=20)
    grade_scale_id: int | None = None
    instructions: str | None = None

    @field_validator("pass_marks")
    @classmethod
    def pass_marks_le_max(cls, pass_marks: Decimal | None, info):
        max_marks = info.data.get("max_marks")
        if pass_marks is not None and max_marks is not None and pass_marks > max_marks:
            raise ValueError("pass_marks cannot be greater than max_marks")
        return pass_marks


class ExamSubjectOut(BaseModel):
    id: int
    exam_id: int
    subject_id: int
    max_marks: Decimal
    pass_marks: Decimal | None
    weightage_percent: Decimal | None
    assessment_mode: str
    evaluator_teacher_id: str | None
    grade_scale_id: int | None

    model_config = ConfigDict(from_attributes=True)


class RegisterStudentsPayload(StrictBase):
    exam_subject_id: int
    student_ids: list[str] = Field(..., min_length=1)


class BulkMarkRow(StrictBase):
    student_id: str = Field(..., min_length=2, max_length=20)
    attendance_status: AttendanceStatus = AttendanceStatus.PRESENT
    raw_marks: Decimal | None = Field(default=None, ge=0)
    grace_marks: Decimal | None = Field(default=0, ge=0)
    remarks: str | None = None


class BulkMarksPayload(StrictBase):
    exam_subject_id: int
    rows: list[BulkMarkRow] = Field(..., min_length=1)


class VerifyMarkPayload(StrictBase):
    remarks: str | None = None


class GenerateReportCardsPayload(StrictBase):
    academic_year_id: int
    academic_term_id: int | None = None
    class_section_id: int | None = None
    report_type: ReportType = ReportType.TERM
    student_ids: list[str] | None = None


class PublishReportCardsPayload(StrictBase):
    report_card_ids: list[int] | None = None
    academic_year_id: int | None = None
    academic_term_id: int | None = None
    class_section_id: int | None = None
    report_type: ReportType | None = None


class ReportCardSubjectOut(BaseModel):
    subject_id: int
    subject_max_marks: Decimal | None
    subject_obtained: Decimal | None
    subject_percentage: Decimal | None
    grade_label: str | None
    grade_point: Decimal | None
    result_status: str | None
    absent_in_any_exam: bool


class ReportCardOut(BaseModel):
    id: int
    student_id: str
    academic_year_id: int
    academic_term_id: int | None
    class_section_id: int | None
    report_type: str
    publish_status: str
    total_max_marks: Decimal | None
    total_obtained: Decimal | None
    percentage: Decimal | None
    overall_grade: str | None
    overall_grade_point: Decimal | None
    result_status: str | None
    rank_in_class: int | None
    attendance_percent: Decimal | None
    generated_at: datetime
    published_at: datetime | None
    subjects: list[ReportCardSubjectOut] = []


class AssignmentCreate(StrictBase):
    assignment_code: str | None = Field(default=None, max_length=50)
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    academic_year_id: int
    academic_term_id: int | None = None
    class_section_id: int
    subject_id: int
    assigned_by_teacher_id: str = Field(..., min_length=2, max_length=20)
    assigned_date: date
    due_date: date
    allow_late_submission: bool = False
    late_until: date | None = None
    max_marks: Decimal = Field(..., gt=0)
    pass_marks: Decimal | None = Field(default=None, ge=0)
    grading_rubric_json: dict | None = None
    attachment_url: str | None = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, due_date: date, info):
        assigned_date = info.data.get("assigned_date")
        if assigned_date and due_date < assigned_date:
            raise ValueError("due_date must be on or after assigned_date")
        return due_date


class AssignmentUpdate(StrictBase):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    due_date: date | None = None
    allow_late_submission: bool | None = None
    late_until: date | None = None
    pass_marks: Decimal | None = Field(default=None, ge=0)
    grading_rubric_json: dict | None = None
    attachment_url: str | None = None


class AssignmentOut(BaseModel):
    id: int
    assignment_code: str | None
    title: str
    description: str | None
    academic_year_id: int
    academic_term_id: int | None
    class_section_id: int
    subject_id: int
    assigned_by_teacher_id: str
    assigned_date: date
    due_date: date
    allow_late_submission: bool
    late_until: date | None
    max_marks: Decimal
    pass_marks: Decimal | None
    status: str

    model_config = ConfigDict(from_attributes=True)


class AssignmentSubmissionCreate(StrictBase):
    submission_text: str | None = None
    attachment_url: str | None = None
    word_count: int | None = Field(default=None, ge=0)


class AssignmentSubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: str
    attempt_no: int
    is_latest: bool
    submission_status: str
    submitted_at: datetime | None
    submission_text: str | None
    attachment_url: str | None
    word_count: int | None

    model_config = ConfigDict(from_attributes=True)


class AssignmentBulkMarkRow(StrictBase):
    student_id: str = Field(..., min_length=2, max_length=20)
    submission_status: AssignmentSubmissionStatus = AssignmentSubmissionStatus.SUBMITTED
    raw_marks: Decimal | None = Field(default=None, ge=0)
    grace_marks: Decimal | None = Field(default=0, ge=0)
    feedback: str | None = None


class AssignmentBulkMarksPayload(StrictBase):
    assignment_id: int
    rows: list[AssignmentBulkMarkRow] = Field(..., min_length=1)


class VerifyAssignmentMarkPayload(StrictBase):
    feedback: str | None = None


class ComponentWeightCreate(StrictBase):
    academic_year_id: int
    academic_term_id: int | None = None
    class_section_id: int
    subject_id: int
    component_code: str = Field(..., min_length=2, max_length=30)
    weight_percent: Decimal = Field(..., ge=0, le=100)


class ComponentWeightOut(BaseModel):
    id: int
    academic_year_id: int
    academic_term_id: int | None
    class_section_id: int
    subject_id: int
    component_id: int
    weight_percent: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class BulkOperationResponse(BaseModel):
    message: str
    count: int


class StudentHistoryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
