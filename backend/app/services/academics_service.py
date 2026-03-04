"""
Academic Service - CRUD and business logic for academics
"""

from app.models.academics import Class, Section, Subject, ClassTeacherAssignment, TimetableSlot
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class AcademicsService:
    """Service for academics management"""
    
    # ==================== CLASS MANAGEMENT ====================
    
    @staticmethod
    def create_class(school_id, name, numeric_class, description=None):
        """Create a new class"""
        try:
            # Check if class already exists
            existing = Class.query.filter_by(school_id=school_id, name=name).first()
            if existing:
                return {'success': False, 'error': f'Class "{name}" already exists'}
            
            class_obj = Class(
                school_id=school_id,
                name=name,
                numeric_class=numeric_class,
                description=description
            )
            db.session.add(class_obj)
            db.session.commit()
            
            return {'success': True, 'class': class_obj.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating class: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_classes(school_id, page=1, limit=50):
        """Get all classes for a school"""
        try:
            query = Class.query.filter_by(school_id=school_id, is_active=True)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            classes = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'classes': [c.to_dict() for c in classes],
                'total': total,
                'pages': pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"Error getting classes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_class(school_id, class_id):
        """Get class by ID"""
        try:
            class_obj = Class.query.filter_by(id=class_id, school_id=school_id).first()
            if not class_obj:
                return {'success': False, 'error': 'Class not found'}
            return {'success': True, 'class': class_obj.to_dict()}
        except Exception as e:
            logger.error(f"Error getting class: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_class(school_id, class_id, **kwargs):
        """Update class details"""
        try:
            class_obj = Class.query.filter_by(id=class_id, school_id=school_id).first()
            if not class_obj:
                return {'success': False, 'error': 'Class not found'}
            
            allowed_fields = ['name', 'description', 'is_active']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(class_obj, field, value)
            
            db.session.commit()
            return {'success': True, 'class': class_obj.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating class: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== SECTION MANAGEMENT ====================
    
    @staticmethod
    def create_section(school_id, class_id, name, capacity=50, class_teacher_id=None):
        """Create a section within a class"""
        try:
            # Verify class exists
            class_obj = Class.query.filter_by(id=class_id, school_id=school_id).first()
            if not class_obj:
                return {'success': False, 'error': 'Class not found'}
            
            # Check if section already exists
            existing = Section.query.filter_by(school_id=school_id, class_id=class_id, name=name).first()
            if existing:
                return {'success': False, 'error': f'Section "{name}" already exists in this class'}
            
            section = Section(
                school_id=school_id,
                class_id=class_id,
                name=name,
                capacity=capacity,
                class_teacher_id=class_teacher_id
            )
            db.session.add(section)
            db.session.commit()
            
            return {'success': True, 'section': section.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating section: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_sections_by_class(school_id, class_id):
        """Get all sections in a class"""
        try:
            sections = Section.query.filter_by(school_id=school_id, class_id=class_id, is_active=True).all()
            return {'success': True, 'sections': [s.to_dict() for s in sections]}
        except Exception as e:
            logger.error(f"Error getting sections: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== SUBJECT MANAGEMENT ====================
    
    @staticmethod
    def create_subject(school_id, name, code, description=None):
        """Create a subject"""
        try:
            # Check if subject code already exists
            existing = Subject.query.filter_by(school_id=school_id, code=code).first()
            if existing:
                return {'success': False, 'error': f'Subject code "{code}" already exists'}
            
            subject = Subject(
                school_id=school_id,
                name=name,
                code=code,
                description=description
            )
            db.session.add(subject)
            db.session.commit()
            
            return {'success': True, 'subject': subject.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating subject: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_subjects(school_id, page=1, limit=50):
        """Get all subjects for a school"""
        try:
            query = Subject.query.filter_by(school_id=school_id, is_active=True)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            subjects = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'subjects': [s.to_dict() for s in subjects],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting subjects: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== TEACHER ASSIGNMENT ====================
    
    @staticmethod
    def assign_teacher(school_id, class_id, section_id, teacher_id, subject_id):
        """Assign teacher to class/section for a subject"""
        try:
            # Verify all entities exist
            class_obj = Class.query.filter_by(id=class_id, school_id=school_id).first()
            if not class_obj:
                return {'success': False, 'error': 'Class not found'}
            
            if section_id:
                section = Section.query.filter_by(id=section_id, school_id=school_id).first()
                if not section:
                    return {'success': False, 'error': 'Section not found'}
            
            subject = Subject.query.filter_by(id=subject_id, school_id=school_id).first()
            if not subject:
                return {'success': False, 'error': 'Subject not found'}
            
            # Check duplicate assignment
            existing = ClassTeacherAssignment.query.filter_by(
                school_id=school_id,
                class_id=class_id,
                section_id=section_id,
                teacher_id=teacher_id,
                subject_id=subject_id
            ).first()
            if existing:
                return {'success': False, 'error': 'Teacher already assigned to this class/section/subject'}
            
            assignment = ClassTeacherAssignment(
                school_id=school_id,
                class_id=class_id,
                section_id=section_id,
                teacher_id=teacher_id,
                subject_id=subject_id
            )
            db.session.add(assignment)
            db.session.commit()
            
            return {'success': True, 'assignment': assignment.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning teacher: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_teacher_assignments(school_id, teacher_id=None, class_id=None):
        """Get teacher assignments"""
        try:
            query = ClassTeacherAssignment.query.filter_by(school_id=school_id, is_active=True)
            
            if teacher_id:
                query = query.filter_by(teacher_id=teacher_id)
            if class_id:
                query = query.filter_by(class_id=class_id)
            
            assignments = query.all()
            return {'success': True, 'assignments': [a.to_dict() for a in assignments]}
        except Exception as e:
            logger.error(f"Error getting assignments: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== TIMETABLE MANAGEMENT ====================
    
    @staticmethod
    def create_timetable_slot(school_id, class_id, section_id, teacher_id, subject_id, 
                             day_of_week, start_time, end_time, room_number=None):
        """Create timetable slot with conflict detection"""
        try:
            # Check for conflicts
            if TimetableSlot.check_conflict(school_id, teacher_id, day_of_week, start_time, end_time):
                return {'success': False, 'error': 'Teacher conflict: Already assigned at this time'}
            
            slot = TimetableSlot(
                school_id=school_id,
                class_id=class_id,
                section_id=section_id,
                teacher_id=teacher_id,
                subject_id=subject_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room_number=room_number
            )
            db.session.add(slot)
            db.session.commit()
            
            return {'success': True, 'slot': slot.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating timetable slot: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_timetable(school_id, class_id=None, section_id=None, teacher_id=None, day=None):
        """Get timetable slots with optional filters"""
        try:
            query = TimetableSlot.query.filter_by(school_id=school_id, is_active=True)
            
            if class_id:
                query = query.filter_by(class_id=class_id)
            if section_id:
                query = query.filter_by(section_id=section_id)
            if teacher_id:
                query = query.filter_by(teacher_id=teacher_id)
            if day:
                query = query.filter_by(day_of_week=day)
            
            slots = query.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
            return {'success': True, 'slots': [s.to_dict() for s in slots]}
        except Exception as e:
            logger.error(f"Error getting timetable: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_timetable_slot(school_id, slot_id, **kwargs):
        """Update timetable slot"""
        try:
            slot = TimetableSlot.query.filter_by(id=slot_id, school_id=school_id).first()
            if not slot:
                return {'success': False, 'error': 'Timetable slot not found'}
            
            # If time is being changed, check for conflicts
            if 'start_time' in kwargs or 'end_time' in kwargs:
                start_time = kwargs.get('start_time', slot.start_time)
                end_time = kwargs.get('end_time', slot.end_time)
                if TimetableSlot.check_conflict(school_id, slot.teacher_id, slot.day_of_week, start_time, end_time, slot.id):
                    return {'success': False, 'error': 'Conflict with existing timetable'}
            
            allowed_fields = ['teacher_id', 'subject_id', 'start_time', 'end_time', 'room_number', 'is_active']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(slot, field, value)
            
            db.session.commit()
            return {'success': True, 'slot': slot.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating timetable slot: {str(e)}")
            return {'success': False, 'error': str(e)}
