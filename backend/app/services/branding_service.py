"""
Custom Branding Service
Logo, theme colors, school name on reports per school
"""
from app.extensions import db
from app.models.settings import SchoolConfiguration
from app.models.school import School
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BrandingService:
    """Service for per-school custom branding"""

    @staticmethod
    def get_branding(school_id):
        """Get school branding configuration"""
        try:
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()
            if not config:
                return {
                    'success': True,
                    'data': {
                        'school_id': school_id,
                        'school_name': 'My School',
                        'school_logo_url': None,
                        'primary_color': '#003366',
                        'secondary_color': '#FF6600',
                        'school_address': None,
                        'school_phone': None,
                        'school_email': None,
                        'school_website': None
                    }
                }

            return {
                'success': True,
                'data': {
                    'school_id': school_id,
                    'school_name': config.school_name,
                    'school_logo_url': config.school_logo_url,
                    'primary_color': config.primary_color,
                    'secondary_color': config.secondary_color,
                    'school_address': config.school_address,
                    'school_phone': config.school_phone,
                    'school_email': config.school_email,
                    'school_website': config.school_website
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_branding(school_id, **kwargs):
        """Update school branding settings"""
        try:
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()
            if not config:
                config = SchoolConfiguration(
                    school_id=school_id,
                    school_name=kwargs.get('school_name', 'My School')
                )
                db.session.add(config)

            allowed_fields = [
                'school_name', 'school_logo_url', 'primary_color', 'secondary_color',
                'school_address', 'school_phone', 'school_email', 'school_website'
            ]

            for field in allowed_fields:
                if field in kwargs and kwargs[field] is not None:
                    setattr(config, field, kwargs[field])

            db.session.commit()
            return {
                'success': True,
                'message': 'Branding updated successfully',
                'data': {
                    'school_name': config.school_name,
                    'school_logo_url': config.school_logo_url,
                    'primary_color': config.primary_color,
                    'secondary_color': config.secondary_color,
                    'school_address': config.school_address,
                    'school_phone': config.school_phone,
                    'school_email': config.school_email,
                    'school_website': config.school_website
                }
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update branding error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_branding(school_id, logo_url=None, primary_color=None, custom_domain=None):
        """Update school branding settings for white label support"""
        try:
            school = School.query.get(school_id)
            if not school:
                logger.error(f"School not found for branding update: {school_id}")
                return False
            if logo_url is not None:
                school.logo_url = logo_url
            if primary_color is not None:
                school.primary_color = primary_color
            if custom_domain is not None:
                school.custom_domain = custom_domain
            db.session.commit()
            logger.info(f"Branding updated for school {school_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update branding error: {str(e)}")
            return False

    @staticmethod
    def get_report_header(school_id):
        """Get branding data formatted for report headers"""
        try:
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()
            return {
                'success': True,
                'data': {
                    'school_name': config.school_name if config else 'School',
                    'logo_url': config.school_logo_url if config else None,
                    'address': config.school_address if config else None,
                    'phone': config.school_phone if config else None,
                    'email': config.school_email if config else None,
                    'website': config.school_website if config else None,
                    'primary_color': config.primary_color if config else '#003366',
                    'secondary_color': config.secondary_color if config else '#FF6600',
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def upload_logo(school_id, logo_url):
        """Update school logo URL"""
        try:
            config = SchoolConfiguration.query.filter_by(school_id=school_id).first()
            if not config:
                config = SchoolConfiguration(school_id=school_id, school_name='My School')
                db.session.add(config)

            config.school_logo_url = logo_url
            db.session.commit()
            return {'success': True, 'message': 'Logo updated', 'data': {'logo_url': logo_url}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
