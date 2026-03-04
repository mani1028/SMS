"""
Platform Management Service
Business logic for managing schools, subscriptions, and billing
"""
from app.models.school import School
from app.models.user import User
from app.models.role import Role
from app.models.billing import Plan, Subscription, Billing, SchoolUsage
from app.models.student import Student
from app.models.staff import Staff
from app.extensions import db
from app.services.activity_service import ActivityService
from app.models.activity import ActivityType
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class PlatformService:
    """Service for platform-wide admin operations"""
    
    @staticmethod
    def list_schools(page=1, per_page=20, status=None, search=None):
        """List all schools with pagination and enhanced details"""
        try:
            query = School.query
            
            # Filter by status if provided
            if status:
                query = query.filter_by(subscription_status=status)
            
            # Search by name or email
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    db.or_(
                        School.name.ilike(search_term),
                        School.email.ilike(search_term)
                    )
                )
            
            # Pagination
            total = query.count()
            pages = (total + per_page - 1) // per_page
            schools = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Enhance each school with subscription and user info
            schools_data = []
            for school in schools:
                school_dict = school.to_dict()
                
                # Get subscription plan name
                subscription = Subscription.query.filter_by(school_id=school.id).first()
                if subscription and subscription.plan:
                    school_dict['plan_name'] = subscription.plan.name
                    school_dict['plan_id'] = subscription.plan.id
                else:
                    school_dict['plan_name'] = 'N/A'
                    school_dict['plan_id'] = None
                
                # Get user count
                user_count = User.query.filter_by(school_id=school.id).count()
                school_dict['user_count'] = user_count
                
                schools_data.append(school_dict)
            
            return {
                'schools': schools_data,
                'total': total,
                'pages': pages,
                'current_page': page,
                'per_page': per_page
            }
        except Exception as e:
            logger.error(f"Error listing schools: {str(e)}")
            raise
    
    @staticmethod
    def get_school_details(school_id):
        """Get detailed info about a school"""
        try:
            school = School.query.get(school_id)
            if not school:
                raise ValueError("School not found")
            
            # Get subscription info
            subscription = Subscription.query.filter_by(school_id=school_id).first()
            
            # Get usage
            usage = SchoolUsage.query.filter_by(school_id=school_id).first()
            
            # Get admin user
            admin = User.query.filter_by(school_id=school_id, role_id=None).first()
            
            return {
                'school': school.to_dict(),
                'subscription': subscription.to_dict() if subscription else None,
                'usage': usage.to_dict() if usage else None,
                'admin': admin.to_dict() if admin else None,
                'students_count': Student.query.filter_by(school_id=school_id).count(),
                'staff_count': Staff.query.filter_by(school_id=school_id).count(),
                'users_count': User.query.filter_by(school_id=school_id).count()
            }
        except Exception as e:
            logger.error(f"Error getting school details: {str(e)}")
            raise
    
    @staticmethod
    def create_school(school_name, school_email, admin_name, admin_email, admin_password, plan_id=1):
        """Create a new school with admin user"""
        try:
            # Check if school already exists
            existing_school = School.query.filter_by(email=school_email).first()
            if existing_school:
                return {'success': False, 'error': 'School email already exists'}
            
            # Check if admin email is already used as super admin
            existing_user = User.query.filter_by(email=admin_email).first()
            if existing_user:
                return {'success': False, 'error': 'Admin email already exists'}
            
            # Create school
            school = School(
                name=school_name,
                email=school_email,
                subscription_status='trial'
            )
            db.session.add(school)
            db.session.flush()  # Get school.id without committing
            
            # Create admin user
            admin_user = User(
                school_id=school.id,
                name=admin_name,
                email=admin_email,
                is_active=True,
                is_super_admin=False
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.flush()
            
            # Create default admin role for school
            admin_role = Role(
                school_id=school.id,
                name='Admin',
                description='School administrator'
            )
            db.session.add(admin_role)
            admin_user.role_id = admin_role.id
            db.session.flush()
            
            # Create default trial subscription
            plan = Plan.query.get(plan_id)
            if not plan:
                plan = Plan.query.filter_by(name='Free').first()
            
            if plan:
                subscription = Subscription(
                    school_id=school.id,
                    plan_id=plan.id,
                    status='trial',
                    is_trial=True,
                    trial_start_date=datetime.utcnow(),
                    trial_end_date=datetime.utcnow() + timedelta(days=14)
                )
                db.session.add(subscription)
            
            # Create usage tracker
            usage = SchoolUsage(school_id=school.id)
            db.session.add(usage)
            
            # Commit all
            db.session.commit()
            
            # Log activity
            ActivityService.log_activity(
                school_id=school.id,
                user_id=admin_user.id,
                activity_type=ActivityType.SCHOOL_CREATED,
                description=f"School '{school_name}' created by platform admin"
            )
            
            return {
                'success': True,
                'message': 'School created successfully',
                'school': school.to_dict()
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating school: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_school_status(school_id, status, reason=None):
        """Update school subscription status"""
        try:
            school = School.query.get(school_id)
            if not school:
                return {'success': False, 'error': 'School not found'}
            
            old_status = school.subscription_status
            school.subscription_status = status
            db.session.commit()
            
            logger.info(f"School {school_id} status changed from {old_status} to {status}")
            
            return {
                'success': True,
                'message': f'School status updated to {status}',
                'school': school.to_dict()
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating school status: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_school(school_id):
        """Delete a school and all its data (cascade)"""
        try:
            school = School.query.get(school_id)
            if not school:
                return {'success': False, 'error': 'School not found'}
            
            school_name = school.name
            db.session.delete(school)
            db.session.commit()
            
            logger.warning(f"School {school_id} ({school_name}) deleted with all data")
            
            return {
                'success': True,
                'message': f'School {school_name} deleted successfully'
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting school: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_plans():
        """Get all subscription plans"""
        try:
            plans = Plan.query.filter_by(is_active=True).order_by(Plan.display_order).all()
            return [plan.to_dict() for plan in plans]
        except Exception as e:
            logger.error(f"Error listing plans: {str(e)}")
            raise
    
    @staticmethod
    def get_school_subscription(school_id):
        """Get a school's subscription"""
        try:
            subscription = Subscription.query.filter_by(school_id=school_id).first()
            if not subscription:
                raise ValueError("Subscription not found")
            
            return subscription.to_dict()
        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            raise
    
    @staticmethod
    def upgrade_subscription(school_id, plan_id):
        """Upgrade or change a school's subscription plan"""
        try:
            subscription = Subscription.query.filter_by(school_id=school_id).first()
            if not subscription:
                raise ValueError("Subscription not found")
            
            plan = Plan.query.get(plan_id)
            if not plan:
                raise ValueError("Plan not found")
            
            subscription.plan_id = plan_id
            subscription.status = 'active'
            subscription.is_trial = False
            subscription.start_date = datetime.utcnow()
            subscription.renewal_date = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            logger.info(f"School {school_id} upgraded to plan {plan.name}")
            
            return {
                'success': True,
                'message': f'Subscription upgraded to {plan.name}',
                'subscription': subscription.to_dict()
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error upgrading subscription: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_school_usage(school_id):
        """Get usage metrics for a school"""
        try:
            usage = SchoolUsage.query.filter_by(school_id=school_id).first()
            if not usage:
                usage = SchoolUsage(school_id=school_id)
                db.session.add(usage)
                db.session.commit()
            
            return usage.to_dict()
        except Exception as e:
            logger.error(f"Error getting usage: {str(e)}")
            raise
    
    @staticmethod
    def list_billings(page=1, per_page=20, status=None):
        """List all billings across all schools"""
        try:
            query = Billing.query
            
            if status:
                query = query.filter_by(payment_status=status)
            
            total = query.count()
            pages = (total + per_page - 1) // per_page
            billings = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                'billings': [billing.to_dict() for billing in billings],
                'total': total,
                'pages': pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"Error listing billings: {str(e)}")
            raise
    
    @staticmethod
    def get_platform_analytics():
        """Get platform-wide analytics"""
        try:
            total_schools = School.query.count()
            active_schools = School.query.filter_by(subscription_status='active').count()
            trial_schools = School.query.filter_by(subscription_status='trial').count()
            
            # Get subscription breakdown
            subscriptions = db.session.query(
                Plan.name,
                func.count(Subscription.id).label('count')
            ).join(Subscription).group_by(Plan.name).all()
            
            subscription_breakdown = {name: count for name, count in subscriptions}
            
            # Get revenue
            paid_billings = Billing.query.filter_by(payment_status='paid').all()
            total_revenue = sum(b.amount for b in paid_billings)
            
            # Get total users
            total_users = User.query.count()
            total_students = db.session.query(func.sum(SchoolUsage.students_count)).scalar() or 0
            total_staff = db.session.query(func.sum(SchoolUsage.staff_count)).scalar() or 0
            
            # Failed payments
            failed_payments = Billing.query.filter_by(payment_status='failed').count()
            
            return {
                'schools': {
                    'total': total_schools,
                    'active': active_schools,
                    'trial': trial_schools,
                    'inactive': total_schools - active_schools - trial_schools
                },
                'subscriptions': subscription_breakdown,
                'revenue': {
                    'total': total_revenue,
                    'currency': 'INR'
                },
                'users': {
                    'total': total_users,
                    'students': total_students,
                    'staff': total_staff
                },
                'payments': {
                    'failed': failed_payments
                }
            }
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            raise
