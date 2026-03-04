"""
Enquiry Service Layer
Handles business logic for lead and enquiry management
"""
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from app.extensions import db
from app.models.enquiry import Enquiry, FollowUp, EnquiryDocument
from app.models.user import User
from app.services.activity_service import ActivityService


class EnquiryService:
    """Service for managing enquiries and leads"""
    
    @staticmethod
    def create_enquiry(school_id, data, created_by_id):
        """
        Create a new enquiry/lead
        
        Args:
            school_id: School ID
            data: Enquiry data dictionary
            created_by_id: User creating the enquiry
            
        Returns:
            Created enquiry object
        """
        enquiry = Enquiry(
            school_id=school_id,
            student_name=data.get('student_name'),
            parent_name=data.get('parent_name'),
            parent_email=data.get('parent_email'),
            parent_phone=data.get('parent_phone'),
            secondary_phone=data.get('secondary_phone'),
            class_applying_for=data.get('class_applying_for'),
            preferred_section=data.get('preferred_section'),
            previous_school=data.get('previous_school'),
            date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date() if data.get('date_of_birth') else None,
            status=data.get('status', 'new'),
            source=data.get('source'),
            priority=data.get('priority', 'medium'),
            assigned_to=data.get('assigned_to'),
            next_follow_up=datetime.strptime(data.get('next_follow_up'), '%Y-%m-%d %H:%M') if data.get('next_follow_up') else None,
            address=data.get('address'),
            notes=data.get('notes')
        )
        
        db.session.add(enquiry)
        db.session.commit()
        
        # Log activity
        ActivityService.log_activity(
            school_id=school_id,
            user_id=created_by_id,
            activity_type='enquiry_created',
            entity_type='enquiry',
            entity_id=enquiry.id,
            description=f"New enquiry created for {enquiry.student_name}"
        )
        
        return enquiry
    
    @staticmethod
    def get_enquiries(school_id, filters=None, page=1, per_page=20):
        """
        Get enquiries with filters and pagination
        
        Args:
            school_id: School ID
            filters: Dictionary of filter criteria
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated enquiries and metadata
        """
        query = Enquiry.query.filter_by(school_id=school_id)
        
        if filters:
            if filters.get('status'):
                query = query.filter(Enquiry.status == filters['status'])
            
            if filters.get('source'):
                query = query.filter(Enquiry.source == filters['source'])
            
            if filters.get('priority'):
                query = query.filter(Enquiry.priority == filters['priority'])
            
            if filters.get('assigned_to'):
                query = query.filter(Enquiry.assigned_to == filters['assigned_to'])
            
            if filters.get('class_applying_for'):
                query = query.filter(Enquiry.class_applying_for == filters['class_applying_for'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Enquiry.student_name.ilike(search_term),
                        Enquiry.parent_name.ilike(search_term),
                        Enquiry.parent_phone.ilike(search_term),
                        Enquiry.parent_email.ilike(search_term)
                    )
                )
            
            if filters.get('follow_up_due'):
                # Get enquiries with follow-up due in next 7 days
                now = datetime.utcnow()
                next_week = now + timedelta(days=7)
                query = query.filter(
                    and_(
                        Enquiry.next_follow_up.isnot(None),
                        Enquiry.next_follow_up <= next_week
                    )
                )
        
        # Order by priority and next follow-up
        query = query.order_by(
            Enquiry.priority.desc(),
            Enquiry.next_follow_up.asc(),
            Enquiry.created_at.desc()
        )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'enquiries': [e.to_dict() for e in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def get_enquiry_by_id(school_id, enquiry_id):
        """Get single enquiry by ID"""
        return Enquiry.query.filter_by(id=enquiry_id, school_id=school_id).first()
    
    @staticmethod
    def update_enquiry(school_id, enquiry_id, data, updated_by_id):
        """
        Update enquiry details
        
        Args:
            school_id: School ID
            enquiry_id: Enquiry ID
            data: Updated data dictionary
            updated_by_id: User updating the enquiry
            
        Returns:
            Updated enquiry object
        """
        enquiry = Enquiry.query.filter_by(id=enquiry_id, school_id=school_id).first()
        if not enquiry:
            return None
        
        # Track status changes
        old_status = enquiry.status
        
        # Update fields
        for key, value in data.items():
            if hasattr(enquiry, key) and key not in ['id', 'school_id', 'created_at']:
                if key == 'date_of_birth' and value:
                    setattr(enquiry, key, datetime.strptime(value, '%Y-%m-%d').date())
                elif key in ['next_follow_up'] and value:
                    setattr(enquiry, key, datetime.strptime(value, '%Y-%m-%d %H:%M'))
                else:
                    setattr(enquiry, key, value)
        
        db.session.commit()
        
        # Log activity if status changed
        if old_status != enquiry.status:
            ActivityService.log_activity(
                school_id=school_id,
                user_id=updated_by_id,
                activity_type='enquiry_status_changed',
                entity_type='enquiry',
                entity_id=enquiry.id,
                description=f"Enquiry status changed from {old_status} to {enquiry.status}"
            )
        
        return enquiry
    
    @staticmethod
    def delete_enquiry(school_id, enquiry_id, deleted_by_id):
        """Delete an enquiry"""
        enquiry = Enquiry.query.filter_by(id=enquiry_id, school_id=school_id).first()
        if not enquiry:
            return False
        
        student_name = enquiry.student_name
        db.session.delete(enquiry)
        db.session.commit()
        
        ActivityService.log_activity(
            school_id=school_id,
            user_id=deleted_by_id,
            activity_type='enquiry_deleted',
            entity_type='enquiry',
            entity_id=enquiry_id,
            description=f"Deleted enquiry for {student_name}"
        )
        
        return True
    
    @staticmethod
    def add_follow_up(school_id, enquiry_id, data, created_by_id):
        """
        Add a follow-up activity for an enquiry
        
        Args:
            school_id: School ID
            enquiry_id: Enquiry ID
            data: Follow-up data
            created_by_id: User creating the follow-up
            
        Returns:
            Created follow-up object
        """
        enquiry = Enquiry.query.filter_by(id=enquiry_id, school_id=school_id).first()
        if not enquiry:
            return None
        
        follow_up = FollowUp(
            school_id=school_id,
            enquiry_id=enquiry_id,
            follow_up_type=data.get('follow_up_type'),
            follow_up_date=datetime.strptime(data.get('follow_up_date'), '%Y-%m-%d %H:%M') if data.get('follow_up_date') else datetime.utcnow(),
            contacted_by=created_by_id,
            status=data.get('status', 'completed'),
            outcome=data.get('outcome'),
            notes=data.get('notes'),
            schedule_next=datetime.strptime(data.get('schedule_next'), '%Y-%m-%d %H:%M') if data.get('schedule_next') else None
        )
        
        db.session.add(follow_up)
        
        # Update enquiry's last_contacted and next_follow_up
        enquiry.last_contacted = follow_up.follow_up_date
        if follow_up.schedule_next:
            enquiry.next_follow_up = follow_up.schedule_next
        
        db.session.commit()
        
        return follow_up
    
    @staticmethod
    def get_follow_ups(school_id, enquiry_id):
        """Get all follow-ups for an enquiry"""
        return FollowUp.query.filter_by(
            school_id=school_id,
            enquiry_id=enquiry_id
        ).order_by(FollowUp.follow_up_date.desc()).all()
    
    @staticmethod
    def get_dashboard_stats(school_id):
        """
        Get enquiry dashboard statistics
        
        Returns:
            Dictionary with pipeline stats
        """
        # Total enquiries by status
        status_counts = db.session.query(
            Enquiry.status,
            func.count(Enquiry.id)
        ).filter_by(school_id=school_id).group_by(Enquiry.status).all()
        
        # Enquiries by source
        source_counts = db.session.query(
            Enquiry.source,
            func.count(Enquiry.id)
        ).filter_by(school_id=school_id).group_by(Enquiry.source).all()
        
        # Follow-ups due this week
        now = datetime.utcnow()
        next_week = now + timedelta(days=7)
        follow_ups_due = Enquiry.query.filter(
            and_(
                Enquiry.school_id == school_id,
                Enquiry.next_follow_up.isnot(None),
                Enquiry.next_follow_up <= next_week,
                Enquiry.status.notin_(['admitted', 'rejected', 'lost'])
            )
        ).count()
        
        # Conversion rate (this month)
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        enquiries_this_month = Enquiry.query.filter(
            and_(
                Enquiry.school_id == school_id,
                Enquiry.created_at >= month_start
            )
        ).count()
        
        converted_this_month = Enquiry.query.filter(
            and_(
                Enquiry.school_id == school_id,
                Enquiry.status == 'admitted',
                Enquiry.converted_at >= month_start
            )
        ).count()
        
        conversion_rate = (converted_this_month / enquiries_this_month * 100) if enquiries_this_month > 0 else 0
        
        return {
            'total_enquiries': sum(count for _, count in status_counts),
            'status_breakdown': dict(status_counts),
            'source_breakdown': dict(source_counts),
            'follow_ups_due': follow_ups_due,
            'enquiries_this_month': enquiries_this_month,
            'converted_this_month': converted_this_month,
            'conversion_rate': round(conversion_rate, 2)
        }
    
    @staticmethod
    def convert_to_student(school_id, enquiry_id, student_id, converted_by_id):
        """
        Mark enquiry as converted to student
        
        Args:
            school_id: School ID
            enquiry_id: Enquiry ID
            student_id: Student user ID
            converted_by_id: User performing conversion
            
        Returns:
            Updated enquiry
        """
        enquiry = Enquiry.query.filter_by(id=enquiry_id, school_id=school_id).first()
        if not enquiry:
            return None
        
        enquiry.status = 'admitted'
        enquiry.converted_to_student_id = student_id
        enquiry.converted_at = datetime.utcnow()
        
        db.session.commit()
        
        ActivityService.log_activity(
            school_id=school_id,
            user_id=converted_by_id,
            activity_type='enquiry_converted',
            entity_type='enquiry',
            entity_id=enquiry.id,
            description=f"Enquiry converted to student: {enquiry.student_name}"
        )
        
        return enquiry
