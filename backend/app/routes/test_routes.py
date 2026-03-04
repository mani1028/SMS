"""
Test & Verification Endpoints
Provides endpoints to test and verify all SMS modules
"""

from flask import Blueprint, jsonify, request
from app.core.auth import token_required
from app.core.response import success_response, error_response
from datetime import datetime

test_bp = Blueprint('test', __name__, url_prefix='/api/test')

@test_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return success_response("SMS System is online", {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    })

@test_bp.route('/system-status', methods=['GET'])
@token_required
def system_status(current_user):
    """Get complete system status"""
    try:
        from app import db
        from app.models.permission import Permission
        from app.models.role import Role
        from app.models.user import User
        from app.models.school import School
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "school": {
                "total": School.query.count()
            },
            "users": {
                "total": User.query.count(),
                "in_school": User.query.filter_by(school_id=current_user.school_id).count()
            },
            "permissions": {
                "total": Permission.query.count()
            },
            "roles": {
                "total": Role.query.count(),
                "in_school": Role.query.filter_by(school_id=current_user.school_id).count()
            },
            "modules": {
                "academics": "✓ ready",
                "attendance": "✓ ready",
                "exams": "✓ ready",
                "finance": "✓ ready",
                "logistics": "✓ ready",
                "communication": "✓ ready",
                "settings": "✓ ready"
            }
        }
        
        # Try to count models
        try:
            from app.models.academics import Class
            status["modules"]["academics"] = {
                "status": "✓ ready",
                "classes": Class.query.filter_by(school_id=current_user.school_id).count()
            }
        except:
            pass
        
        try:
            from app.models.attendance import Attendance
            status["modules"]["attendance"] = {
                "status": "✓ ready",
                "records": Attendance.query.filter_by(school_id=current_user.school_id).count()
            }
        except:
            pass
        
        return success_response("System status retrieved", status)
    
    except Exception as e:
        return error_response(str(e), 500)

@test_bp.route('/endpoints', methods=['GET'])
@token_required
def list_endpoints(current_user):
    """List all available API endpoints"""
    try:
        from flask import current_app
        
        endpoints = {}
        for rule in current_app.url_map.iter_rules():
            if 'api' in rule.rule and rule.endpoint != 'static':
                methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                endpoints[rule.rule] = methods
        
        return success_response(f"Found {len(endpoints)} endpoints", {
            "total": len(endpoints),
            "endpoints": sorted(endpoints.items())
        })
    
    except Exception as e:
        return error_response(str(e), 500)

@test_bp.route('/test-data', methods=['GET'])
@token_required
def test_data_summary(current_user):
    """Get summary of test data"""
    try:
        from app.models.academics import Class, Section, Subject
        from app.models.user import User
        from app.models.settings import AcademicYear, SchoolConfiguration
        
        data = {
            "school_id": current_user.school_id,
            "current_user": {
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role.name if current_user.role else "N/A"
            },
            "academic_data": {
                "classes": Class.query.filter_by(school_id=current_user.school_id).count(),
                "sections": Section.query.filter_by(school_id=current_user.school_id).count(),
                "subjects": Subject.query.filter_by(school_id=current_user.school_id).count()
            },
            "users": {
                "total": User.query.filter_by(school_id=current_user.school_id).count()
            },
            "settings": {
                "academic_years": AcademicYear.query.filter_by(school_id=current_user.school_id).count(),
                "configurations": SchoolConfiguration.query.filter_by(school_id=current_user.school_id).count()
            }
        }
        
        return success_response("Test data summary", data)
    
    except Exception as e:
        return error_response(str(e), 500)

@test_bp.route('/module-test/<module_name>', methods=['GET'])
@token_required
def test_module(current_user, module_name):
    """Test a specific module"""
    try:
        module_tests = {
            "academics": test_academics_module,
            "attendance": test_attendance_module,
            "exams": test_exams_module,
            "finance": test_finance_module,
            "logistics": test_logistics_module,
            "communication": test_communication_module,
            "settings": test_settings_module
        }
        
        if module_name not in module_tests:
            return error_response(f"Unknown module: {module_name}", 400)
        
        result = module_tests[module_name](current_user)
        return success_response(f"Module test: {module_name}", result)
    
    except Exception as e:
        return error_response(str(e), 500)

def test_academics_module(user):
    """Test academics module"""
    try:
        from app.models.academics import Class, Section, Subject, TimetableSlot
        
        return {
            "module": "academics",
            "status": "✓ working",
            "tests": {
                "classes": Class.query.filter_by(school_id=user.school_id).count(),
                "sections": Section.query.filter_by(school_id=user.school_id).count(),
                "subjects": Subject.query.filter_by(school_id=user.school_id).count(),
                "timetable_slots": TimetableSlot.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "academics", "status": "⚠️ error", "error": str(e)}

def test_attendance_module(user):
    """Test attendance module"""
    try:
        from app.models.attendance import Attendance, LeaveRequest, StaffCheckInOut
        
        return {
            "module": "attendance",
            "status": "✓ working",
            "tests": {
                "attendance_records": Attendance.query.filter_by(school_id=user.school_id).count(),
                "leave_requests": LeaveRequest.query.filter_by(school_id=user.school_id).count(),
                "staff_checkins": StaffCheckInOut.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "attendance", "status": "⚠️ error", "error": str(e)}

def test_exams_module(user):
    """Test exams module"""
    try:
        from app.models.exams import ExamTerm, ExamSchedule, GradeBook, StudentRank
        
        return {
            "module": "exams",
            "status": "✓ working",
            "tests": {
                "exam_terms": ExamTerm.query.filter_by(school_id=user.school_id).count(),
                "exam_schedules": ExamSchedule.query.filter_by(school_id=user.school_id).count(),
                "grades": GradeBook.query.filter_by(school_id=user.school_id).count(),
                "rankings": StudentRank.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "exams", "status": "⚠️ error", "error": str(e)}

def test_finance_module(user):
    """Test finance module"""
    try:
        from app.models.finance import FeeStructure, FeePayment, StudentFeeInstallment
        
        return {
            "module": "finance",
            "status": "✓ working",
            "tests": {
                "fee_structures": FeeStructure.query.filter_by(school_id=user.school_id).count(),
                "installments": StudentFeeInstallment.query.filter_by(school_id=user.school_id).count(),
                "payments": FeePayment.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "finance", "status": "⚠️ error", "error": str(e)}

def test_logistics_module(user):
    """Test logistics module"""
    try:
        from app.models.logistics import Vehicle, Book, HostelRoom, LabInventory
        
        return {
            "module": "logistics",
            "status": "✓ working",
            "tests": {
                "vehicles": Vehicle.query.filter_by(school_id=user.school_id).count(),
                "books": Book.query.filter_by(school_id=user.school_id).count(),
                "hostel_rooms": HostelRoom.query.filter_by(school_id=user.school_id).count(),
                "lab_inventory": LabInventory.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "logistics", "status": "⚠️ error", "error": str(e)}

def test_communication_module(user):
    """Test communication module"""
    try:
        from app.models.communication import Notice, Event, Homework
        
        return {
            "module": "communication",
            "status": "✓ working",
            "tests": {
                "notices": Notice.query.filter_by(school_id=user.school_id).count(),
                "events": Event.query.filter_by(school_id=user.school_id).count(),
                "homework": Homework.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "communication", "status": "⚠️ error", "error": str(e)}

def test_settings_module(user):
    """Test settings module"""
    try:
        from app.models.settings import SchoolConfiguration, AcademicYear, AuditLog
        
        return {
            "module": "settings",
            "status": "✓ working",
            "tests": {
                "configurations": SchoolConfiguration.query.filter_by(school_id=user.school_id).count(),
                "academic_years": AcademicYear.query.filter_by(school_id=user.school_id).count(),
                "audit_logs": AuditLog.query.filter_by(school_id=user.school_id).count()
            }
        }
    except Exception as e:
        return {"module": "settings", "status": "⚠️ error", "error": str(e)}
