from sqlalchemy import (
    BIGINT,
    BOOLEAN,
    DATE,
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True)
    is_current = Column(Boolean)


class AcademicTerm(Base):
    __tablename__ = "academic_terms"

    id = Column(Integer, primary_key=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    term_number = Column(Integer)
    term_name = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    is_current = Column(Boolean)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)


class Class(Base):
    __tablename__ = "classes"

    class_id = Column(Integer, primary_key=True)


class ClassSection(Base):
    __tablename__ = "class_sections"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.class_id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=True)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    subject_name = Column(String(100), nullable=False)
    subject_code = Column(String(20), nullable=False)


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.class_id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String(20), primary_key=True)


class StudentSubjectEnrollment(Base):
    __tablename__ = "student_subject_enrollments"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False)


class AssessmentGradeScale(Base):
    __tablename__ = "assessment_grade_scales"

    id = Column(Integer, primary_key=True)
    scale_name = Column(String(100), nullable=False)
    description = Column(Text)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"))
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"))
    is_default = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    grade_bands = relationship("AssessmentGradeBand", back_populates="grade_scale", cascade="all, delete-orphan")


class AssessmentGradeBand(Base):
    __tablename__ = "assessment_grade_bands"

    id = Column(Integer, primary_key=True)
    grade_scale_id = Column(Integer, ForeignKey("assessment_grade_scales.id", ondelete="CASCADE"), nullable=False)
    grade_label = Column(String(10), nullable=False)
    min_percent = Column(Numeric(5, 2), nullable=False)
    max_percent = Column(Numeric(5, 2), nullable=False)
    grade_point = Column(Numeric(4, 2))
    is_fail = Column(Boolean, nullable=False, default=False)
    remarks = Column(String(200))
    sort_order = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    grade_scale = relationship("AssessmentGradeScale", back_populates="grade_bands")


class AssessmentExam(Base):
    __tablename__ = "assessment_exams"

    id = Column(BigInteger, primary_key=True)
    exam_code = Column(String(40), unique=True)
    exam_name = Column(String(120), nullable=False)
    exam_type = Column(String(30), nullable=False)
    exam_group = Column(String(30), nullable=False, default="REGULAR")
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="RESTRICT"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="RESTRICT"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    grade_scale_id = Column(Integer, ForeignKey("assessment_grade_scales.id", ondelete="SET NULL"))
    created_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    approved_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    published_at = Column(TIMESTAMP)
    remarks = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentExamSubject(Base):
    __tablename__ = "assessment_exam_subjects"

    id = Column(BigInteger, primary_key=True)
    exam_id = Column(BigInteger, ForeignKey("assessment_exams.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False)
    max_marks = Column(Numeric(6, 2), nullable=False)
    pass_marks = Column(Numeric(6, 2))
    weightage_percent = Column(Numeric(5, 2))
    assessment_mode = Column(String(20), nullable=False, default="THEORY")
    evaluator_teacher_id = Column(String(20), ForeignKey("teachers.id", ondelete="SET NULL"))
    grade_scale_id = Column(Integer, ForeignKey("assessment_grade_scales.id", ondelete="SET NULL"))
    instructions = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("exam_id", "subject_id", name="uq_assessment_exam_subject"),
    )


class AssessmentExamRegistration(Base):
    __tablename__ = "assessment_exam_registrations"

    id = Column(BigInteger, primary_key=True)
    exam_subject_id = Column(BigInteger, ForeignKey("assessment_exam_subjects.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(20), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("student_subject_enrollments.id", ondelete="SET NULL"))
    attendance_status = Column(String(20), nullable=False, default="PRESENT")
    hall_ticket_no = Column(String(50))
    seat_no = Column(String(30))
    remarks = Column(Text)
    registered_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("exam_subject_id", "student_id", name="uq_assessment_registration"),
    )


class AssessmentMark(Base):
    __tablename__ = "assessment_marks"

    id = Column(BigInteger, primary_key=True)
    registration_id = Column(BigInteger, ForeignKey("assessment_exam_registrations.id", ondelete="CASCADE"), nullable=False, unique=True)
    raw_marks = Column(Numeric(6, 2))
    grace_marks = Column(Numeric(6, 2), nullable=False, default=0)
    final_marks = Column(Numeric(6, 2))
    percentage = Column(Numeric(6, 2))
    grade_band_id = Column(Integer, ForeignKey("assessment_grade_bands.id", ondelete="SET NULL"))
    grade_label = Column(String(10))
    is_pass = Column(Boolean)
    entry_status = Column(String(20), nullable=False, default="DRAFT")
    submitted_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    verified_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    submitted_at = Column(TIMESTAMP)
    verified_at = Column(TIMESTAMP)
    remarks = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentReportCard(Base):
    __tablename__ = "assessment_report_cards"

    id = Column(BigInteger, primary_key=True)
    student_id = Column(String(20), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="RESTRICT"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="SET NULL"))
    report_type = Column(String(20), nullable=False)
    publish_status = Column(String(20), nullable=False, default="DRAFT")
    total_max_marks = Column(Numeric(10, 2))
    total_obtained = Column(Numeric(10, 2))
    percentage = Column(Numeric(6, 2))
    overall_grade = Column(String(10))
    overall_grade_point = Column(Numeric(4, 2))
    result_status = Column(String(20))
    rank_in_class = Column(Integer)
    attendance_percent = Column(Numeric(5, 2))
    teacher_remarks = Column(Text)
    principal_remarks = Column(Text)
    generated_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    generated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    published_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentReportCardSubject(Base):
    __tablename__ = "assessment_report_card_subjects"

    id = Column(BigInteger, primary_key=True)
    report_card_id = Column(BigInteger, ForeignKey("assessment_report_cards.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False)
    subject_max_marks = Column(Numeric(8, 2))
    subject_obtained = Column(Numeric(8, 2))
    subject_percentage = Column(Numeric(6, 2))
    grade_label = Column(String(10))
    grade_point = Column(Numeric(4, 2))
    result_status = Column(String(20))
    absent_in_any_exam = Column(Boolean, nullable=False, default=False)
    teacher_remark = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("report_card_id", "subject_id", name="uq_assessment_report_subject"),
    )


class AssessmentStudentExamHistory(Base):
    __tablename__ = "vw_assessment_student_exam_history"

    student_id = Column(String(20), primary_key=True)
    exam_id = Column(BigInteger, primary_key=True)
    subject_id = Column(Integer, primary_key=True)
    academic_year_id = Column(Integer)
    academic_term_id = Column(Integer)
    class_section_id = Column(Integer)
    exam_name = Column(String(120))
    exam_type = Column(String(30))
    exam_group = Column(String(30))
    exam_status = Column(String(20))
    subject_name = Column(String(100))
    subject_code = Column(String(20))
    attendance_status = Column(String(20))
    raw_marks = Column(Numeric(6, 2))
    grace_marks = Column(Numeric(6, 2))
    final_marks = Column(Numeric(6, 2))
    percentage = Column(Numeric(6, 2))
    grade_label = Column(String(10))
    is_pass = Column(Boolean)
    entry_status = Column(String(20))
    start_date = Column(Date)
    end_date = Column(Date)
    exam_created_at = Column(TIMESTAMP)


class AssessmentStudentAcademicHistory(Base):
    __tablename__ = "vw_assessment_student_academic_history"

    student_id = Column(String(20), primary_key=True)
    academic_year_id = Column(Integer, primary_key=True)
    report_type = Column(String(20), primary_key=True)
    academic_term_id = Column(Integer, primary_key=True, nullable=True)
    publish_status = Column(String(20))
    total_max_marks = Column(Numeric(10, 2))
    total_obtained = Column(Numeric(10, 2))
    percentage = Column(Numeric(6, 2))
    overall_grade = Column(String(10))
    overall_grade_point = Column(Numeric(4, 2))
    result_status = Column(String(20))
    rank_in_class = Column(Integer)
    attendance_percent = Column(Numeric(5, 2))
    generated_at = Column(TIMESTAMP)
    published_at = Column(TIMESTAMP)


class AssessmentComponent(Base):
    __tablename__ = "assessment_components"

    id = Column(Integer, primary_key=True)
    component_code = Column(String(30), nullable=False, unique=True)
    component_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentSubjectComponentWeight(Base):
    __tablename__ = "assessment_subject_component_weights"

    id = Column(BigInteger, primary_key=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="CASCADE"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(Integer, ForeignKey("assessment_components.id", ondelete="RESTRICT"), nullable=False)
    weight_percent = Column(Numeric(5, 2), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentAssignment(Base):
    __tablename__ = "assessment_assignments"

    id = Column(BigInteger, primary_key=True)
    assignment_code = Column(String(50), unique=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False)
    academic_term_id = Column(Integer, ForeignKey("academic_terms.id", ondelete="RESTRICT"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id", ondelete="RESTRICT"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False)
    assigned_by_teacher_id = Column(String(20), ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False)
    assigned_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    allow_late_submission = Column(Boolean, nullable=False, default=False)
    late_until = Column(Date)
    max_marks = Column(Numeric(6, 2), nullable=False)
    pass_marks = Column(Numeric(6, 2))
    grading_rubric_json = Column(Text)
    attachment_url = Column(Text)
    status = Column(String(20), nullable=False, default="DRAFT")
    created_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    published_at = Column(TIMESTAMP)
    closed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentAssignmentStudentOverride(Base):
    __tablename__ = "assessment_assignment_student_overrides"

    id = Column(BigInteger, primary_key=True)
    assignment_id = Column(BigInteger, ForeignKey("assessment_assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(20), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    extended_due_date = Column(Date)
    is_excused = Column(Boolean, nullable=False, default=False)
    excuse_reason = Column(Text)
    approved_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentAssignmentSubmission(Base):
    __tablename__ = "assessment_assignment_submissions"

    id = Column(BigInteger, primary_key=True)
    assignment_id = Column(BigInteger, ForeignKey("assessment_assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(20), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("student_subject_enrollments.id", ondelete="SET NULL"))
    attempt_no = Column(Integer, nullable=False, default=1)
    is_latest = Column(Boolean, nullable=False, default=True)
    submission_status = Column(String(25), nullable=False, default="NOT_SUBMITTED")
    submitted_at = Column(TIMESTAMP)
    submission_text = Column(Text)
    attachment_url = Column(Text)
    word_count = Column(Integer)
    plagiarism_score = Column(Numeric(5, 2))
    plagiarism_flag = Column(Boolean, nullable=False, default=False)
    teacher_feedback = Column(Text)
    teacher_remarks = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentAssignmentMark(Base):
    __tablename__ = "assessment_assignment_marks"

    id = Column(BigInteger, primary_key=True)
    submission_id = Column(
        BigInteger,
        ForeignKey("assessment_assignment_submissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    raw_marks = Column(Numeric(6, 2))
    grace_marks = Column(Numeric(6, 2), nullable=False, default=0)
    final_marks = Column(Numeric(6, 2))
    percentage = Column(Numeric(6, 2))
    grade_band_id = Column(Integer, ForeignKey("assessment_grade_bands.id", ondelete="SET NULL"))
    grade_label = Column(String(10))
    is_pass = Column(Boolean)
    marking_status = Column(String(20), nullable=False, default="DRAFT")
    evaluated_by = Column(String(20), ForeignKey("teachers.id", ondelete="SET NULL"))
    evaluated_at = Column(TIMESTAMP)
    verified_by = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    verified_at = Column(TIMESTAMP)
    feedback = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class AssessmentStudentAssignmentHistory(Base):
    __tablename__ = "vw_assessment_student_assignment_history"

    student_id = Column(String(20), primary_key=True)
    assignment_id = Column(BigInteger, primary_key=True)
    attempt_no = Column(Integer, primary_key=True)
    assignment_code = Column(String(50))
    title = Column(String(200))
    academic_year_id = Column(Integer)
    academic_term_id = Column(Integer)
    class_section_id = Column(Integer)
    subject_id = Column(Integer)
    subject_name = Column(String(100))
    subject_code = Column(String(20))
    assigned_date = Column(Date)
    due_date = Column(Date)
    assignment_status = Column(String(20))
    submission_status = Column(String(25))
    submitted_at = Column(TIMESTAMP)
    raw_marks = Column(Numeric(6, 2))
    grace_marks = Column(Numeric(6, 2))
    final_marks = Column(Numeric(6, 2))
    percentage = Column(Numeric(6, 2))
    grade_label = Column(String(10))
    is_pass = Column(Boolean)
    marking_status = Column(String(20))
    evaluated_at = Column(TIMESTAMP)
    verified_at = Column(TIMESTAMP)
