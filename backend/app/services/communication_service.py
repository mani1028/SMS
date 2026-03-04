"""
Communication Service - CRUD and business logic for notices, events, homework
"""

from app.models.communication import (Notice, NoticeView, Event, Homework, HomeworkSubmission,
                                      Announcement, Document)
from app.extensions import db
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class NoticeService:
    """Service for notice management"""
    
    @staticmethod
    def create_notice(school_id, title, content, notice_type, published_by_id,
                     visibility='all', target_class_id=None, attachment_url=None):
        """Create a notice"""
        try:
            notice = Notice(
                school_id=school_id,
                title=title,
                content=content,
                notice_type=notice_type,
                published_by_id=published_by_id,
                visibility=visibility,
                target_class_id=target_class_id,
                attachment_url=attachment_url,
                published_date=datetime.utcnow()
            )
            db.session.add(notice)
            db.session.commit()
            
            return {'success': True, 'notice': notice.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating notice: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_notices(school_id, user_id=None, page=1, limit=50):
        """Get notices visible to user"""
        try:
            query = Notice.query.filter_by(school_id=school_id, is_active=True)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            notices = query.offset((page - 1) * limit).limit(limit).order_by(
                Notice.published_date.desc()
            ).all()
            
            return {
                'success': True,
                'notices': [n.to_dict() for n in notices],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting notices: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def mark_notice_viewed(school_id, notice_id, user_id):
        """Mark notice as viewed by user"""
        try:
            # Check if already viewed
            existing = NoticeView.query.filter_by(
                school_id=school_id,
                notice_id=notice_id,
                user_id=user_id
            ).first()
            
            if not existing:
                view = NoticeView(
                    school_id=school_id,
                    notice_id=notice_id,
                    user_id=user_id,
                    viewed_at=datetime.utcnow()
                )
                db.session.add(view)
                db.session.commit()
            
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking view: {str(e)}")
            return {'success': False, 'error': str(e)}


class EventService:
    """Service for event management"""
    
    @staticmethod
    def create_event(school_id, title, event_date, event_type, created_by_id,
                    description=None, start_time=None, end_time=None, location=None,
                    is_public=True, attachment_url=None):
        """Create an event"""
        try:
            event = Event(
                school_id=school_id,
                title=title,
                description=description,
                event_date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
                event_type=event_type,
                created_by_id=created_by_id,
                is_public=is_public,
                attachment_url=attachment_url
            )
            db.session.add(event)
            db.session.commit()
            
            return {'success': True, 'event': event.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating event: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_events(school_id, from_date=None, to_date=None, page=1, limit=50):
        """Get school events"""
        try:
            query = Event.query.filter_by(school_id=school_id)
            
            if from_date:
                query = query.filter(Event.event_date >= from_date)
            if to_date:
                query = query.filter(Event.event_date <= to_date)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            events = query.offset((page - 1) * limit).limit(limit).order_by(
                Event.event_date.asc()
            ).all()
            
            return {
                'success': True,
                'events': [e.to_dict() for e in events],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting events: {str(e)}")
            return {'success': False, 'error': str(e)}


class HomeworkService:
    """Service for homework management"""
    
    @staticmethod
    def create_homework(school_id, class_id, section_id, subject_id, teacher_id,
                       title, description, due_date, attachment_url=None, marks=None):
        """Create homework assignment"""
        try:
            homework = Homework(
                school_id=school_id,
                class_id=class_id,
                section_id=section_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                title=title,
                description=description,
                due_date=due_date,
                attachment_url=attachment_url,
                marks=marks
            )
            db.session.add(homework)
            db.session.commit()
            
            return {'success': True, 'homework': homework.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating homework: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_homework(school_id, class_id=None, section_id=None, subject_id=None, page=1, limit=50):
        """Get homework assignments"""
        try:
            query = Homework.query.filter_by(school_id=school_id)
            
            if class_id:
                query = query.filter_by(class_id=class_id)
            if section_id:
                query = query.filter_by(section_id=section_id)
            if subject_id:
                query = query.filter_by(subject_id=subject_id)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            homework = query.offset((page - 1) * limit).limit(limit).order_by(
                Homework.due_date.asc()
            ).all()
            
            return {
                'success': True,
                'homework': [h.to_dict() for h in homework],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting homework: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def submit_homework(school_id, homework_id, student_id, file_url):
        """Submit homework"""
        try:
            homework = Homework.query.filter_by(id=homework_id, school_id=school_id).first()
            if not homework:
                return {'success': False, 'error': 'Homework not found'}
            
            # Check if already submitted
            existing = HomeworkSubmission.query.filter_by(
                school_id=school_id,
                homework_id=homework_id,
                student_id=student_id
            ).first()
            
            if existing:
                existing.file_url = file_url
                existing.submission_date = datetime.utcnow()
                db.session.commit()
                return {'success': True, 'submission': existing.to_dict(), 'message': 'Updated'}
            
            submission = HomeworkSubmission(
                school_id=school_id,
                homework_id=homework_id,
                student_id=student_id,
                file_url=file_url,
                is_late=date.today() > homework.due_date
            )
            db.session.add(submission)
            db.session.commit()
            
            return {'success': True, 'submission': submission.to_dict(), 'message': 'Submitted'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting homework: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def evaluate_submission(school_id, submission_id, marks_obtained, feedback, teacher_id):
        """Evaluate homework submission"""
        try:
            submission = HomeworkSubmission.query.filter_by(
                id=submission_id,
                school_id=school_id
            ).first()
            
            if not submission:
                return {'success': False, 'error': 'Submission not found'}
            
            submission.marks_obtained = marks_obtained
            submission.feedback = feedback
            submission.is_evaluated = True
            submission.evaluated_on = datetime.utcnow()
            
            db.session.commit()
            
            return {'success': True, 'submission': submission.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error evaluating submission: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_submissions(school_id, homework_id=None, student_id=None, page=1, limit=50):
        """Get homework submissions"""
        try:
            query = HomeworkSubmission.query.filter_by(school_id=school_id)
            
            if homework_id:
                query = query.filter_by(homework_id=homework_id)
            if student_id:
                query = query.filter_by(student_id=student_id)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            submissions = query.offset((page - 1) * limit).limit(limit).order_by(
                HomeworkSubmission.submission_date.desc()
            ).all()
            
            return {
                'success': True,
                'submissions': [s.to_dict() for s in submissions],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting submissions: {str(e)}")
            return {'success': False, 'error': str(e)}


class AnnouncementService:
    """Service for announcements"""
    
    @staticmethod
    def create_announcement(school_id, title, content, announced_by_id, priority='normal', expire_date=None):
        """Create an announcement"""
        try:
            announcement = Announcement(
                school_id=school_id,
                title=title,
                content=content,
                announced_by_id=announced_by_id,
                announcement_date=datetime.utcnow(),
                expire_date=expire_date,
                priority=priority
            )
            db.session.add(announcement)
            db.session.commit()
            
            return {'success': True, 'announcement': announcement.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating announcement: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_announcements(school_id, page=1, limit=50):
        """Get active announcements"""
        try:
            now = datetime.utcnow()
            query = Announcement.query.filter(
                Announcement.school_id == school_id,
                db.or_(
                    Announcement.expire_date == None,
                    Announcement.expire_date > now
                )
            )
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            announcements = query.offset((page - 1) * limit).limit(limit).order_by(
                Announcement.priority.desc(),
                Announcement.announcement_date.desc()
            ).all()
            
            return {
                'success': True,
                'announcements': [a.to_dict() for a in announcements],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting announcements: {str(e)}")
            return {'success': False, 'error': str(e)}


class DocumentService:
    """Service for document management"""
    
    @staticmethod
    def upload_document(school_id, title, document_type, file_url, uploaded_by_id, 
                       related_user_id=None, is_public=False):
        """Upload document"""
        try:
            document = Document(
                school_id=school_id,
                title=title,
                document_type=document_type,
                file_url=file_url,
                uploaded_by_id=uploaded_by_id,
                uploaded_date=datetime.utcnow(),
                related_user_id=related_user_id,
                is_public=is_public
            )
            db.session.add(document)
            db.session.commit()
            
            return {'success': True, 'document': document.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading document: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_documents(school_id, document_type=None, is_public=False, page=1, limit=50):
        """Get documents"""
        try:
            query = Document.query.filter_by(school_id=school_id)
            
            if is_public:
                query = query.filter_by(is_public=True)
            
            if document_type:
                query = query.filter_by(document_type=document_type)
            
            total = query.count()
            pages = (total + limit - 1) // limit
            
            documents = query.offset((page - 1) * limit).limit(limit).order_by(
                Document.uploaded_date.desc()
            ).all()
            
            return {
                'success': True,
                'documents': [d.to_dict() for d in documents],
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return {'success': False, 'error': str(e)}
