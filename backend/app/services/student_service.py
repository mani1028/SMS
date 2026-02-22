from app.models.student import Student
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class StudentService:
    """Student CRUD service"""
    
    @staticmethod
    def create_student(school_id, name, admission_no, class_name, email=None, phone=None):
        """Create a new student"""
        try:
            # Check if admission_no already exists in school
            existing = Student.query.filter_by(
                school_id=school_id,
                admission_no=admission_no
            ).first()
            
            if existing:
                return {"success": False, "error": "Admission number already exists"}
            
            student = Student(
                school_id=school_id,
                name=name,
                admission_no=admission_no,
                class_name=class_name,
                email=email,
                phone=phone
            )
            
            db.session.add(student)
            db.session.commit()
            
            logger.info(f"Student created: {admission_no}")
            return {
                "success": True,
                "student": student.to_dict(),
                "message": "Student created successfully"
            }
        except Exception as e:
            logger.error(f"Student creation error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_students(school_id, page=1, limit=50):
        """Get all students for a school"""
        try:
            students = Student.query.filter_by(
                school_id=school_id,
                is_active=True
            ).paginate(page=page, per_page=limit)
            
            return {
                "success": True,
                "students": [s.to_dict() for s in students.items],
                "total": students.total,
                "pages": students.pages,
                "current_page": page
            }
        except Exception as e:
            logger.error(f"Get students error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_student(student_id, school_id):
        """Get a specific student"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            return {
                "success": True,
                "student": student.to_dict()
            }
        except Exception as e:
            logger.error(f"Get student error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_student(student_id, school_id, **kwargs):
        """Update a student"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            # Update allowed fields
            allowed_fields = ['name', 'class_name', 'email', 'phone', 'is_active']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(student, field, value)
            
            db.session.commit()
            
            logger.info(f"Student updated: {student_id}")
            return {
                "success": True,
                "student": student.to_dict(),
                "message": "Student updated successfully"
            }
        except Exception as e:
            logger.error(f"Student update error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_student(student_id, school_id):
        """Soft delete a student"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            student.is_active = False
            db.session.commit()
            
            logger.info(f"Student deleted: {student_id}")
            return {
                "success": True,
                "message": "Student deleted successfully"
            }
        except Exception as e:
            logger.error(f"Student delete error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
