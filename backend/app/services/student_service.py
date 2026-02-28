from app.models.student import Student, AcademicHistory, StudentDocument, StudentStatus
from app.extensions import db
from datetime import datetime, date
from sqlalchemy import func, extract
import logging
import os

logger = logging.getLogger(__name__)


class StudentService:
    """Student CRUD service with advanced features"""
    
    @staticmethod
    def generate_admission_no(school_id, year=None):
        """Auto-generate unique admission number for a school"""
        try:
            if year is None:
                year = datetime.now().year
            
            # Get count of students in this school for this year
            count = Student.query.filter(
                Student.school_id == school_id,
                extract('year', Student.created_at) == year
            ).count()
            
            # Format: SCH{school_id}-{year}-{count+1:04d}
            admission_no = f"SCH{school_id}-{year}-{(count + 1):04d}"
            
            # Ensure uniqueness
            while Student.query.filter_by(school_id=school_id, admission_no=admission_no).first():
                count += 1
                admission_no = f"SCH{school_id}-{year}-{(count + 1):04d}"
            
            return admission_no
        except Exception as e:
            logger.error(f"Error generating admission number: {str(e)}")
            return None
    
    @staticmethod
    def generate_roll_no(school_id, class_name, section=None):
        """Auto-generate unique roll number within a class"""
        try:
            # Get count of students in this class
            query = Student.query.filter_by(
                school_id=school_id,
                class_name=class_name
            )
            
            if section:
                query = query.filter_by(section=section)
            
            count = query.count()
            
            # Format: Roll number as sequential number
            roll_no = f"{count + 1:03d}"
            
            return roll_no
        except Exception as e:
            logger.error(f"Error generating roll number: {str(e)}")
            return None
    
    @staticmethod
    def create_student(school_id, name, admission_no=None, class_name=None, **kwargs):
        """Create a new student with enhanced fields"""
        try:
            # Auto-generate admission number if not provided
            if not admission_no:
                admission_no = StudentService.generate_admission_no(school_id)
                if not admission_no:
                    return {"success": False, "error": "Failed to generate admission number"}
            
            # Check if admission_no already exists in school
            existing = Student.query.filter_by(
                school_id=school_id,
                admission_no=admission_no
            ).first()
            
            if existing:
                return {"success": False, "error": "Admission number already exists"}
            
            # Auto-generate roll number if class is provided
            roll_no = kwargs.get('roll_no')
            if class_name and not roll_no:
                section = kwargs.get('section')
                roll_no = StudentService.generate_roll_no(school_id, class_name, section)
            
            # Parse date fields if provided as strings
            dob = kwargs.get('dob')
            if dob and isinstance(dob, str):
                try:
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                except ValueError:
                    return {"success": False, "error": "Invalid date format for DOB. Use YYYY-MM-DD"}
            
            admission_date = kwargs.get('admission_date')
            if admission_date and isinstance(admission_date, str):
                try:
                    admission_date = datetime.strptime(admission_date, '%Y-%m-%d').date()
                except ValueError:
                    return {"success": False, "error": "Invalid date format for admission_date. Use YYYY-MM-DD"}
            elif not admission_date:
                admission_date = date.today()
            
            # Parse status if provided
            status = kwargs.get('status', 'active')
            if isinstance(status, str):
                try:
                    status = StudentStatus(status.lower())
                except ValueError:
                    status = StudentStatus.ACTIVE
            
            student = Student(
                school_id=school_id,
                name=name,
                admission_no=admission_no,
                roll_no=roll_no,
                class_name=class_name,
                section=kwargs.get('section'),
                email=kwargs.get('email'),
                phone=kwargs.get('phone'),
                gender=kwargs.get('gender'),
                dob=dob,
                blood_group=kwargs.get('blood_group'),
                address=kwargs.get('address'),
                previous_school=kwargs.get('previous_school'),
                admission_date=admission_date,
                status=status,
                parent_name=kwargs.get('parent_name'),
                parent_phone=kwargs.get('parent_phone'),
                parent_email=kwargs.get('parent_email')
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
    def update_student(student_id, school_id, **kwargs):
        """Update a student with enhanced fields"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            # Update allowed fields
            allowed_fields = [
                'name', 'class_name', 'section', 'roll_no', 'email', 'phone',
                'gender', 'dob', 'blood_group', 'address', 'previous_school',
                'admission_date', 'is_active', 'parent_name', 'parent_phone', 'parent_email'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    # Parse date fields if provided as strings
                    if field in ['dob', 'admission_date'] and value and isinstance(value, str):
                        try:
                            value = datetime.strptime(value, '%Y-%m-%d').date()
                        except ValueError:
                            continue
                    setattr(student, field, value)
            
            # Handle status separately
            if 'status' in kwargs:
                status = kwargs['status']
                if isinstance(status, str):
                    try:
                        student.status = StudentStatus(status.lower())
                    except ValueError:
                        pass
            
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
    def get_student_profile(student_id, school_id):
        """Get comprehensive student profile with all relations"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            # Get student with all relations
            profile = student.to_dict(include_relations=True)
            
            return {
                "success": True,
                "profile": profile
            }
        except Exception as e:
            logger.error(f"Get student profile error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def promote_students(school_id, student_ids, new_class, new_section=None, academic_year=None):
        """
        Bulk promote students to next class and archive current year data
        
        Args:
            school_id: School ID
            student_ids: List of student IDs to promote
            new_class: New class name
            new_section: New section (optional)
            academic_year: Academic year for archiving (e.g., "2025-2026")
        """
        try:
            if not academic_year:
                current_year = datetime.now().year
                academic_year = f"{current_year}-{current_year + 1}"
            
            promoted_count = 0
            failed_students = []
            
            for student_id in student_ids:
                student = Student.query.filter_by(
                    id=student_id,
                    school_id=school_id
                ).first()
                
                if not student:
                    failed_students.append({"id": student_id, "reason": "Student not found"})
                    continue
                
                try:
                    # Archive current academic data
                    academic_record = AcademicHistory(
                        school_id=school_id,
                        student_id=student.id,
                        class_name=student.class_name,
                        section=student.section,
                        academic_year=academic_year,
                        roll_no=student.roll_no,
                        final_result="Promoted"
                    )
                    db.session.add(academic_record)
                    
                    # Update student to new class
                    student.class_name = new_class
                    student.section = new_section
                    
                    # Regenerate roll number for new class
                    new_roll = StudentService.generate_roll_no(school_id, new_class, new_section)
                    student.roll_no = new_roll
                    
                    promoted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error promoting student {student_id}: {str(e)}")
                    failed_students.append({"id": student_id, "reason": str(e)})
            
            db.session.commit()
            
            logger.info(f"Promoted {promoted_count} students")
            return {
                "success": True,
                "promoted_count": promoted_count,
                "failed_students": failed_students,
                "message": f"Successfully promoted {promoted_count} student(s)"
            }
            
        except Exception as e:
            logger.error(f"Bulk promotion error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def generate_tc(student_id, school_id, reason="", remarks=""):
        """
        Generate Transfer Certificate data and mark student as transferred
        
        Args:
            student_id: Student ID
            school_id: School ID
            reason: Reason for transfer
            remarks: Additional remarks
        """
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            # Get academic history
            history = AcademicHistory.query.filter_by(
                student_id=student_id,
                school_id=school_id
            ).order_by(AcademicHistory.created_at.desc()).all()
            
            # Update student status
            student.status = StudentStatus.TRANSFERRED
            student.is_active = False
            
            db.session.commit()
            
            # Prepare TC data
            tc_data = {
                "student_id": student.id,
                "student_name": student.name,
                "admission_no": student.admission_no,
                "admission_date": student.admission_date.isoformat() if student.admission_date else None,
                "dob": student.dob.isoformat() if student.dob else None,
                "class_name": student.class_name,
                "section": student.section,
                "roll_no": student.roll_no,
                "gender": student.gender,
                "blood_group": student.blood_group,
                "parent_name": student.parent_name,
                "previous_school": student.previous_school,
                "tc_issue_date": datetime.now().isoformat(),
                "reason": reason,
                "remarks": remarks,
                "academic_history": [h.to_dict() for h in history],
                "conduct": "Good",  # Can be customized
                "character": "Good"  # Can be customized
            }
            
            logger.info(f"TC generated for student: {student_id}")
            return {
                "success": True,
                "tc_data": tc_data,
                "message": "Transfer Certificate generated successfully"
            }
            
        except Exception as e:
            logger.error(f"TC generation error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def change_student_status(student_id, school_id, new_status):
        """
        Change student status (active, inactive, transferred, graduated)
        
        Args:
            student_id: Student ID
            school_id: School ID
            new_status: New status (string or StudentStatus enum)
        """
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            # Parse status
            if isinstance(new_status, str):
                try:
                    new_status = StudentStatus(new_status.lower())
                except ValueError:
                    return {"success": False, "error": f"Invalid status: {new_status}"}
            
            student.status = new_status
            
            # Update is_active based on status
            if new_status in [StudentStatus.TRANSFERRED, StudentStatus.GRADUATED]:
                student.is_active = False
            elif new_status == StudentStatus.ACTIVE:
                student.is_active = True
            
            db.session.commit()
            
            logger.info(f"Student {student_id} status changed to {new_status.value}")
            return {
                "success": True,
                "student": student.to_dict(),
                "message": f"Student status updated to {new_status.value}"
            }
            
        except Exception as e:
            logger.error(f"Status change error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def add_academic_record(school_id, student_id, class_name, academic_year, **kwargs):
        """Add academic history record for a student"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            record = AcademicHistory(
                school_id=school_id,
                student_id=student_id,
                class_name=class_name,
                academic_year=academic_year,
                section=kwargs.get('section'),
                roll_no=kwargs.get('roll_no'),
                result_data=kwargs.get('result_data'),
                attendance_percentage=kwargs.get('attendance_percentage'),
                final_result=kwargs.get('final_result'),
                remarks=kwargs.get('remarks')
            )
            
            db.session.add(record)
            db.session.commit()
            
            logger.info(f"Academic record added for student: {student_id}")
            return {
                "success": True,
                "record": record.to_dict(),
                "message": "Academic record added successfully"
            }
            
        except Exception as e:
            logger.error(f"Add academic record error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def add_document(school_id, student_id, doc_type, doc_name, file_path, **kwargs):
        """Add document metadata for a student"""
        try:
            student = Student.query.filter_by(
                id=student_id,
                school_id=school_id
            ).first()
            
            if not student:
                return {"success": False, "error": "Student not found", "status_code": 404}
            
            document = StudentDocument(
                school_id=school_id,
                student_id=student_id,
                doc_type=doc_type,
                doc_name=doc_name,
                file_path=file_path,
                file_size=kwargs.get('file_size'),
                mime_type=kwargs.get('mime_type')
            )
            
            db.session.add(document)
            db.session.commit()
            
            logger.info(f"Document added for student: {student_id}")
            return {
                "success": True,
                "document": document.to_dict(),
                "message": "Document added successfully"
            }
            
        except Exception as e:
            logger.error(f"Add document error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_students(school_id, page=1, limit=50, status=None, class_name=None):
        """Get all students for a school with filtering options"""
        try:
            query = Student.query.filter_by(school_id=school_id)
            
            # Filter by status if provided
            if status:
                if isinstance(status, str):
                    try:
                        status_enum = StudentStatus(status.lower())
                        query = query.filter_by(status=status_enum)
                    except ValueError:
                        pass
            else:
                # Default to active students only
                query = query.filter_by(is_active=True)
            
            # Filter by class if provided
            if class_name:
                query = query.filter_by(class_name=class_name)
            
            # Order by admission number
            query = query.order_by(Student.admission_no)
            
            students = query.paginate(page=page, per_page=limit, error_out=False)
            
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
