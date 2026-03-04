#!/usr/bin/env python
"""
Seed script for SaaS platform initialization
- Creates default subscription plans
- Creates super admin user
- Can be run after database migrations
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.billing import Plan, Subscription
from app.models.user import User
from app.models.role import Role


def seed_plans():
    """Create default subscription plans"""
    print("📋 Seeding subscription plans...")
    
    plans_data = [
        {
            'name': 'Base',
            'description': 'Temporary base plan for real-time testing',
            'price_monthly': 1,
            'price_annual': 10,
            'max_students': 10,
            'max_staff': 2,
            'storage_gb': 1,
            'sms_credits_monthly': 10,
            'api_calls_per_day': 100,
            'display_order': 0,
            'features': {"students_management": True},
            'enabled_features': ["students_management"],
            'is_active': True
        },
        {
            'name': 'Free',
            'description': 'Perfect for getting started',
            'price_monthly': 0,
            'price_annual': 0,
            'max_students': 100,
            'max_staff': 10,
            'storage_gb': 5,
            'sms_credits_monthly': 100,
            'api_calls_per_day': 1000,
            'display_order': 1,
            'features': {
                'students_management': True,
                'staff_management': True,
                'basic_reports': True,
                'email_support': False,
                'api_access': False,
                'custom_branding': False,
                'sso': False
            },
            'enabled_features': [
                'students_management',
                'staff_management',
                'basic_reports'
            ]
        },
        {
            'name': 'Basic',
            'description': 'Growing school package',
            'price_monthly': 499,
            'price_annual': 4990,
            'max_students': 500,
            'max_staff': 50,
            'storage_gb': 50,
            'sms_credits_monthly': 1000,
            'api_calls_per_day': 10000,
            'display_order': 2,
            'features': {
                'students_management': True,
                'staff_management': True,
                'basic_reports': True,
                'email_support': True,
                'api_access': True,
                'custom_branding': False,
                'sso': False
            },
            'enabled_features': [
                'students_management',
                'staff_management',
                'basic_reports',
                'email_support',
                'api_access'
            ]
        },
        {
            'name': 'Pro',
            'description': 'Advanced features for established schools',
            'price_monthly': 1299,
            'price_annual': 12990,
            'max_students': 2000,
            'max_staff': 200,
            'storage_gb': 200,
            'sms_credits_monthly': 5000,
            'api_calls_per_day': 50000,
            'display_order': 3,
            'features': {
                'students_management': True,
                'staff_management': True,
                'basic_reports': True,
                'email_support': True,
                'api_access': True,
                'custom_branding': True,
                'sso': False
            },
            'enabled_features': [
                'students_management',
                'staff_management',
                'basic_reports',
                'email_support',
                'api_access',
                'custom_branding'
            ]
        },
        {
            'name': 'Enterprise',
            'description': 'Custom solution for large institutions',
            'price_monthly': 4999,
            'price_annual': 49990,
            'max_students': 10000,
            'max_staff': 500,
            'storage_gb': 1000,
            'sms_credits_monthly': 50000,
            'api_calls_per_day': 500000,
            'display_order': 4,
            'features': {
                'students_management': True,
                'staff_management': True,
                'basic_reports': True,
                'email_support': True,
                'api_access': True,
                'custom_branding': True,
                'sso': True
            },
            'enabled_features': [
                'students_management',
                'staff_management',
                'basic_reports',
                'email_support',
                'api_access',
                'custom_branding',
                'sso'
            ]
        }
    ]
    
    for plan_data in plans_data:
        # Check if plan already exists
        existing_plan = Plan.query.filter_by(name=plan_data['name']).first()
        if existing_plan:
            print(f"  ✓ Plan '{plan_data['name']}' already exists")
            continue
        
        plan = Plan(**plan_data)
        db.session.add(plan)
        print(f"  ✓ Plan '{plan_data['name']}' created (₹{plan_data['price_monthly']}/month)")
    
    db.session.commit()
    print("✅ Plans seeded successfully!\n")


def create_super_admin():
    """Create super admin user"""
    print("👤 Creating super admin user...")
    
    # Check if super admin already exists
    existing_admin = User.query.filter_by(is_super_admin=True).first()
    if existing_admin:
        print(f"  ✓ Super admin already exists: {existing_admin.email}")
        return
    
    # Create super admin user
    admin_email = 'admin@platform.local'
    admin_password = 'Admin@123456'  # Default - should be changed in production
    
    admin_user = User(
        email=admin_email,
        password=admin_password,
        is_active=True,
        is_super_admin=True,
        school_id=None  # Super admin belongs to no school
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"  ✓ Super admin created successfully")
    print(f"    Email: {admin_email}")
    print(f"    Password: {admin_password}")
    print("    ⚠️  IMPORTANT: Change this password in production!\n")


def verify_plans():
    """Verify plans were created"""
    print("🔍 Verifying plans...")
    plans = Plan.query.all()
    print(f"  Total plans in database: {len(plans)}")
    for plan in plans:
        print(f"  - {plan.name}: ₹{plan.price_monthly}/month | Max students: {plan.max_students}")
    print()


def verify_super_admin():
    """Verify super admin was created"""
    print("🔍 Verifying super admin...")
    admin = User.query.filter_by(is_super_admin=True).first()
    if admin:
        print(f"  ✓ Super admin exists: {admin.email} (ID: {admin.id})")
        print(f"    is_super_admin: {admin.is_super_admin}")
        print(f"    school_id: {admin.school_id}")
        print(f"    is_active: {admin.is_active}\n")
    else:
        print("  ✗ No super admin found\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌱 SaaS Platform Seeding Script")
    print("="*60 + "\n")
    
    app = create_app()
    with app.app_context():
        print("📊 Database Configuration:")
        print(f"  Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}\n")
        
        try:
            # Seed plans
            seed_plans()
            
            # Create super admin
            create_super_admin()
            
            # Verify everything
            verify_plans()
            verify_super_admin()
            
            print("="*60)
            print("✅ Seeding completed successfully!")
            print("="*60)
            print("\n📝 Next steps:")
            print("  1. Start your Flask server: python run.py")
            print("  2. Login as super admin at: /platform/super-admin/login")
            print("  3. Email: admin@platform.local | Password: Admin@123456")
            print("  4. ⚠️  CHANGE THE PASSWORD IMMEDIATELY IN PRODUCTION\n")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
