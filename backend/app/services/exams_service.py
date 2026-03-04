"""
Examinations Service - CRUD and business logic for exams and grading
"""

from app.models.exams import ExamTerm, ExamSchedule, GradeBook, GradingScale, StudentRank
from app.extensions import db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class ExamService:
    """Service for exam management"""
    
    @staticmethod
    def create_exam_term(school_id, name, academic_year, start_date, end_date, declaration_date=None):
        """Create an exam term"""
        try:
            existing = ExamTerm.query.filter_by(
                school_id=school_id,
                name=name,
                academic_year=academic_year
            ).first()
            
            if existing:
                return {'success': False, 'error': 'Exam term already exists'}
            
            term = ExamTerm(
                school_id=school_id,
                name=name,
                academic_year=academic_year,
                start_date=start_date,
                end_date=end_date,
                declaration_date=declaration_date
            )
            db.session.add(term)
            db.session.commit()
            
            return {'success': True, 'exam_term': term.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating exam term: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_exam_terms(school_id, page=1, limit=50):
        """Get all exam terms"""
        try:
            query = ExamTerm.query.filter_by(school_id=school_id)
            total = query.count()
            pages = (total + limit - 1) // limit
            
            terms = query.offset((page - 1) * limit).limit(limit).order_by(ExamTerm.start_date.desc()).all()
            return {
                'success': True,
                'terms': [t.to_dict() for t in terms],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting exam terms: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_exam_schedule(school_id, exam_term_id, class_id, section_id, subject_id,
                            exam_date, start_time, end_time, room_number=None, max_marks=100):
        """Create exam schedule"""
        try:
            schedule = ExamSchedule(
                school_id=school_id,
                exam_term_id=exam_term_id,
                class_id=class_id,
                section_id=section_id,
                subject_id=subject_id,
                exam_date=exam_date,
                start_time=start_time,
                end_time=end_time,
                room_number=room_number,
                max_marks=max_marks
            )
            db.session.add(schedule)
            db.session.commit()
            
            return {'success': True, 'schedule': schedule.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating exam schedule: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_exam_schedule(school_id, exam_term_id=None, class_id=None, section_id=None):
        """Get exam schedule"""
        try:
            query = ExamSchedule.query.filter_by(school_id=school_id, is_active=True)
            
            if exam_term_id:
                query = query.filter_by(exam_term_id=exam_term_id)
            if class_id:
                query = query.filter_by(class_id=class_id)
            if section_id:
                query = query.filter_by(section_id=section_id)
            
            schedules = query.order_by(ExamSchedule.exam_date, ExamSchedule.start_time).all()
            return {'success': True, 'schedules': [s.to_dict() for s in schedules]}
        except Exception as e:
            logger.error(f"Error getting exam schedule: {str(e)}")
            return {'success': False, 'error': str(e)}


class GradeService:
    """Service for grading and marks entry"""
    
    @staticmethod
    def enter_marks(school_id, exam_schedule_id, student_id, subject_id, exam_term_id, obtained_marks, remarks=None):
        """Enter marks for a student"""
        try:
            # Check if entry already exists
            existing = GradeBook.query.filter_by(
                school_id=school_id,
                exam_schedule_id=exam_schedule_id,
                student_id=student_id,
                subject_id=subject_id
            ).first()
            
            if existing:
                existing.obtained_marks = obtained_marks
                existing.remarks = remarks
                existing.calculate_percentage()
                existing.determine_grade()
                db.session.commit()
                return {'success': True, 'grade': existing.to_dict(), 'message': 'Updated'}
            
            # Get max marks from schedule
            schedule = ExamSchedule.query.filter_by(id=exam_schedule_id, school_id=school_id).first()
            if not schedule:
                return {'success': False, 'error': 'Exam schedule not found'}
            
            grade = GradeBook(
                school_id=school_id,
                exam_term_id=exam_term_id,
                exam_schedule_id=exam_schedule_id,
                student_id=student_id,
                subject_id=subject_id,
                obtained_marks=obtained_marks,
                max_marks=schedule.max_marks,
                remarks=remarks
            )
            grade.calculate_percentage()
            grade.determine_grade()
            
            db.session.add(grade)
            db.session.commit()
            
            return {'success': True, 'grade': grade.to_dict(), 'message': 'Created'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error entering marks: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def bulk_enter_marks(school_id, exam_schedule_id, exam_term_id, subject_id, marks_data):
        """Bulk enter marks for multiple students"""
        try:
            results = []
            for record in marks_data:
                result = GradeService.enter_marks(
                    school_id=school_id,
                    exam_schedule_id=exam_schedule_id,
                    exam_term_id=exam_term_id,
                    student_id=record['student_id'],
                    subject_id=subject_id,
                    obtained_marks=record['obtained_marks'],
                    remarks=record.get('remarks')
                )
                results.append(result)
            
            success_count = sum(1 for r in results if r['success'])
            return {
                'success': True,
                'total': len(marks_data),
                'entered': success_count,
                'results': results
            }
        except Exception as e:
            logger.error(f"Error bulk entering marks: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_grades(school_id, student_id=None, exam_term_id=None, subject_id=None, page=1, limit=50):
        """Get grades/marks"""
        try:
            query = GradeBook.query.filter_by(school_id=school_id)
            
            if student_id:
                query = query.filter_by(student_id=student_id)
            if exam_term_id:
                query = query.filter_by(exam_term_id=exam_term_id)
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            grades = query.offset((page - 1) * limit).limit(limit).all()
            return {
                'success': True,
                'grades': [g.to_dict() for g in grades],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting grades: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_student_report(school_id, student_id, exam_term_id):
        """Get complete report card for a student"""
        try:
            grades = GradeBook.query.filter_by(
                school_id=school_id,
                student_id=student_id,
                exam_term_id=exam_term_id
            ).all()
            
            if not grades:
                return {'success': False, 'error': 'No grades found for this student'}
            
            total_marks = 0
            total_obtained = 0
            
            for grade in grades:
                total_marks += grade.max_marks
                if grade.obtained_marks:
                    total_obtained += grade.obtained_marks
            
            overall_percentage = (total_obtained / total_marks * 100) if total_marks > 0 else 0
            
            return {
                'success': True,
                'report': {
                    'student_id': student_id,
                    'exam_term_id': exam_term_id,
                    'grades': [g.to_dict() for g in grades],
                    'total_marks': total_marks,
                    'total_obtained': total_obtained,
                    'overall_percentage': round(overall_percentage, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def calculate_ranks(school_id, exam_term_id, class_id, section_id=None):
        """Calculate student rankings"""
        try:
            from app.models.exams import StudentRank
            
            # Get all students in class/section
            if section_id:
                query = GradeBook.query.filter(
                    GradeBook.school_id == school_id,
                    GradeBook.exam_term_id == exam_term_id
                )
            
            # Calculate average percentage for each student
            student_grades = db.session.query(
                GradeBook.student_id,
                func.avg(GradeBook.percentage).label('avg_percentage'),
                func.count(GradeBook.id).label('subject_count')
            ).filter_by(school_id=school_id, exam_term_id=exam_term_id).group_by(GradeBook.student_id).all()
            
            # Sort by percentage and assign ranks
            sorted_grades = sorted(student_grades, key=lambda x: x.avg_percentage or 0, reverse=True)
            
            # Clear previous ranks
            StudentRank.query.filter_by(
                school_id=school_id,
                exam_term_id=exam_term_id,
                class_id=class_id
            ).delete()
            
            # Insert new ranks
            for rank, (student_id, avg_percentage, subject_count) in enumerate(sorted_grades, 1):
                student_rank = StudentRank(
                    school_id=school_id,
                    exam_term_id=exam_term_id,
                    class_id=class_id,
                    section_id=section_id,
                    student_id=student_id,
                    rank=rank,
                    total_percentage=round(avg_percentage, 2),
                    total_students=len(sorted_grades)
                )
                db.session.add(student_rank)
            
            db.session.commit()
            
            return {'success': True, 'message': f'Ranks calculated for {len(sorted_grades)} students'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error calculating ranks: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_student_rank(school_id, exam_term_id, class_id, student_id):
        """Get student's rank"""
        try:
            rank = StudentRank.query.filter_by(
                school_id=school_id,
                exam_term_id=exam_term_id,
                class_id=class_id,
                student_id=student_id
            ).first()
            
            if not rank:
                return {'success': False, 'error': 'Rank not found'}
            
            return {'success': True, 'rank': rank.to_dict()}
        except Exception as e:
            logger.error(f"Error getting rank: {str(e)}")
            return {'success': False, 'error': str(e)}
