"""
Attendance Service - CRUD and business logic for attendance and leave
"""

from app.models.attendance import Attendance, LeaveRequest, AttendanceStatus, LeaveStatus, StaffCheckInOut
from app.extensions import db
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for attendance management"""
    
    @staticmethod
    def mark_attendance(school_id, user_id, attendance_date, status, section_id=None, 
                       subject_id=None, remarks=None, marked_by_id=None):
        """Mark attendance for a student/staff"""
        try:
            if status not in AttendanceStatus.CHOICES:
                return {'success': False, 'error': f'Invalid attendance status: {status}'}
            
            # Check if already marked
            existing = Attendance.query.filter_by(
                school_id=school_id,
                user_id=user_id,
                attendance_date=attendance_date,
                section_id=section_id,
                subject_id=subject_id
            ).first()
            
            if existing:
                # Update existing attendance
                existing.status = status
                existing.remarks = remarks
                existing.marked_by_id = marked_by_id
                db.session.commit()
                return {'success': True, 'attendance': existing.to_dict(), 'message': 'Updated'}
            
            # Create new attendance record
            attendance = Attendance(
                school_id=school_id,
                user_id=user_id,
                section_id=section_id,
                subject_id=subject_id,
                attendance_date=attendance_date,
                status=status,
                remarks=remarks,
                marked_by_id=marked_by_id
            )
            db.session.add(attendance)
            db.session.commit()
            
            return {'success': True, 'attendance': attendance.to_dict(), 'message': 'Created'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking attendance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def bulk_mark_attendance(school_id, section_id, attendance_date, records, marked_by_id):
        """Mark attendance for multiple students in a class/section"""
        try:
            results = []
            for record in records:
                result = AttendanceService.mark_attendance(
                    school_id=school_id,
                    user_id=record['user_id'],
                    attendance_date=attendance_date,
                    status=record['status'],
                    section_id=section_id,
                    remarks=record.get('remarks'),
                    marked_by_id=marked_by_id
                )
                results.append(result)
            
            success_count = sum(1 for r in results if r['success'])
            return {
                'success': True,
                'total': len(records),
                'marked': success_count,
                'results': results
            }
        except Exception as e:
            logger.error(f"Error bulk marking attendance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_attendance(school_id, user_id=None, section_id=None, from_date=None, to_date=None, page=1, limit=50):
        """Get attendance records"""
        try:
            query = Attendance.query.filter_by(school_id=school_id)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            if section_id:
                query = query.filter_by(section_id=section_id)
            if from_date:
                query = query.filter(Attendance.attendance_date >= from_date)
            if to_date:
                query = query.filter(Attendance.attendance_date <= to_date)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            records = query.offset((page - 1) * limit).limit(limit).order_by(Attendance.attendance_date.desc()).all()
            return {
                'success': True,
                'attendance': [a.to_dict() for a in records],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting attendance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_attendance_stats(school_id, user_id, from_date=None, to_date=None):
        """Get attendance statistics for a user"""
        try:
            if not from_date:
                from_date = date.today() - timedelta(days=30)
            if not to_date:
                to_date = date.today()
            
            query = Attendance.query.filter_by(
                school_id=school_id,
                user_id=user_id
            ).filter(Attendance.attendance_date.between(from_date, to_date))
            
            records = query.all()
            
            # Calculate statistics
            total_days = len(records)
            present_days = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
            absent_days = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
            late_days = sum(1 for r in records if r.status == AttendanceStatus.LATE)
            half_days = sum(1 for r in records if r.status == AttendanceStatus.HALF_DAY)
            excused_days = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
            
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            return {
                'success': True,
                'stats': {
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat(),
                    'total_days': total_days,
                    'present': present_days,
                    'absent': absent_days,
                    'late': late_days,
                    'half_day': half_days,
                    'excused': excused_days,
                    'attendance_percentage': round(attendance_percentage, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error getting attendance stats: {str(e)}")
            return {'success': False, 'error': str(e)}


class LeaveService:
    """Service for leave management"""
    
    @staticmethod
    def apply_leave(school_id, user_id, leave_type, start_date, end_date, reason, doc_url=None):
        """Apply for leave"""
        try:
            # Calculate number of days
            delta = end_date - start_date
            number_of_days = delta.days + 1
            
            leave_request = LeaveRequest(
                school_id=school_id,
                user_id=user_id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                number_of_days=number_of_days,
                reason=reason,
                supporting_doc_url=doc_url,
                status=LeaveStatus.PENDING
            )
            db.session.add(leave_request)
            db.session.commit()
            
            return {'success': True, 'leave': leave_request.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error applying leave: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def approve_leave(school_id, leave_id, approved_by_id):
        """Approve a leave request"""
        try:
            leave = LeaveRequest.query.filter_by(id=leave_id, school_id=school_id).first()
            if not leave:
                return {'success': False, 'error': 'Leave request not found'}
            
            if leave.status != LeaveStatus.PENDING:
                return {'success': False, 'error': f'Cannot approve leave in {leave.status} status'}
            
            leave.status = LeaveStatus.APPROVED
            leave.approved_by_id = approved_by_id
            leave.approved_on = datetime.utcnow()
            db.session.commit()
            
            return {'success': True, 'leave': leave.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error approving leave: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reject_leave(school_id, leave_id, approved_by_id, rejection_reason):
        """Reject a leave request"""
        try:
            leave = LeaveRequest.query.filter_by(id=leave_id, school_id=school_id).first()
            if not leave:
                return {'success': False, 'error': 'Leave request not found'}
            
            if leave.status != LeaveStatus.PENDING:
                return {'success': False, 'error': f'Cannot reject leave in {leave.status} status'}
            
            leave.status = LeaveStatus.REJECTED
            leave.approved_by_id = approved_by_id
            leave.approved_on = datetime.utcnow()
            leave.rejection_reason = rejection_reason
            db.session.commit()
            
            return {'success': True, 'leave': leave.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error rejecting leave: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_leave_requests(school_id, user_id=None, status=None, page=1, limit=50):
        """Get leave requests"""
        try:
            query = LeaveRequest.query.filter_by(school_id=school_id)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            if status:
                query = query.filter_by(status=status)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            leaves = query.offset((page - 1) * limit).limit(limit).order_by(LeaveRequest.start_date.desc()).all()
            return {
                'success': True,
                'leaves': [l.to_dict() for l in leaves],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting leave requests: {str(e)}")
            return {'success': False, 'error': str(e)}


class CheckInOutService:
    """Service for staff check-in/check-out"""
    
    @staticmethod
    def check_in(school_id, user_id, location=None, device_info=None):
        """Staff check-in"""
        try:
            # Check if already checked in today
            today = date.today()
            existing = StaffCheckInOut.query.filter(
                StaffCheckInOut.school_id == school_id,
                StaffCheckInOut.user_id == user_id,
                db.func.date(StaffCheckInOut.check_in_time) == today,
                StaffCheckInOut.check_out_time == None
            ).first()
            
            if existing:
                return {'success': False, 'error': 'Already checked in. Please check out first.'}
            
            check_in = StaffCheckInOut(
                school_id=school_id,
                user_id=user_id,
                check_in_time=datetime.utcnow(),
                location=location,
                device_info=device_info
            )
            db.session.add(check_in)
            db.session.commit()
            
            return {'success': True, 'check_in': check_in.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during check-in: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def check_out(school_id, user_id):
        """Staff check-out"""
        try:
            today = date.today()
            check_in = StaffCheckInOut.query.filter(
                StaffCheckInOut.school_id == school_id,
                StaffCheckInOut.user_id == user_id,
                db.func.date(StaffCheckInOut.check_in_time) == today,
                StaffCheckInOut.check_out_time == None
            ).first()
            
            if not check_in:
                return {'success': False, 'error': 'No active check-in found'}
            
            check_in.check_out_time = datetime.utcnow()
            db.session.commit()
            
            return {'success': True, 'check_out': check_in.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during check-out: {str(e)}")
            return {'success': False, 'error': str(e)}
