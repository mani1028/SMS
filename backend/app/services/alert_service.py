"""
Alert Service
Auto alerts for attendance, fees, exams, leaves, document expiry
"""
from app.models.alert import Alert, AlertRule, AlertType, AlertPriority
from app.models.attendance import Attendance, AttendanceStatus
from app.models.finance import StudentFeeInstallment
from app.models.exams import ExamSchedule
from app.models.logistics import Vehicle
from app.models.student import Student
from app.models.user import User
from app.extensions import db
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for auto-alert generation and management"""

    # ==================== ALERT CRUD ====================

    @staticmethod
    def create_alert(school_id, alert_type, title, message, priority='medium',
                     target_user_id=None, target_role=None, entity_type=None,
                     entity_id=None, is_auto=True, created_by_id=None,
                     send_email=False, send_sms=False):
        """Create a new alert"""
        try:
            alert = Alert(
                school_id=school_id,
                alert_type=alert_type,
                title=title,
                message=message,
                priority=priority,
                target_user_id=target_user_id,
                target_role=target_role,
                entity_type=entity_type,
                entity_id=entity_id,
                is_auto=is_auto,
                created_by_id=created_by_id,
                send_email=send_email,
                send_sms=send_sms
            )
            db.session.add(alert)
            db.session.commit()
            return {'success': True, 'alert': alert.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create alert error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_alerts(school_id, user_id=None, alert_type=None, is_read=None,
                   page=1, per_page=20):
        """Get alerts with filters"""
        try:
            query = Alert.query.filter_by(school_id=school_id)

            if user_id:
                query = query.filter(
                    db.or_(
                        Alert.target_user_id == user_id,
                        Alert.target_user_id.is_(None)
                    )
                )
            if alert_type:
                query = query.filter_by(alert_type=alert_type)
            if is_read is not None:
                query = query.filter_by(is_read=is_read)

            # Exclude expired
            query = query.filter(
                db.or_(
                    Alert.expires_at.is_(None),
                    Alert.expires_at > datetime.utcnow()
                )
            )

            query = query.order_by(Alert.created_at.desc())

            total = query.count()
            pages = (total + per_page - 1) // per_page
            alerts = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'success': True,
                'data': {
                    'alerts': [a.to_dict() for a in alerts],
                    'total': total,
                    'pages': pages,
                    'current_page': page,
                    'unread_count': Alert.query.filter_by(
                        school_id=school_id, is_read=False
                    ).count()
                }
            }
        except Exception as e:
            logger.error(f"Get alerts error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def mark_read(school_id, alert_id):
        """Mark alert as read"""
        try:
            alert = Alert.query.filter_by(id=alert_id, school_id=school_id).first()
            if not alert:
                return {'success': False, 'error': 'Alert not found'}
            alert.is_read = True
            alert.read_at = datetime.utcnow()
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def mark_all_read(school_id, user_id=None):
        """Mark all alerts as read"""
        try:
            query = Alert.query.filter_by(school_id=school_id, is_read=False)
            if user_id:
                query = query.filter(
                    db.or_(Alert.target_user_id == user_id, Alert.target_user_id.is_(None))
                )
            query.update({'is_read': True, 'read_at': datetime.utcnow()})
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def dismiss_alert(school_id, alert_id):
        """Dismiss an alert"""
        try:
            alert = Alert.query.filter_by(id=alert_id, school_id=school_id).first()
            if not alert:
                return {'success': False, 'error': 'Alert not found'}
            alert.is_dismissed = True
            alert.dismissed_at = datetime.utcnow()
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ==================== ALERT RULES ====================

    @staticmethod
    def create_alert_rule(school_id, alert_type, name, conditions=None,
                          notify_email=False, notify_sms=False, target_roles=None,
                          frequency='daily', description=None):
        """Create an alert automation rule"""
        try:
            rule = AlertRule(
                school_id=school_id,
                alert_type=alert_type,
                name=name,
                description=description,
                conditions=conditions or {},
                notify_email=notify_email,
                notify_sms=notify_sms,
                target_roles=target_roles or ['Admin'],
                frequency=frequency
            )
            db.session.add(rule)
            db.session.commit()
            return {'success': True, 'rule': rule.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_alert_rules(school_id):
        """Get all alert rules for a school"""
        try:
            rules = AlertRule.query.filter_by(school_id=school_id).all()
            return {'success': True, 'rules': [r.to_dict() for r in rules]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def toggle_rule(school_id, rule_id, enabled):
        """Enable/disable an alert rule"""
        try:
            rule = AlertRule.query.filter_by(id=rule_id, school_id=school_id).first()
            if not rule:
                return {'success': False, 'error': 'Rule not found'}
            rule.is_enabled = enabled
            db.session.commit()
            return {'success': True, 'rule': rule.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ==================== AUTO ALERT GENERATORS ====================

    @staticmethod
    def generate_low_attendance_alerts(school_id, threshold=75, period_days=30):
        """Generate alerts for students with attendance below threshold"""
        try:
            cutoff = (datetime.utcnow() - timedelta(days=period_days)).date()

            student_att = db.session.query(
                Attendance.user_id,
                func.count(Attendance.id).label('total'),
                func.sum(case(
                    (Attendance.status == AttendanceStatus.PRESENT, 1), else_=0
                )).label('present')
            ).filter(
                Attendance.school_id == school_id,
                Attendance.attendance_date >= cutoff
            ).group_by(Attendance.user_id).all()

            alerts_created = 0
            for sa in student_att:
                pct = round((int(sa.present) / sa.total) * 100, 2) if sa.total > 0 else 0
                if pct < threshold:
                    # Check if alert already exists recently
                    existing = Alert.query.filter(
                        Alert.school_id == school_id,
                        Alert.alert_type == AlertType.LOW_ATTENDANCE,
                        Alert.entity_id == sa.user_id,
                        Alert.created_at >= datetime.utcnow() - timedelta(days=7)
                    ).first()

                    if not existing:
                        user = User.query.get(sa.user_id)
                        name = user.name if user else f"Student #{sa.user_id}"
                        AlertService.create_alert(
                            school_id=school_id,
                            alert_type=AlertType.LOW_ATTENDANCE,
                            title=f"Low Attendance Alert: {name}",
                            message=f"{name}'s attendance is {pct}% (below {threshold}%) in the last {period_days} days.",
                            priority=AlertPriority.HIGH if pct < 50 else AlertPriority.MEDIUM,
                            target_user_id=sa.user_id,
                            target_role='Admin',
                            entity_type='student',
                            entity_id=sa.user_id
                        )
                        alerts_created += 1

            return {'success': True, 'alerts_created': alerts_created}
        except Exception as e:
            logger.error(f"Low attendance alerts error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_fee_overdue_alerts(school_id):
        """Generate alerts for overdue fee installments"""
        try:
            overdue = StudentFeeInstallment.query.filter(
                StudentFeeInstallment.school_id == school_id,
                StudentFeeInstallment.is_paid == False,
                StudentFeeInstallment.due_date < datetime.utcnow().date()
            ).all()

            alerts_created = 0
            for inst in overdue:
                # Check if alert already exists recently
                existing = Alert.query.filter(
                    Alert.school_id == school_id,
                    Alert.alert_type == AlertType.FEE_OVERDUE,
                    Alert.entity_id == inst.id,
                    Alert.created_at >= datetime.utcnow() - timedelta(days=7)
                ).first()

                if not existing:
                    days_overdue = (datetime.utcnow().date() - inst.due_date).days
                    outstanding = float(inst.amount) - float(inst.paid_amount)
                    user = User.query.get(inst.student_id)
                    name = user.name if user else f"Student #{inst.student_id}"

                    AlertService.create_alert(
                        school_id=school_id,
                        alert_type=AlertType.FEE_OVERDUE,
                        title=f"Fee Overdue: {name}",
                        message=f"{name} has an overdue fee installment of ₹{outstanding:.2f} ({days_overdue} days overdue).",
                        priority=AlertPriority.HIGH if days_overdue > 30 else AlertPriority.MEDIUM,
                        target_user_id=inst.student_id,
                        target_role='Admin',
                        entity_type='fee_installment',
                        entity_id=inst.id
                    )
                    alerts_created += 1

            return {'success': True, 'alerts_created': alerts_created}
        except Exception as e:
            logger.error(f"Fee overdue alerts error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_exam_reminders(school_id, days_before=3):
        """Generate exam reminder alerts"""
        try:
            upcoming_date = (datetime.utcnow() + timedelta(days=days_before)).date()
            today = datetime.utcnow().date()

            upcoming_exams = ExamSchedule.query.filter(
                ExamSchedule.school_id == school_id,
                ExamSchedule.exam_date >= today,
                ExamSchedule.exam_date <= upcoming_date,
                ExamSchedule.is_active == True
            ).all()

            alerts_created = 0
            for exam in upcoming_exams:
                existing = Alert.query.filter(
                    Alert.school_id == school_id,
                    Alert.alert_type == AlertType.EXAM_REMINDER,
                    Alert.entity_id == exam.id,
                    Alert.created_at >= datetime.utcnow() - timedelta(days=1)
                ).first()

                if not existing:
                    days_until = (exam.exam_date - today).days
                    AlertService.create_alert(
                        school_id=school_id,
                        alert_type=AlertType.EXAM_REMINDER,
                        title=f"Exam Reminder: {exam.subject.name if exam.subject else 'Exam'}",
                        message=f"Exam for {exam.subject.name if exam.subject else 'subject'} "
                                f"(Class {exam.class_obj.name if exam.class_obj else ''}) "
                                f"is scheduled in {days_until} day(s) on {exam.exam_date.isoformat()}.",
                        priority=AlertPriority.MEDIUM,
                        entity_type='exam_schedule',
                        entity_id=exam.id
                    )
                    alerts_created += 1

            return {'success': True, 'alerts_created': alerts_created}
        except Exception as e:
            logger.error(f"Exam reminders error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def run_all_auto_alerts(school_id):
        """Run all auto-alert generators for a school"""
        try:
            results = {}
            results['low_attendance'] = AlertService.generate_low_attendance_alerts(school_id)
            results['fee_overdue'] = AlertService.generate_fee_overdue_alerts(school_id)
            results['exam_reminder'] = AlertService.generate_exam_reminders(school_id)

            total = sum(
                r.get('alerts_created', 0)
                for r in results.values()
                if r.get('success')
            )

            return {
                'success': True,
                'total_alerts_created': total,
                'details': results
            }
        except Exception as e:
            logger.error(f"Run all auto alerts error: {str(e)}")
            return {'success': False, 'error': str(e)}
