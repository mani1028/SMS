"""
Analytics Service
Student performance analytics, admission funnel, advanced dashboards
"""
from app.extensions import db
from app.models.student import Student
from app.models.exams import GradeBook, ExamTerm, ExamSchedule, StudentRank
from app.models.attendance import Attendance, AttendanceStatus
from app.models.academics import Class, Section, Subject, ClassTeacherAssignment
from app.models.enquiry import Enquiry
from app.models.finance import FeePayment, StudentFeeInstallment
from app.models.user import User
from sqlalchemy import func, and_, case, distinct
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Student performance analytics and advanced dashboards"""

    # ==================== STUDENT PERFORMANCE ====================

    @staticmethod
    def get_student_performance(school_id, student_id, academic_year=None):
        """Comprehensive performance analytics for a single student"""
        try:
            query = GradeBook.query.filter_by(school_id=school_id, student_id=student_id)
            if academic_year:
                query = query.join(ExamTerm).filter(ExamTerm.academic_year == academic_year)

            grades = query.all()

            if not grades:
                return {'success': True, 'data': {'message': 'No exam data found'}}

            # Subject-wise analysis
            subject_data = {}
            for g in grades:
                subj_name = g.subject.name if g.subject else f"Subject-{g.subject_id}"
                if subj_name not in subject_data:
                    subject_data[subj_name] = []
                subject_data[subj_name].append({
                    'exam_term': g.exam_term.name if g.exam_term else None,
                    'obtained_marks': g.obtained_marks,
                    'max_marks': g.max_marks,
                    'percentage': round((g.obtained_marks / g.max_marks) * 100, 2) if g.obtained_marks and g.max_marks else 0
                })

            # Subject-wise trends (average per subject)
            subject_averages = {}
            weak_subjects = []
            strong_subjects = []
            for subj, exams in subject_data.items():
                avg = sum(e['percentage'] for e in exams) / len(exams) if exams else 0
                subject_averages[subj] = round(avg, 2)
                if avg < 50:
                    weak_subjects.append({'subject': subj, 'average': avg})
                elif avg >= 80:
                    strong_subjects.append({'subject': subj, 'average': avg})

            # Overall performance
            all_percentages = [
                round((g.obtained_marks / g.max_marks) * 100, 2)
                for g in grades if g.obtained_marks and g.max_marks
            ]
            overall_avg = round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else 0

            # Rankings
            ranks = StudentRank.query.filter_by(
                school_id=school_id, student_id=student_id
            ).order_by(StudentRank.created_at.desc()).all()

            return {
                'success': True,
                'data': {
                    'student_id': student_id,
                    'overall_average': overall_avg,
                    'total_exams': len(grades),
                    'subject_averages': subject_averages,
                    'subject_trends': subject_data,
                    'weak_subjects': weak_subjects,
                    'strong_subjects': strong_subjects,
                    'ranks': [r.to_dict() for r in ranks]
                }
            }
        except Exception as e:
            logger.error(f"Student performance error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_class_performance(school_id, class_id, exam_term_id=None):
        """Class-level performance analytics"""
        try:
            query = GradeBook.query.join(ExamSchedule).filter(
                GradeBook.school_id == school_id,
                ExamSchedule.class_id == class_id
            )
            if exam_term_id:
                query = query.filter(GradeBook.exam_term_id == exam_term_id)

            grades = query.all()

            if not grades:
                return {'success': True, 'data': {'message': 'No exam data found'}}

            # Top performers
            student_totals = {}
            for g in grades:
                if g.student_id not in student_totals:
                    student_totals[g.student_id] = {
                        'name': g.student.name if g.student else None,
                        'total_marks': 0, 'max_total': 0, 'exams': 0
                    }
                if g.obtained_marks and g.max_marks:
                    student_totals[g.student_id]['total_marks'] += g.obtained_marks
                    student_totals[g.student_id]['max_total'] += g.max_marks
                    student_totals[g.student_id]['exams'] += 1

            # Calculate percentages and sort
            ranked = []
            for sid, data in student_totals.items():
                pct = round((data['total_marks'] / data['max_total']) * 100, 2) if data['max_total'] > 0 else 0
                ranked.append({
                    'student_id': sid,
                    'name': data['name'],
                    'percentage': pct,
                    'total_marks': data['total_marks'],
                    'max_total': data['max_total']
                })
            ranked.sort(key=lambda x: x['percentage'], reverse=True)

            # Class average
            class_avg = sum(r['percentage'] for r in ranked) / len(ranked) if ranked else 0

            # Subject averages for the class
            subject_avgs = {}
            for g in grades:
                subj_name = g.subject.name if g.subject else f"Subject-{g.subject_id}"
                if subj_name not in subject_avgs:
                    subject_avgs[subj_name] = {'total': 0, 'count': 0}
                if g.obtained_marks and g.max_marks:
                    subject_avgs[subj_name]['total'] += (g.obtained_marks / g.max_marks) * 100
                    subject_avgs[subj_name]['count'] += 1

            subject_class_avg = {
                subj: round(data['total'] / data['count'], 2) if data['count'] > 0 else 0
                for subj, data in subject_avgs.items()
            }

            # Pass/fail distribution
            pass_count = sum(1 for r in ranked if r['percentage'] >= 33)
            fail_count = len(ranked) - pass_count

            return {
                'success': True,
                'data': {
                    'class_id': class_id,
                    'class_average': round(class_avg, 2),
                    'total_students': len(ranked),
                    'pass_count': pass_count,
                    'fail_count': fail_count,
                    'pass_percentage': round((pass_count / len(ranked)) * 100, 2) if ranked else 0,
                    'top_performers': ranked[:10],
                    'bottom_performers': ranked[-5:] if len(ranked) > 5 else [],
                    'subject_averages': subject_class_avg
                }
            }
        except Exception as e:
            logger.error(f"Class performance error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_teacher_performance(school_id, teacher_id=None):
        """Teacher performance comparison based on student results"""
        try:
            query = db.session.query(
                ClassTeacherAssignment.teacher_id,
                User.name.label('teacher_name'),
                Subject.name.label('subject_name'),
                func.avg(
                    case(
                        (and_(GradeBook.obtained_marks.isnot(None), GradeBook.max_marks > 0),
                         GradeBook.obtained_marks * 100.0 / GradeBook.max_marks),
                        else_=None
                    )
                ).label('avg_percentage'),
                func.count(distinct(GradeBook.student_id)).label('students_taught')
            ).join(
                User, ClassTeacherAssignment.teacher_id == User.id
            ).join(
                Subject, ClassTeacherAssignment.subject_id == Subject.id
            ).outerjoin(
                GradeBook,
                and_(
                    GradeBook.school_id == ClassTeacherAssignment.school_id,
                    GradeBook.subject_id == ClassTeacherAssignment.subject_id
                )
            ).filter(ClassTeacherAssignment.school_id == school_id)

            if teacher_id:
                query = query.filter(ClassTeacherAssignment.teacher_id == teacher_id)

            results = query.group_by(
                ClassTeacherAssignment.teacher_id,
                User.name,
                Subject.name
            ).all()

            teachers = []
            for r in results:
                teachers.append({
                    'teacher_id': r.teacher_id,
                    'teacher_name': r.teacher_name,
                    'subject': r.subject_name,
                    'avg_student_percentage': round(float(r.avg_percentage), 2) if r.avg_percentage else None,
                    'students_taught': r.students_taught
                })

            return {'success': True, 'data': teachers}
        except Exception as e:
            logger.error(f"Teacher performance error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ==================== ADMISSION FUNNEL DASHBOARD ====================

    @staticmethod
    def get_admission_funnel(school_id, start_date=None, end_date=None):
        """Admission funnel analytics for CRM"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=365)
            if not end_date:
                end_date = datetime.utcnow()

            query = Enquiry.query.filter(
                Enquiry.school_id == school_id,
                Enquiry.created_at >= start_date,
                Enquiry.created_at <= end_date
            )

            total = query.count()

            # Status breakdown (funnel stages)
            status_counts = db.session.query(
                Enquiry.status,
                func.count(Enquiry.id).label('count')
            ).filter(
                Enquiry.school_id == school_id,
                Enquiry.created_at >= start_date,
                Enquiry.created_at <= end_date
            ).group_by(Enquiry.status).all()

            funnel = {s: c for s, c in status_counts}

            # Source performance
            source_counts = db.session.query(
                Enquiry.source,
                func.count(Enquiry.id).label('total'),
                func.sum(case((Enquiry.status == 'admitted', 1), else_=0)).label('converted')
            ).filter(
                Enquiry.school_id == school_id,
                Enquiry.created_at >= start_date,
                Enquiry.created_at <= end_date
            ).group_by(Enquiry.source).all()

            sources = []
            for s in source_counts:
                conv_rate = round((s.converted / s.total) * 100, 2) if s.total > 0 else 0
                sources.append({
                    'source': s.source or 'Unknown',
                    'total_enquiries': s.total,
                    'converted': int(s.converted),
                    'conversion_rate': conv_rate
                })

            # Monthly trend
            monthly = db.session.query(
                func.strftime('%Y-%m', Enquiry.created_at).label('month'),
                func.count(Enquiry.id).label('enquiries'),
                func.sum(case((Enquiry.status == 'admitted', 1), else_=0)).label('admissions')
            ).filter(
                Enquiry.school_id == school_id,
                Enquiry.created_at >= start_date,
                Enquiry.created_at <= end_date
            ).group_by(func.strftime('%Y-%m', Enquiry.created_at)).all()

            monthly_trends = [{
                'month': m.month,
                'enquiries': m.enquiries,
                'admissions': int(m.admissions),
                'conversion_rate': round((int(m.admissions) / m.enquiries) * 100, 2) if m.enquiries > 0 else 0
            } for m in monthly]

            # Overall conversion rate
            admitted = funnel.get('admitted', 0)
            conversion_rate = round((admitted / total) * 100, 2) if total > 0 else 0

            return {
                'success': True,
                'data': {
                    'total_enquiries': total,
                    'conversion_rate': conversion_rate,
                    'funnel_stages': funnel,
                    'source_performance': sources,
                    'monthly_trends': monthly_trends
                }
            }
        except Exception as e:
            logger.error(f"Admission funnel error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ==================== ATTENDANCE ANALYTICS ====================

    @staticmethod
    def get_attendance_analytics(school_id, class_id=None, start_date=None, end_date=None):
        """Attendance analytics with trend data"""
        try:
            if not start_date:
                start_date = (datetime.utcnow() - timedelta(days=30)).date()
            if not end_date:
                end_date = datetime.utcnow().date()

            query = Attendance.query.filter(
                Attendance.school_id == school_id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date
            )

            if class_id:
                query = query.join(Section).filter(Section.class_id == class_id)

            total_records = query.count()
            present_count = query.filter(Attendance.status == AttendanceStatus.PRESENT).count()
            absent_count = query.filter(Attendance.status == AttendanceStatus.ABSENT).count()
            late_count = query.filter(Attendance.status == AttendanceStatus.LATE).count()

            avg_attendance = round((present_count / total_records) * 100, 2) if total_records > 0 else 0

            # Students with low attendance (below 75%)
            student_att = db.session.query(
                Attendance.user_id,
                func.count(Attendance.id).label('total'),
                func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present')
            ).filter(
                Attendance.school_id == school_id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date
            ).group_by(Attendance.user_id).all()

            low_attendance_students = []
            for sa in student_att:
                pct = round((int(sa.present) / sa.total) * 100, 2) if sa.total > 0 else 0
                if pct < 75:
                    low_attendance_students.append({
                        'user_id': sa.user_id,
                        'attendance_percentage': pct,
                        'total_days': sa.total,
                        'present_days': int(sa.present)
                    })

            return {
                'success': True,
                'data': {
                    'total_records': total_records,
                    'present': present_count,
                    'absent': absent_count,
                    'late': late_count,
                    'average_attendance': avg_attendance,
                    'low_attendance_students_count': len(low_attendance_students),
                    'low_attendance_students': low_attendance_students[:20]
                }
            }
        except Exception as e:
            logger.error(f"Attendance analytics error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ==================== FEE ANALYTICS ====================

    @staticmethod
    def get_fee_analytics(school_id, academic_year=None):
        """Fee collection analytics"""
        try:
            from app.models.finance import FeePayment, StudentFeeInstallment, PaymentStatus

            # Total fees expected
            installment_query = StudentFeeInstallment.query.filter_by(school_id=school_id)
            total_expected = db.session.query(
                func.sum(StudentFeeInstallment.amount)
            ).filter_by(school_id=school_id).scalar() or 0

            total_paid = db.session.query(
                func.sum(StudentFeeInstallment.paid_amount)
            ).filter_by(school_id=school_id).scalar() or 0

            total_overdue = StudentFeeInstallment.query.filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
                StudentFeeInstallment.due_date < datetime.utcnow().date()
            ).count()

            # Payment method breakdown
            method_breakdown = db.session.query(
                FeePayment.payment_method,
                func.count(FeePayment.id).label('count'),
                func.sum(FeePayment.amount).label('total')
            ).filter_by(school_id=school_id).group_by(FeePayment.payment_method).all()

            methods = [{
                'method': m.payment_method,
                'count': m.count,
                'total': float(m.total) if m.total else 0
            } for m in method_breakdown]

            collection_rate = round((float(total_paid) / float(total_expected)) * 100, 2) if total_expected > 0 else 0

            return {
                'success': True,
                'data': {
                    'total_expected': float(total_expected),
                    'total_collected': float(total_paid),
                    'outstanding': float(total_expected) - float(total_paid),
                    'collection_rate': collection_rate,
                    'overdue_installments': total_overdue,
                    'payment_methods': methods
                }
            }
        except Exception as e:
            logger.error(f"Fee analytics error: {str(e)}")
            return {'success': False, 'error': str(e)}
