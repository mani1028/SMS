from datetime import datetime
import logging

from app.core.validators import InputValidator, ValidationError
from app.extensions import db
from app.models.role import Role
from app.models.staff import (
    Staff,
    StaffSalary,
    StaffAttendance,
    LeaveRequest,
    AttendanceStatus,
    LeaveStatus,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class StaffService:
    """Service layer for staff/teacher module."""

    @staticmethod
    def create_staff(school_id, payload):
        """Create user first and then staff profile."""
        try:
            required_fields = [
                'name',
                'email',
                'password',
                'role_name',
                'staff_no',
                'department',
                'designation',
                'date_of_joining',
            ]
            InputValidator.validate_required_fields(payload, required_fields)

            name = InputValidator.sanitize_string(payload.get('name'))
            email = InputValidator.sanitize_string(payload.get('email')).lower()
            password = payload.get('password')
            role_name = InputValidator.sanitize_string(payload.get('role_name'))
            staff_no = InputValidator.sanitize_string(payload.get('staff_no'))
            department = InputValidator.sanitize_string(payload.get('department'))
            designation = InputValidator.sanitize_string(payload.get('designation'))
            date_of_joining_raw = InputValidator.sanitize_string(
                payload.get('date_of_joining')
            )

            InputValidator.validate_email(email)
            InputValidator.validate_string(password, 'password', min_length=8, max_length=128)
            InputValidator.validate_string(staff_no, 'staff_no', min_length=1, max_length=100)

            try:
                date_of_joining = datetime.strptime(
                    date_of_joining_raw,
                    '%Y-%m-%d'
                ).date()
            except ValueError as exc:
                raise ValidationError('date_of_joining must be in YYYY-MM-DD format') from exc

            role = Role.query.filter_by(
                school_id=school_id,
                name=role_name
            ).first()
            if not role:
                return {'success': False, 'error': f'Role not found: {role_name}'}

            existing_user = User.query.filter_by(
                school_id=school_id,
                email=email
            ).first()
            if existing_user:
                return {'success': False, 'error': 'User email already exists'}

            existing_staff_no = Staff.query.filter_by(
                school_id=school_id,
                staff_no=staff_no
            ).first()
            if existing_staff_no:
                return {'success': False, 'error': 'staff_no already exists'}

            user = User(
                school_id=school_id,
                name=name,
                email=email,
                role_id=role.id,
                is_active=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            staff = Staff(
                school_id=school_id,
                user_id=user.id,
                staff_no=staff_no,
                department=department,
                designation=designation,
                date_of_joining=date_of_joining,
                qualification=InputValidator.sanitize_string(
                    payload.get('qualification', '')
                ) or None,
                experience=float(payload.get('experience', 0) or 0),
                is_teaching_staff=InputValidator.validate_boolean(
                    payload.get('is_teaching_staff', True),
                    'is_teaching_staff'
                ),
            )
            db.session.add(staff)
            db.session.flush()

            salary_payload = payload.get('salary') or {}
            if salary_payload:
                salary = StaffSalary(
                    school_id=school_id,
                    staff_id=staff.id,
                    basic_salary=float(salary_payload.get('basic_salary', 0) or 0),
                    allowances=float(salary_payload.get('allowances', 0) or 0),
                    deductions=float(salary_payload.get('deductions', 0) or 0),
                    bank_account_details=InputValidator.sanitize_string(
                        salary_payload.get('bank_account_details', '')
                    ) or None,
                    pan_number=InputValidator.sanitize_string(
                        salary_payload.get('pan_number', '')
                    ) or None,
                )
                db.session.add(salary)

            db.session.commit()
            return {
                'success': True,
                'message': 'Staff created successfully',
                'staff': staff.to_dict(include_relations=True),
            }
        except ValidationError as exc:
            db.session.rollback()
            return {'success': False, 'error': str(exc)}
        except Exception as exc:
            logger.error(f'Create staff error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def get_staff_list(school_id, page=1, limit=20, department=None, role_name=None):
        """Get paginated staff list with optional filters."""
        try:
            query = Staff.query.filter_by(school_id=school_id).join(User)

            if department:
                query = query.filter(Staff.department == department)

            if role_name:
                query = query.join(Role, User.role_id == Role.id).filter(Role.name == role_name)

            pagination = query.order_by(Staff.created_at.desc()).paginate(
                page=page,
                per_page=limit,
                error_out=False
            )

            return {
                'success': True,
                'staff': [member.to_dict() for member in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
            }
        except Exception as exc:
            logger.error(f'Get staff list error: {str(exc)}')
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def record_attendance(school_id, attendance_date, records):
        """Bulk create or update attendance for one date."""
        try:
            try:
                parsed_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            except ValueError as exc:
                raise ValidationError('attendance_date must be in YYYY-MM-DD format') from exc

            updated_records = []
            for entry in records:
                staff_id = entry.get('staff_id')
                status_raw = InputValidator.sanitize_string(entry.get('status'))
                check_in_out_time = InputValidator.sanitize_string(
                    entry.get('check_in_out_time', '')
                ) or None

                staff = Staff.query.filter_by(
                    id=staff_id,
                    school_id=school_id
                ).first()
                if not staff:
                    return {'success': False, 'error': f'Staff not found: {staff_id}'}

                try:
                    status_enum = AttendanceStatus(status_raw)
                except ValueError:
                    return {
                        'success': False,
                        'error': 'status must be Present, Absent, Leave, or Late'
                    }

                attendance = StaffAttendance.query.filter_by(
                    school_id=school_id,
                    staff_id=staff.id,
                    date=parsed_date
                ).first()

                if attendance:
                    attendance.status = status_enum
                    attendance.check_in_out_time = check_in_out_time
                else:
                    attendance = StaffAttendance(
                        school_id=school_id,
                        staff_id=staff.id,
                        date=parsed_date,
                        status=status_enum,
                        check_in_out_time=check_in_out_time,
                    )
                    db.session.add(attendance)

                updated_records.append(attendance)

            db.session.commit()
            return {
                'success': True,
                'message': 'Attendance recorded successfully',
                'attendance': [record.to_dict() for record in updated_records],
            }
        except ValidationError as exc:
            db.session.rollback()
            return {'success': False, 'error': str(exc)}
        except Exception as exc:
            logger.error(f'Record attendance error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def process_leave(school_id, payload, reviewer_user_id=None):
        """Apply for leave or approve/reject an existing leave request."""
        try:
            action = InputValidator.sanitize_string(payload.get('action', 'apply')).lower()

            if action == 'apply':
                required_fields = [
                    'staff_id',
                    'leave_type',
                    'start_date',
                    'end_date',
                    'reason',
                ]
                InputValidator.validate_required_fields(payload, required_fields)

                staff = Staff.query.filter_by(
                    id=payload.get('staff_id'),
                    school_id=school_id
                ).first()
                if not staff:
                    return {'success': False, 'error': 'Staff not found'}

                try:
                    start_date = datetime.strptime(
                        InputValidator.sanitize_string(payload.get('start_date')),
                        '%Y-%m-%d'
                    ).date()
                    end_date = datetime.strptime(
                        InputValidator.sanitize_string(payload.get('end_date')),
                        '%Y-%m-%d'
                    ).date()
                except ValueError as exc:
                    raise ValidationError('start_date/end_date must be in YYYY-MM-DD format') from exc

                if end_date < start_date:
                    return {
                        'success': False,
                        'error': 'end_date must be greater than or equal to start_date'
                    }

                leave_request = LeaveRequest(
                    school_id=school_id,
                    staff_id=staff.id,
                    leave_type=InputValidator.sanitize_string(payload.get('leave_type')),
                    start_date=start_date,
                    end_date=end_date,
                    reason=InputValidator.sanitize_string(payload.get('reason')),
                    status=LeaveStatus.PENDING,
                )
                db.session.add(leave_request)
                db.session.commit()

                return {
                    'success': True,
                    'message': 'Leave request submitted successfully',
                    'leave_request': leave_request.to_dict(),
                }

            leave_id = payload.get('leave_id')
            decision = InputValidator.sanitize_string(payload.get('status', '')).capitalize()
            if not leave_id or decision not in ('Approved', 'Rejected'):
                return {
                    'success': False,
                    'error': 'leave_id and status (Approved/Rejected) are required for decision'
                }

            leave_request = LeaveRequest.query.filter_by(
                id=leave_id,
                school_id=school_id
            ).first()
            if not leave_request:
                return {'success': False, 'error': 'Leave request not found'}

            leave_request.status = LeaveStatus(decision)
            db.session.commit()

            result = leave_request.to_dict()
            result['reviewed_by'] = reviewer_user_id
            return {
                'success': True,
                'message': f'Leave request {decision.lower()} successfully',
                'leave_request': result,
            }
        except ValidationError as exc:
            db.session.rollback()
            return {'success': False, 'error': str(exc)}
        except Exception as exc:
            logger.error(f'Process leave error: {str(exc)}')
            db.session.rollback()
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def generate_id_card_data(staff_id, school_id):
        """Build data payload for staff ID card generation."""
        try:
            staff = Staff.query.filter_by(id=staff_id, school_id=school_id).first()
            if not staff:
                return {
                    'success': False,
                    'error': 'Staff not found',
                    'status_code': 404,
                }

            data = {
                'name': staff.user.name if staff.user else None,
                'photo_path': None,
                'staff_no': staff.staff_no,
                'department': staff.department,
                'blood_group': None,
            }
            return {'success': True, 'id_card_data': data}
        except Exception as exc:
            logger.error(f'Generate ID card data error: {str(exc)}')
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def get_staff_profile(staff_id, school_id):
        """Get detailed staff profile including salary and role."""
        try:
            staff = Staff.query.filter_by(id=staff_id, school_id=school_id).first()
            if not staff:
                return {
                    'success': False,
                    'error': 'Staff not found',
                    'status_code': 404,
                }

            profile = staff.to_dict(include_relations=True)
            return {'success': True, 'profile': profile}
        except Exception as exc:
            logger.error(f'Get staff profile error: {str(exc)}')
            return {'success': False, 'error': str(exc)}
