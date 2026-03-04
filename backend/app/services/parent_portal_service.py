"""
Parent Portal Service
Provides parent-facing views for attendance, marks, fees, homework, notifications
"""
from app.models.student import Student
from app.models.attendance import Attendance, AttendanceStatus
from app.models.exams import GradeBook, ExamTerm, ExamSchedule
from app.models.finance import StudentFeeInstallment, FeePayment
from app.models.communication import Homework, HomeworkSubmission, Notice, Event
from app.models.alert import Alert
from app.extensions import db
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ParentPortalService:
    """Service for parent-facing portal"""

    @staticmethod
    def get_student_overview(school_id, student_id):
        """Get student overview for parent dashboard"""
        try:
            student = Student.query.filter_by(school_id=school_id, id=student_id).first()
            if not student:
                return {'success': False, 'error': 'Student not found'}

            # Attendance summary (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).date()
            att_records = Attendance.query.filter(
                Attendance.school_id == school_id,
                Attendance.user_id == student_id,
                Attendance.attendance_date >= thirty_days_ago
            ).all()

            total_att = len(att_records)
            present = sum(1 for a in att_records if a.status == AttendanceStatus.PRESENT)
            att_percentage = round((present / total_att) * 100, 2) if total_att > 0 else 0

            # Fee status
            pending_fees = StudentFeeInstallment.query.filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.student_id == student_id,
                StudentFeeInstallment.is_paid == False
            ).all()

            total_pending = sum(float(f.amount) - float(f.paid_amount) for f in pending_fees)
            overdue_count = sum(1 for f in pending_fees if f.is_overdue())

            # Recent grades
            recent_grades = GradeBook.query.filter_by(
                school_id=school_id, student_id=student_id
            ).order_by(GradeBook.created_at.desc()).limit(10).all()

            return {
                'success': True,
                'data': {
                    'student': student.to_dict(),
                    'attendance': {
                        'percentage': att_percentage,
                        'present_days': present,
                        'total_days': total_att,
                        'period': '30 days'
                    },
                    'fees': {
                        'total_pending': total_pending,
                        'overdue_count': overdue_count,
                        'pending_installments': [f.to_dict() for f in pending_fees]
                    },
                    'recent_grades': [g.to_dict() for g in recent_grades]
                }
            }
        except Exception as e:
            logger.error(f"Student overview error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_attendance_view(school_id, student_id, month=None, year=None):
        """Get detailed attendance for a student"""
        try:
            now = datetime.utcnow()
            if not month:
                month = now.month
            if not year:
                year = now.year

            from calendar import monthrange
            start_date = datetime(year, month, 1).date()
            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day).date()

            records = Attendance.query.filter(
                Attendance.school_id == school_id,
                Attendance.user_id == student_id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date
            ).order_by(Attendance.attendance_date).all()

            total = len(records)
            present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
            absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
            late = sum(1 for r in records if r.status == AttendanceStatus.LATE)

            return {
                'success': True,
                'data': {
                    'month': month,
                    'year': year,
                    'total_days': total,
                    'present': present,
                    'absent': absent,
                    'late': late,
                    'percentage': round((present / total) * 100, 2) if total > 0 else 0,
                    'records': [r.to_dict() for r in records]
                }
            }
        except Exception as e:
            logger.error(f"Attendance view error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_marks_view(school_id, student_id, exam_term_id=None):
        """Get marks/grades for a student"""
        try:
            query = GradeBook.query.filter_by(
                school_id=school_id, student_id=student_id
            )
            if exam_term_id:
                query = query.filter_by(exam_term_id=exam_term_id)

            grades = query.order_by(GradeBook.created_at.desc()).all()

            # Group by exam term
            by_term = {}
            for g in grades:
                term_name = g.exam_term.name if g.exam_term else 'Unknown'
                if term_name not in by_term:
                    by_term[term_name] = []
                by_term[term_name].append(g.to_dict())

            # Overall statistics
            total_marks = sum(g.obtained_marks or 0 for g in grades)
            max_marks = sum(g.max_marks or 0 for g in grades)
            overall_pct = round((total_marks / max_marks) * 100, 2) if max_marks > 0 else 0

            return {
                'success': True,
                'data': {
                    'overall_percentage': overall_pct,
                    'total_subjects': len(grades),
                    'by_term': by_term,
                    'all_grades': [g.to_dict() for g in grades]
                }
            }
        except Exception as e:
            logger.error(f"Marks view error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_fee_status(school_id, student_id):
        """Get fee payment status for a student"""
        try:
            installments = StudentFeeInstallment.query.filter_by(
                school_id=school_id, student_id=student_id
            ).order_by(StudentFeeInstallment.due_date).all()

            payments = FeePayment.query.filter_by(
                school_id=school_id, student_id=student_id
            ).order_by(FeePayment.payment_date.desc()).all()

            total_fee = sum(float(i.amount) for i in installments)
            total_paid = sum(float(i.paid_amount) for i in installments)
            total_outstanding = total_fee - total_paid

            return {
                'success': True,
                'data': {
                    'total_fee': total_fee,
                    'total_paid': total_paid,
                    'outstanding': total_outstanding,
                    'installments': [i.to_dict() for i in installments],
                    'payment_history': [p.to_dict() for p in payments]
                }
            }
        except Exception as e:
            logger.error(f"Fee status error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_homework_view(school_id, student_id, class_id=None):
        """Get homework assignments for a student"""
        try:
            student = Student.query.filter_by(school_id=school_id, id=student_id).first()
            if not student:
                return {'success': False, 'error': 'Student not found'}

            query = Homework.query.filter_by(school_id=school_id)

            # Filter by class if available
            if class_id:
                query = query.filter_by(class_id=class_id)

            homeworks = query.order_by(Homework.due_date.desc()).limit(50).all()

            # Check submissions
            result = []
            for hw in homeworks:
                submission = HomeworkSubmission.query.filter_by(
                    homework_id=hw.id, student_id=student_id
                ).first()

                hw_data = hw.to_dict()
                hw_data['submitted'] = submission is not None
                hw_data['submission'] = submission.to_dict() if submission else None
                hw_data['is_overdue'] = not submission and hw.due_date < datetime.utcnow().date()
                result.append(hw_data)

            return {
                'success': True,
                'data': {
                    'total_homework': len(result),
                    'submitted': sum(1 for r in result if r['submitted']),
                    'pending': sum(1 for r in result if not r['submitted'] and not r['is_overdue']),
                    'overdue': sum(1 for r in result if r['is_overdue']),
                    'homework': result
                }
            }
        except Exception as e:
            logger.error(f"Homework view error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_notifications(school_id, student_id=None, page=1, per_page=20):
        """Get notifications/notices relevant to a parent"""
        try:
            # Get notices
            notices = Notice.query.filter(
                Notice.school_id == school_id,
                Notice.is_active == True
            ).order_by(Notice.published_date.desc()).limit(per_page).all()

            # Get alerts for this student
            alerts = []
            if student_id:
                alerts = Alert.query.filter(
                    Alert.school_id == school_id,
                    Alert.target_user_id == student_id,
                    Alert.is_dismissed == False
                ).order_by(Alert.created_at.desc()).limit(20).all()

            # Upcoming events
            events = Event.query.filter(
                Event.school_id == school_id,
                Event.event_date >= datetime.utcnow().date(),
                Event.is_public == True
            ).order_by(Event.event_date).limit(10).all()

            return {
                'success': True,
                'data': {
                    'notices': [n.to_dict() for n in notices],
                    'alerts': [a.to_dict() for a in alerts],
                    'upcoming_events': [e.to_dict() for e in events]
                }
            }
        except Exception as e:
            logger.error(f"Notifications view error: {str(e)}")
            return {'success': False, 'error': str(e)}
