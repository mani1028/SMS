"""
Feature Toggle Service
Enable/disable modules per school based on subscription plan
"""
from app.extensions import db
from app.models.feature_toggle import FeatureDefinition, SchoolFeatureToggle, DEFAULT_FEATURES
from app.models.billing import Subscription, Plan
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeatureToggleService:
    """Service for feature toggle management"""

    @staticmethod
    def seed_feature_definitions():
        """Seed default feature definitions (called on app startup)"""
        try:
            for key, info in DEFAULT_FEATURES.items():
                existing = FeatureDefinition.query.filter_by(key=key).first()
                if not existing:
                    feature = FeatureDefinition(
                        key=key,
                        name=info['name'],
                        available_plans=info['plans'],
                        min_plan=info['plans'][0] if info['plans'] else 'Enterprise',
                        is_global_enabled=True
                    )
                    db.session.add(feature)
            db.session.commit()
            return {'success': True, 'message': 'Feature definitions seeded'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Seed features error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_all_features():
        """Get all feature definitions (platform admin)"""
        try:
            features = FeatureDefinition.query.order_by(FeatureDefinition.sort_order).all()
            return {'success': True, 'data': [f.to_dict() for f in features]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_school_features(school_id):
        """
        Get features available for a school based on their plan + any overrides.
        Returns a dict of feature_key -> is_enabled.
        """
        try:
            # Get school's subscription plan
            subscription = Subscription.query.filter_by(school_id=school_id).first()
            plan_name = 'Free'
            if subscription and subscription.plan:
                plan_name = subscription.plan.name

            # Get all feature definitions
            all_features = FeatureDefinition.query.all()

            # Get school-specific overrides
            overrides = {
                t.feature_key: t for t in
                SchoolFeatureToggle.query.filter_by(school_id=school_id).all()
            }

            result = []
            for feature in all_features:
                # Check if plan includes this feature
                plan_enabled = plan_name in (feature.available_plans or [])

                # Check for school-specific override
                override = overrides.get(feature.key)

                if override and override.override_by_admin:
                    # Admin override takes priority
                    is_enabled = override.is_enabled
                elif override:
                    # School toggle: only works if plan allows it
                    is_enabled = plan_enabled and override.is_enabled
                else:
                    # Default: based on plan
                    is_enabled = plan_enabled

                # Global kill switch
                if not feature.is_global_enabled:
                    is_enabled = False

                result.append({
                    'key': feature.key,
                    'name': feature.name,
                    'is_enabled': is_enabled,
                    'included_in_plan': plan_enabled,
                    'has_override': override is not None,
                    'override_by_admin': override.override_by_admin if override else False,
                    'category': feature.category,
                    'description': feature.description
                })

            return {'success': True, 'data': {'plan': plan_name, 'features': result}}
        except Exception as e:
            logger.error(f"Get school features error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def check_feature_enabled(school_id, feature_key):
        """Quick check if a specific feature is enabled for a school"""
        try:
            # Check global
            feature_def = FeatureDefinition.query.filter_by(key=feature_key).first()
            if not feature_def or not feature_def.is_global_enabled:
                return False

            # Check plan
            subscription = Subscription.query.filter_by(school_id=school_id).first()
            plan_name = 'Free'
            if subscription and subscription.plan:
                plan_name = subscription.plan.name

            plan_enabled = plan_name in (feature_def.available_plans or [])

            # Check override
            override = SchoolFeatureToggle.query.filter_by(
                school_id=school_id, feature_key=feature_key
            ).first()

            if override and override.override_by_admin:
                return override.is_enabled
            elif override:
                return plan_enabled and override.is_enabled
            else:
                return plan_enabled

        except Exception as e:
            logger.error(f"Check feature error: {str(e)}")
            return False

    @staticmethod
    def toggle_feature(school_id, feature_key, is_enabled, reason=None):
        """Toggle a feature for a specific school"""
        try:
            toggle = SchoolFeatureToggle.query.filter_by(
                school_id=school_id, feature_key=feature_key
            ).first()

            if not toggle:
                toggle = SchoolFeatureToggle(
                    school_id=school_id,
                    feature_key=feature_key,
                    is_enabled=is_enabled,
                    enabled_at=datetime.utcnow() if is_enabled else None,
                    disabled_at=datetime.utcnow() if not is_enabled else None,
                    disabled_reason=reason if not is_enabled else None
                )
                db.session.add(toggle)
            else:
                toggle.is_enabled = is_enabled
                if is_enabled:
                    toggle.enabled_at = datetime.utcnow()
                    toggle.disabled_reason = None
                else:
                    toggle.disabled_at = datetime.utcnow()
                    toggle.disabled_reason = reason

            db.session.commit()
            return {
                'success': True,
                'message': f"Feature '{feature_key}' {'enabled' if is_enabled else 'disabled'}",
                'data': toggle.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def admin_override_feature(school_id, feature_key, is_enabled, reason=None):
        """Platform admin override — bypasses plan restrictions"""
        try:
            toggle = SchoolFeatureToggle.query.filter_by(
                school_id=school_id, feature_key=feature_key
            ).first()

            if not toggle:
                toggle = SchoolFeatureToggle(
                    school_id=school_id,
                    feature_key=feature_key,
                    is_enabled=is_enabled,
                    override_by_admin=True,
                    enabled_at=datetime.utcnow() if is_enabled else None,
                    disabled_at=datetime.utcnow() if not is_enabled else None,
                    disabled_reason=reason
                )
                db.session.add(toggle)
            else:
                toggle.is_enabled = is_enabled
                toggle.override_by_admin = True
                if is_enabled:
                    toggle.enabled_at = datetime.utcnow()
                else:
                    toggle.disabled_at = datetime.utcnow()
                    toggle.disabled_reason = reason

            db.session.commit()
            return {
                'success': True,
                'message': f"Admin override: '{feature_key}' {'enabled' if is_enabled else 'disabled'}",
                'data': toggle.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def toggle_global_feature(feature_key, is_enabled):
        """Platform-level kill switch for a feature"""
        try:
            feature = FeatureDefinition.query.filter_by(key=feature_key).first()
            if not feature:
                return {'success': False, 'error': 'Feature not found'}

            feature.is_global_enabled = is_enabled
            db.session.commit()
            return {
                'success': True,
                'message': f"Global feature '{feature_key}' {'enabled' if is_enabled else 'disabled'}"
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
