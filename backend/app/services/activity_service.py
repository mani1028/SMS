from app.models.activity import Activity, ActivityType
from app.models.student import Student
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class ActivityService:
    """Activity logging and reporting service"""
    
    @staticmethod
    def log_activity(school_id, user_id=None, activity_type=None, description=None, 
                     entity_type=None, entity_id=None, additional_data=None, ip_address=None):
        """Log an activity"""
        try:
            activity = Activity(
                school_id=school_id,
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                entity_type=entity_type,
                entity_id=entity_id,
                additional_data=additional_data,
                ip_address=ip_address
            )
            db.session.add(activity)
            db.session.commit()
            
            logger.info(f"Activity logged: {activity_type} for school {school_id}")
            return {"success": True, "activity_id": activity.id}
        except Exception as e:
            logger.error(f"Activity logging error: {str(e)}")
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_activity_log(school_id, page=1, limit=10):
        """Get activity log for school"""
        try:
            activities = Activity.query.filter_by(
                school_id=school_id
            ).order_by(Activity.created_at.desc()).paginate(page=page, per_page=limit)
            
            return {
                "success": True,
                "activities": [a.to_dict() for a in activities.items],
                "total": activities.total,
                "pages": activities.pages
            }
        except Exception as e:
            logger.error(f"Get activity error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_recent_students(school_id, limit=5):
        """Get recently added students"""
        try:
            students = Student.query.filter_by(
                school_id=school_id,
                is_active=True
            ).order_by(Student.created_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "students": [s.to_dict() for s in students]
            }
        except Exception as e:
            logger.error(f"Get recent students error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_enrollment_trends(school_id, days=30):
        """Get student enrollment trends for X days"""
        try:
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Get daily enrollment counts
            daily_data = db.session.query(
                func.date(Student.created_at).label('date'),
                func.count(Student.id).label('count')
            ).filter(
                Student.school_id == school_id,
                Student.created_at >= date_from
            ).group_by(func.date(Student.created_at)).order_by('date').all()
            
            # Format for chart
            trends = [
                {
                    "date": str(day[0]),
                    "admissions": day[1]
                }
                for day in daily_data
            ]
            
            return {
                "success": True,
                "trends": trends,
                "total_new": sum(t['admissions'] for t in trends)
            }
        except Exception as e:
            logger.error(f"Get enrollment trends error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_class_distribution(school_id):
        """Get student distribution by class"""
        try:
            class_data = db.session.query(
                Student.class_name,
                func.count(Student.id).label('count')
            ).filter(
                Student.school_id == school_id,
                Student.is_active == True
            ).group_by(Student.class_name).order_by('count').all()
            
            distribution = [
                {
                    "class_name": row[0],
                    "count": row[1]
                }
                for row in class_data
            ]
            
            return {
                "success": True,
                "distribution": distribution,
                "total_classes": len(distribution)
            }
        except Exception as e:
            logger.error(f"Get class distribution error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_monthly_stats(school_id):
        """Get monthly activity statistics"""
        try:
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Count new admissions this month
            new_students = Student.query.filter(
                Student.school_id == school_id,
                Student.created_at >= month_start,
                Student.is_active == True
            ).count()
            
            # Count activities
            total_activities = Activity.query.filter(
                Activity.school_id == school_id,
                Activity.created_at >= month_start
            ).count()
            
            # Count by activity type
            student_created = Activity.query.filter(
                Activity.school_id == school_id,
                Activity.activity_type == ActivityType.STUDENT_CREATED.value,
                Activity.created_at >= month_start
            ).count()
            
            student_updated = Activity.query.filter(
                Activity.school_id == school_id,
                Activity.activity_type == ActivityType.STUDENT_UPDATED.value,
                Activity.created_at >= month_start
            ).count()
            
            student_deleted = Activity.query.filter(
                Activity.school_id == school_id,
                Activity.activity_type == ActivityType.STUDENT_DELETED.value,
                Activity.created_at >= month_start
            ).count()
            
            return {
                "success": True,
                "new_admissions": new_students,
                "updates": student_updated,
                "deletions": student_deleted,
                "total_activities": total_activities
            }
        except Exception as e:
            logger.error(f"Get monthly stats error: {str(e)}")
            return {"success": False, "error": str(e)}
