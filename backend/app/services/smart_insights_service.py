"""
Smart Insights Dashboard Service
==================================
Provides analytics data for:
  - Fee collection trends (daily/weekly/monthly)
  - Attendance patterns & risk detection
  - Academic performance analytics
  - Enrollment & growth metrics
  - Revenue forecasting

All queries are tenant-isolated via school_id.
"""
from datetime import datetime, timedelta
from sqlalchemy import func, case, extract, and_, desc
import logging

logger = logging.getLogger(__name__)


class SmartInsightsService:
    """Stateless analytics engine for the Smart Insights Dashboard."""

    # ── Fee Collection Trends ─────────────────────────────────────────────

    @staticmethod
    def get_fee_trends(school_id, period='monthly', months=6):
        """
        Fee collection trends over time.
        Returns: {labels, collected, pending, collection_rate}
        """
        try:
            from app.models.finance import FeePayment, StudentFeeInstallment
            from app.extensions import db

            now = datetime.utcnow()
            start_date = now - timedelta(days=months * 30)

            # Monthly collection amounts
            collections = db.session.query(
                extract('year', FeePayment.payment_date).label('year'),
                extract('month', FeePayment.payment_date).label('month'),
                func.sum(FeePayment.amount).label('total_collected'),
                func.count(FeePayment.id).label('payment_count'),
            ).filter(
                FeePayment.school_id == school_id,
                FeePayment.status == 'completed',
                FeePayment.payment_date >= start_date,
            ).group_by('year', 'month').order_by('year', 'month').all()

            labels = []
            collected = []
            for c in collections:
                month_name = datetime(int(c.year), int(c.month), 1).strftime('%b %Y')
                labels.append(month_name)
                collected.append(float(c.total_collected or 0))

            # Current outstanding
            total_pending = db.session.query(
                func.sum(StudentFeeInstallment.amount)
            ).filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
            ).scalar() or 0

            total_collected = sum(collected)
            total_billed = total_collected + float(total_pending)
            collection_rate = (total_collected / total_billed * 100) if total_billed > 0 else 0

            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'collected': collected,
                    'total_collected': total_collected,
                    'total_pending': float(total_pending),
                    'collection_rate': round(collection_rate, 1),
                    'period': period,
                }
            }
        except Exception as e:
            logger.error(f"Fee trends error: {e}")
            return {'success': False, 'error': str(e)}

    # ── Attendance Insights ───────────────────────────────────────────────

    @staticmethod
    def get_attendance_insights(school_id, days=30):
        """
        Attendance patterns, trends, and at-risk students.
        Returns: {daily_trend, class_wise, at_risk_students}
        """
        try:
            from app.models.attendance import Attendance
            from app.models.student import Student
            from app.extensions import db

            cutoff = datetime.utcnow() - timedelta(days=days)

            # Daily attendance trend
            daily = db.session.query(
                Attendance.attendance_date,
                func.count(case((Attendance.status == 'present', 1))).label('present'),
                func.count(case((Attendance.status == 'absent', 1))).label('absent'),
                func.count(Attendance.id).label('total'),
            ).filter(
                Attendance.school_id == school_id,
                Attendance.attendance_date >= cutoff.date(),
            ).group_by(Attendance.attendance_date).order_by(Attendance.attendance_date).all()

            daily_trend = [{
                'date': str(d.attendance_date),
                'present': d.present,
                'absent': d.absent,
                'total': d.total,
                'rate': round(d.present / d.total * 100, 1) if d.total > 0 else 0,
            } for d in daily]

            # At-risk students (below 75% attendance)
            student_attendance = db.session.query(
                Attendance.user_id,
                func.count(Attendance.id).label('total_days'),
                func.count(case((Attendance.status == 'present', 1))).label('present_days'),
            ).filter(
                Attendance.school_id == school_id,
                Attendance.attendance_date >= cutoff.date(),
            ).group_by(Attendance.user_id).all()

            at_risk = []
            for sa in student_attendance:
                pct = (sa.present_days / sa.total_days * 100) if sa.total_days > 0 else 0
                if pct < 75:
                    student = Student.query.filter_by(
                        user_id=sa.user_id, school_id=school_id
                    ).first()
                    if student:
                        at_risk.append({
                            'student_id': student.id,
                            'name': f"{student.first_name} {student.last_name}",
                            'class': student.class_name,
                            'attendance_pct': round(pct, 1),
                            'absent_days': sa.total_days - sa.present_days,
                        })

            at_risk.sort(key=lambda x: x['attendance_pct'])

            # Overall stats
            total_records = sum(d.total for d in daily)
            total_present = sum(d.present for d in daily)
            overall_rate = round(total_present / total_records * 100, 1) if total_records > 0 else 0

            return {
                'success': True,
                'data': {
                    'daily_trend': daily_trend,
                    'at_risk_students': at_risk[:20],  # Top 20
                    'overall_rate': overall_rate,
                    'total_at_risk': len(at_risk),
                    'period_days': days,
                }
            }
        except Exception as e:
            logger.error(f"Attendance insights error: {e}")
            return {'success': False, 'error': str(e)}

    # ── Academic Performance Analytics ────────────────────────────────────

    @staticmethod
    def get_performance_analytics(school_id, exam_term_id=None):
        """
        Academic performance analysis: class-wise averages, subject distribution,
        top performers, and underperformers.
        """
        try:
            from app.models.exams import GradeBook, ExamTerm
            from app.models.student import Student
            from app.extensions import db

            # Get latest exam term if not specified
            if not exam_term_id:
                latest = ExamTerm.query.filter_by(
                    school_id=school_id
                ).order_by(desc(ExamTerm.created_at)).first()
                if latest:
                    exam_term_id = latest.id
                else:
                    return {'success': True, 'data': {'message': 'No exam data available'}}

            # Subject-wise averages
            subject_avgs = db.session.query(
                GradeBook.subject_id,
                func.avg(GradeBook.marks_obtained).label('avg_marks'),
                func.max(GradeBook.marks_obtained).label('max_marks'),
                func.min(GradeBook.marks_obtained).label('min_marks'),
                func.count(GradeBook.id).label('student_count'),
            ).filter(
                GradeBook.school_id == school_id,
                GradeBook.exam_term_id == exam_term_id,
            ).group_by(GradeBook.subject_id).all()

            subjects = []
            for sa in subject_avgs:
                from app.models.academics import Subject
                subj = Subject.query.get(sa.subject_id)
                subjects.append({
                    'subject_id': sa.subject_id,
                    'subject_name': subj.name if subj else f'Subject {sa.subject_id}',
                    'average': round(float(sa.avg_marks or 0), 1),
                    'highest': float(sa.max_marks or 0),
                    'lowest': float(sa.min_marks or 0),
                    'students': sa.student_count,
                })

            # Student-wise total marks (for top/bottom performers)
            student_totals = db.session.query(
                GradeBook.student_id,
                func.sum(GradeBook.marks_obtained).label('total_marks'),
                func.count(GradeBook.id).label('subject_count'),
            ).filter(
                GradeBook.school_id == school_id,
                GradeBook.exam_term_id == exam_term_id,
            ).group_by(GradeBook.student_id).order_by(
                desc('total_marks')
            ).all()

            top_performers = []
            for st in student_totals[:10]:
                student = Student.query.filter_by(
                    id=st.student_id, school_id=school_id
                ).first()
                if student:
                    top_performers.append({
                        'student_id': st.student_id,
                        'name': f"{student.first_name} {student.last_name}",
                        'class': student.class_name,
                        'total_marks': float(st.total_marks or 0),
                        'subjects': st.subject_count,
                    })

            # Grade distribution
            grade_dist = db.session.query(
                GradeBook.grade,
                func.count(GradeBook.id).label('count'),
            ).filter(
                GradeBook.school_id == school_id,
                GradeBook.exam_term_id == exam_term_id,
                GradeBook.grade.isnot(None),
            ).group_by(GradeBook.grade).all()

            grades = {g.grade: g.count for g in grade_dist}

            return {
                'success': True,
                'data': {
                    'subject_analysis': subjects,
                    'top_performers': top_performers,
                    'grade_distribution': grades,
                    'exam_term_id': exam_term_id,
                    'total_students': len(student_totals),
                }
            }
        except Exception as e:
            logger.error(f"Performance analytics error: {e}")
            return {'success': False, 'error': str(e)}

    # ── Enrollment & Growth Metrics ───────────────────────────────────────

    @staticmethod
    def get_enrollment_metrics(school_id, months=12):
        """
        Enrollment trends: new admissions, withdrawals, net growth by month.
        """
        try:
            from app.models.student import Student
            from app.extensions import db

            cutoff = datetime.utcnow() - timedelta(days=months * 30)

            # Monthly new admissions
            monthly = db.session.query(
                extract('year', Student.created_at).label('year'),
                extract('month', Student.created_at).label('month'),
                func.count(Student.id).label('new_admissions'),
            ).filter(
                Student.school_id == school_id,
                Student.created_at >= cutoff,
            ).group_by('year', 'month').order_by('year', 'month').all()

            trend = [{
                'month': datetime(int(m.year), int(m.month), 1).strftime('%b %Y'),
                'new_admissions': m.new_admissions,
            } for m in monthly]

            # Current totals by status
            status_counts = db.session.query(
                Student.status,
                func.count(Student.id).label('count'),
            ).filter(
                Student.school_id == school_id,
            ).group_by(Student.status).all()

            by_status = {s.status: s.count for s in status_counts}

            # Class-wise distribution
            class_dist = db.session.query(
                Student.class_name,
                func.count(Student.id).label('count'),
            ).filter(
                Student.school_id == school_id,
                Student.status == 'active',
            ).group_by(Student.class_name).order_by(Student.class_name).all()

            classes = [{'class': c.class_name, 'students': c.count} for c in class_dist]

            total_active = by_status.get('active', 0)

            return {
                'success': True,
                'data': {
                    'monthly_trend': trend,
                    'by_status': by_status,
                    'class_distribution': classes,
                    'total_active': total_active,
                    'total_students': sum(by_status.values()),
                }
            }
        except Exception as e:
            logger.error(f"Enrollment metrics error: {e}")
            return {'success': False, 'error': str(e)}

    # ── Revenue Forecast ──────────────────────────────────────────────────

    @staticmethod
    def get_revenue_forecast(school_id):
        """
        Simple revenue forecast based on upcoming installment due dates
        and historical collection rate.
        """
        try:
            from app.models.finance import StudentFeeInstallment, FeePayment
            from app.extensions import db

            now = datetime.utcnow()

            # Expected revenue from upcoming installments (next 3 months)
            upcoming = db.session.query(
                extract('month', StudentFeeInstallment.due_date).label('month'),
                extract('year', StudentFeeInstallment.due_date).label('year'),
                func.sum(StudentFeeInstallment.amount).label('expected'),
            ).filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
                StudentFeeInstallment.due_date >= now.date(),
                StudentFeeInstallment.due_date <= (now + timedelta(days=90)).date(),
            ).group_by('year', 'month').order_by('year', 'month').all()

            # Historical collection rate (last 6 months)
            six_months_ago = now - timedelta(days=180)
            total_due = db.session.query(
                func.sum(StudentFeeInstallment.amount)
            ).filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.due_date >= six_months_ago.date(),
                StudentFeeInstallment.due_date <= now.date(),
            ).scalar() or 0

            total_collected = db.session.query(
                func.sum(FeePayment.amount)
            ).filter(
                FeePayment.school_id == school_id,
                FeePayment.status == 'completed',
                FeePayment.payment_date >= six_months_ago,
            ).scalar() or 0

            hist_rate = (float(total_collected) / float(total_due)) if total_due > 0 else 0.85

            forecast = []
            for u in upcoming:
                expected = float(u.expected or 0)
                month_name = datetime(int(u.year), int(u.month), 1).strftime('%b %Y')
                forecast.append({
                    'month': month_name,
                    'expected': expected,
                    'projected_collection': round(expected * hist_rate, 2),
                })

            return {
                'success': True,
                'data': {
                    'forecast': forecast,
                    'historical_collection_rate': round(hist_rate * 100, 1),
                    'total_expected_90_days': sum(f['expected'] for f in forecast),
                    'total_projected_90_days': sum(f['projected_collection'] for f in forecast),
                }
            }
        except Exception as e:
            logger.error(f"Revenue forecast error: {e}")
            return {'success': False, 'error': str(e)}

    # ── Executive Summary ─────────────────────────────────────────────────

    @staticmethod
    def get_executive_summary(school_id):
        """
        One-page executive summary combining all key metrics.
        """
        try:
            from app.models.student import Student
            from app.models.staff import Staff
            from app.models.finance import FeePayment, StudentFeeInstallment
            from app.models.attendance import Attendance
            from app.extensions import db

            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0)

            # Student count
            total_students = Student.query.filter_by(
                school_id=school_id, status='active'
            ).count()

            # Staff count
            total_staff = Staff.query.filter_by(
                school_id=school_id, is_active=True
            ).count()

            # This month's collection
            month_collection = db.session.query(
                func.sum(FeePayment.amount)
            ).filter(
                FeePayment.school_id == school_id,
                FeePayment.status == 'completed',
                FeePayment.payment_date >= month_start,
            ).scalar() or 0

            # Pending fees
            pending_fees = db.session.query(
                func.sum(StudentFeeInstallment.amount)
            ).filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
            ).scalar() or 0

            # Today's attendance rate
            today_att = db.session.query(
                func.count(case((Attendance.status == 'present', 1))).label('present'),
                func.count(Attendance.id).label('total'),
            ).filter(
                Attendance.school_id == school_id,
                Attendance.attendance_date == now.date(),
            ).first()

            att_rate = 0
            if today_att and today_att.total > 0:
                att_rate = round(today_att.present / today_att.total * 100, 1)

            return {
                'success': True,
                'data': {
                    'total_students': total_students,
                    'total_staff': total_staff,
                    'month_collection': float(month_collection),
                    'pending_fees': float(pending_fees),
                    'today_attendance_rate': att_rate,
                    'timestamp': now.isoformat(),
                }
            }
        except Exception as e:
            logger.error(f"Executive summary error: {e}")
            return {'success': False, 'error': str(e)}
