from app.models.student import Student
from app.models.user import User
from app.models.activity import Activity, ActivityType
from app.services.activity_service import ActivityService
from app.extensions import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    """Dashboard statistics service"""
    
    @staticmethod
    def get_stats(school_id):
        """Get summary statistics for the school dashboard"""
        try:
            # 1. Total active students
            total_students = Student.query.filter_by(school_id=school_id, is_active=True).count()
            
            # 2. Total active users (Admin, Teachers, etc.)
            active_users = User.query.filter_by(school_id=school_id, is_active=True).count()
            
            # 3. Total unique classes
            total_classes = db.session.query(Student.class_name).filter_by(
                school_id=school_id, is_active=True
            ).distinct().count()
            
            return {
                "success": True,
                "stats": {
                    "total_students": total_students,
                    "active_users": active_users,
                    "total_classes": total_classes
                }
            }
        except Exception as e:
            logger.error(f"Dashboard stats error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_full_dashboard_data(school_id):
        """Get comprehensive dashboard data"""
        try:
            # Get base stats
            stats_result = DashboardService.get_stats(school_id)
            
            # Get monthly stats
            monthly_result = ActivityService.get_monthly_stats(school_id)
            
            # Get recent students
            recent_result = ActivityService.get_recent_students(school_id, limit=5)
            
            # Get enrollment trends
            trends_result = ActivityService.get_enrollment_trends(school_id, days=30)
            
            # Get class distribution
            class_result = ActivityService.get_class_distribution(school_id)
            
            # Get recent activity log
            activity_result = ActivityService.get_activity_log(school_id, page=1, limit=10)
            
            if all(r.get('success') for r in [stats_result, monthly_result, recent_result, 
                                               trends_result, class_result, activity_result]):
                return {
                    "success": True,
                    "data": {
                        "stats": stats_result['stats'],
                        "monthly": monthly_result,
                        "recent_students": recent_result.get('students', []),
                        "enrollment_trends": trends_result.get('trends', []),
                        "class_distribution": class_result.get('distribution', []),
                        "activity_log": activity_result.get('activities', []),
                        "total_activities": activity_result.get('total', 0)
                    }
                }
            else:
                return {"success": False, "error": "Error fetching dashboard data"}
        
        except Exception as e:
            logger.error(f"Full dashboard error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def seed_sample_activities(school_id, user_id):
        """Create sample activity records for demonstration"""
        try:
            # Sample activity data
            sample_activities = [
                {
                    "activity_type": ActivityType.STUDENT_CREATED.value,
                    "description": "Created student: Rajesh Kumar",
                    "entity_type": "student",
                    "entity_id": 1,
                    "hours_ago": 2
                },
                {
                    "activity_type": ActivityType.STUDENT_UPDATED.value,
                    "description": "Updated student: Priya Singh - Changed class to 12th",
                    "entity_type": "student",
                    "entity_id": 2,
                    "hours_ago": 4
                },
                {
                    "activity_type": ActivityType.STUDENT_CREATED.value,
                    "description": "Created student: Amit Patel",
                    "entity_type": "student",
                    "entity_id": 3,
                    "hours_ago": 6
                },
                {
                    "activity_type": ActivityType.USER_LOGGED_IN.value,
                    "description": "User logged in",
                    "entity_type": "user",
                    "entity_id": user_id,
                    "hours_ago": 8
                },
                {
                    "activity_type": ActivityType.STUDENT_CREATED.value,
                    "description": "Created student: Neha Sharma",
                    "entity_type": "student",
                    "entity_id": 4,
                    "hours_ago": 12
                },
                {
                    "activity_type": ActivityType.STUDENT_UPDATED.value,
                    "description": "Updated student: Vikram - Email changed",
                    "entity_type": "student",
                    "entity_id": 5,
                    "hours_ago": 18
                },
                {
                    "activity_type": ActivityType.STUDENT_DELETED.value,
                    "description": "Deleted student: Removed from 10th class",
                    "entity_type": "student",
                    "entity_id": 6,
                    "hours_ago": 24
                },
                {
                    "activity_type": ActivityType.STUDENT_CREATED.value,
                    "description": "Created student: Aisha Khan",
                    "entity_type": "student",
                    "entity_id": 7,
                    "hours_ago": 36
                },
            ]
            
            # Create activities with timestamps in the past
            created_count = 0
            for activity_data in sample_activities:
                hours_ago = activity_data.pop('hours_ago')
                created_at = datetime.utcnow() - timedelta(hours=hours_ago)
                
                activity = Activity(
                    school_id=school_id,
                    user_id=user_id,
                    activity_type=activity_data['activity_type'],
                    description=activity_data['description'],
                    entity_type=activity_data['entity_type'],
                    entity_id=activity_data['entity_id'],
                    created_at=created_at
                )
                db.session.add(activity)
                created_count += 1
            
            db.session.commit()
            logger.info(f"Created {created_count} sample activities for school {school_id}")
            
            return {
                "success": True,
                "message": f"Successfully created {created_count} sample activities",
                "count": created_count
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Seed activities error: {str(e)}")
            return {"success": False, "error": str(e)}