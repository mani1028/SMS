"""
Performance Indexes for SMS Multi-Tenant Platform
==================================================
High-impact indexes targeting tenant isolation (school_id), common filtering
patterns (status, is_active, dates), and frequent JOIN/WHERE column combos.

These are ADDITIVE — they do NOT duplicate indexes already defined in model
__table_args__ (e.g. enquiry, billing, expense, activity, parent, etc.).

Usage:
    from app.models.indexes import create_indexes
    create_indexes(db)
"""

from sqlalchemy import Index

# ---------------------------------------------------------------------------
# Import every model whose table we reference.  The import ensures the table
# metadata is registered before we create Index objects against it.
# ---------------------------------------------------------------------------
from app.models.student import Student, AcademicHistory, StudentDocument
from app.models.user import User
from app.models.staff import Staff, StaffAttendance, StaffSalary, LeaveRequest as StaffLeaveRequest
from app.models.attendance import Attendance, LeaveRequest, StaffCheckInOut
from app.models.academics import Subject, Class, Section, ClassTeacherAssignment, TimetableSlot
from app.models.finance import (
    FeeStructure, FeeComponent, FeePlan, StudentFeeInstallment, FeePayment, Scholarship,
)
from app.models.billing import Plan, Subscription, Billing, SchoolUsage
from app.models.exams import ExamTerm, ExamSchedule, GradingScale, GradeBook, StudentRank
from app.models.communication import (
    Notice, NoticeView, Event, Homework, HomeworkSubmission, Announcement, Document,
)
from app.models.enquiry import Enquiry, FollowUp, EnquiryDocument
from app.models.logistics import (
    Vehicle, Route, RouteStop, StudentTransportAllocation, GPSLog,
    Book, BookIssue, HostelRoom, HostelAllocation, LabInventory,
)
from app.models.parent import Parent, ParentStudent, EmergencyContact, CommunicationHistory
from app.models.activity import Activity
from app.models.permission import Permission
from app.models.role import Role
from app.models.school import School
from app.models.settings import AcademicYear, SchoolConfiguration, AuditLog, SystemLog
from app.models.expense import Expense, ExpenseCategory, SalaryStructure, SalaryPayment


# ---------------------------------------------------------------------------
# PERFORMANCE_INDEXES — 22 high-impact indexes
# ---------------------------------------------------------------------------
PERFORMANCE_INDEXES = [

    # ── 1. Students: tenant-scoped active listing & class filter ──────────
    Index(
        'idx_student_school_status',
        Student.__table__.c.school_id,
        Student.__table__.c.status,
    ),
    Index(
        'idx_student_school_class',
        Student.__table__.c.school_id,
        Student.__table__.c.class_name,
        Student.__table__.c.section,
    ),

    # ── 2. Users: login lookups & role-based access ──────────────────────
    Index(
        'idx_user_school_active',
        User.__table__.c.school_id,
        User.__table__.c.is_active,
    ),
    Index(
        'idx_user_school_role',
        User.__table__.c.school_id,
        User.__table__.c.role_id,
    ),

    # ── 3. Attendance: daily mark/view is the single hottest query ───────
    Index(
        'idx_attendance_school_date',
        Attendance.__table__.c.school_id,
        Attendance.__table__.c.attendance_date,
    ),
    Index(
        'idx_attendance_user_date',
        Attendance.__table__.c.school_id,
        Attendance.__table__.c.user_id,
        Attendance.__table__.c.attendance_date,
    ),

    # ── 4. Staff: department-wise listing ────────────────────────────────
    Index(
        'idx_staff_school_dept',
        Staff.__table__.c.school_id,
        Staff.__table__.c.department,
    ),

    # ── 5. Staff attendance: daily view ──────────────────────────────────
    Index(
        'idx_staff_att_school_date',
        StaffAttendance.__table__.c.school_id,
        StaffAttendance.__table__.c.date,
    ),

    # ── 6. Leave requests: pending approval queue ────────────────────────
    Index(
        'idx_leave_school_status',
        LeaveRequest.__table__.c.school_id,
        LeaveRequest.__table__.c.status,
    ),

    # ── 7. Fee payments: student payment history & status ────────────────
    Index(
        'idx_feepay_school_student',
        FeePayment.__table__.c.school_id,
        FeePayment.__table__.c.student_id,
    ),
    Index(
        'idx_feepay_school_status',
        FeePayment.__table__.c.school_id,
        FeePayment.__table__.c.status,
    ),

    # ── 8. Fee installments: outstanding/overdue queries ─────────────────
    Index(
        'idx_installment_school_student_paid',
        StudentFeeInstallment.__table__.c.school_id,
        StudentFeeInstallment.__table__.c.student_id,
        StudentFeeInstallment.__table__.c.is_paid,
    ),
    Index(
        'idx_installment_due_date',
        StudentFeeInstallment.__table__.c.school_id,
        StudentFeeInstallment.__table__.c.due_date,
        StudentFeeInstallment.__table__.c.is_paid,
    ),

    # ── 9. Grade books: student result lookup ────────────────────────────
    Index(
        'idx_gradebook_school_student',
        GradeBook.__table__.c.school_id,
        GradeBook.__table__.c.student_id,
    ),
    Index(
        'idx_gradebook_school_exam',
        GradeBook.__table__.c.school_id,
        GradeBook.__table__.c.exam_term_id,
        GradeBook.__table__.c.subject_id,
    ),

    # ── 10. Exam schedules: term-wise listing ────────────────────────────
    Index(
        'idx_examschedule_school_term',
        ExamSchedule.__table__.c.school_id,
        ExamSchedule.__table__.c.exam_term_id,
    ),

    # ── 11. Notices: active notice board ─────────────────────────────────
    Index(
        'idx_notice_school_active',
        Notice.__table__.c.school_id,
        Notice.__table__.c.is_active,
        Notice.__table__.c.published_date,
    ),

    # ── 12. Homework: class-wise homework listing ────────────────────────
    Index(
        'idx_homework_school_class',
        Homework.__table__.c.school_id,
        Homework.__table__.c.class_id,
        Homework.__table__.c.section_id,
    ),

    # ── 13. Timetable: class section schedule ────────────────────────────
    Index(
        'idx_timetable_school_class_section',
        TimetableSlot.__table__.c.school_id,
        TimetableSlot.__table__.c.class_id,
        TimetableSlot.__table__.c.section_id,
    ),

    # ── 14. Sections: class drill-down ───────────────────────────────────
    Index(
        'idx_section_school_class',
        Section.__table__.c.school_id,
        Section.__table__.c.class_id,
    ),

    # ── 15. Book issues: current checkouts per user ──────────────────────
    Index(
        'idx_bookissue_school_user_returned',
        BookIssue.__table__.c.school_id,
        BookIssue.__table__.c.user_id,
        BookIssue.__table__.c.is_returned,
    ),

    # ── 16. Audit logs: time-based audit trail ───────────────────────────
    Index(
        'idx_auditlog_school_timestamp',
        AuditLog.__table__.c.school_id,
        AuditLog.__table__.c.timestamp,
    ),

    # ── 17. Events: upcoming events calendar ─────────────────────────────
    Index(
        'idx_event_school_date',
        Event.__table__.c.school_id,
        Event.__table__.c.event_date,
    ),
]


def create_indexes(db):
    """
    Create all performance indexes that don't already exist.

    Safe to call repeatedly — each index is created with IF NOT EXISTS
    semantics via SQLAlchemy's ``create()`` with ``checkfirst=True``.

    Parameters
    ----------
    db : flask_sqlalchemy.SQLAlchemy
        The initialised SQLAlchemy extension instance.
    """
    bind = db.engine
    for idx in PERFORMANCE_INDEXES:
        try:
            idx.create(bind=bind, checkfirst=True)
        except Exception as exc:
            # Log but don't crash — an index that already exists or has a
            # name collision should not prevent the app from starting.
            import logging
            logging.getLogger(__name__).warning(
                'Could not create index %s: %s', idx.name, exc,
            )
