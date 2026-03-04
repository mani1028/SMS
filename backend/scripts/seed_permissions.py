"""
Permissions Seed Script
Initializes all permission records for the SMS system
Run this after database migration with: python -c "from scripts.seed_permissions import seed_all_permissions; seed_all_permissions()"
"""

from app.models.permission import Permission
from app.models.role import Role
from app.extensions import db


def create_permission(name, description):
    """Helper to create permission"""
    existing = Permission.query.filter_by(name=name).first()
    if existing:
        return existing
    
    perm = Permission(name=name, description=description)
    db.session.add(perm)
    return perm


def seed_all_permissions():
    """Seed all permissions"""
    try:
        # ACADEMIC MANAGEMENT
        create_permission('create_class', 'Create academic class')
        create_permission('edit_class', 'Edit academic class')
        create_permission('view_classes', 'View all classes')
        create_permission('delete_class', 'Delete class')
        
        create_permission('create_section', 'Create section')
        create_permission('edit_section', 'Edit section')
        create_permission('view_sections', 'View sections')
        create_permission('delete_section', 'Delete section')
        
        create_permission('create_subject', 'Create subject')
        create_permission('edit_subject', 'Edit subject')
        create_permission('view_subjects', 'View subjects')
        create_permission('delete_subject', 'Delete subject')
        
        create_permission('assign_teacher', 'Assign teacher to class/subject')
        create_permission('create_timetable', 'Create timetable')
        create_permission('edit_timetable', 'Edit timetable')
        create_permission('view_timetable', 'View timetable')
        
        # ATTENDANCE
        create_permission('mark_attendance', 'Mark attendance')
        create_permission('view_attendance', 'View attendance records')
        create_permission('edit_attendance', 'Edit attendance records')
        create_permission('attendance_report', 'View attendance reports')
        
        create_permission('apply_leave', 'Apply for leave')
        create_permission('approve_leave', 'Approve leave requests')
        create_permission('reject_leave', 'Reject leave requests')
        create_permission('view_leave_requests', 'View leave requests')
        
        create_permission('staff_checkin', 'Staff check-in/check-out')
        create_permission('view_checkin_logs', 'View check-in/out logs')
        
        # EXAMS
        create_permission('create_exam_term', 'Create exam term')
        create_permission('view_exam_terms', 'View exam terms')
        create_permission('create_exam_schedule', 'Create exam schedule')
        create_permission('edit_exam_schedule', 'Edit exam schedule')
        create_permission('view_exam_schedule', 'View exam schedule')
        
        create_permission('enter_marks', 'Enter student marks')
        create_permission('bulk_enter_marks', 'Bulk enter marks')
        create_permission('view_grades', 'View grades')
        create_permission('view_report_card', 'View student report card')
        create_permission('calculate_ranks', 'Calculate student ranks')
        
        # FINANCE
        create_permission('create_fee_structure', 'Create fee structure')
        create_permission('edit_fee_structure', 'Edit fee structure')
        create_permission('view_fee_structure', 'View fee structure')
        
        create_permission('create_fee_plan', 'Create fee plan')
        create_permission('assign_fee', 'Assign fee to student')
        create_permission('view_student_fees', 'View student fees')
        
        create_permission('process_payment', 'Process fee payment')
        create_permission('view_payments', 'View payment records')
        create_permission('collection_report', 'View fee collection report')
        create_permission('view_defaulters', 'View fee defaulters list')
        
        create_permission('award_scholarship', 'Award scholarship')
        create_permission('view_scholarships', 'View scholarships')
        
        create_permission('generate_receipt', 'Generate payment receipt')
        create_permission('receipts_report', 'View receipts report')
        
        # TRANSPORT
        create_permission('add_vehicle', 'Add transport vehicle')
        create_permission('edit_vehicle', 'Edit vehicle details')
        create_permission('view_vehicles', 'View vehicles')
        
        create_permission('create_route', 'Create transport route')
        create_permission('edit_route', 'Edit route')
        create_permission('view_routes', 'View routes')
        
        create_permission('allocate_student_transport', 'Allocate student to route')
        create_permission('view_transport_allocation', 'View transport allocations')
        
        create_permission('view_gps_tracking', 'View vehicle GPS tracking')
        
        # LIBRARY
        create_permission('add_book', 'Add book to library')
        create_permission('edit_book', 'Edit book details')
        create_permission('view_books', 'View library books')
        
        create_permission('issue_book', 'Issue book to user')
        create_permission('return_book', 'Accept book return')
        create_permission('view_book_issues', 'View book issues')
        create_permission('view_overdue_books', 'View overdue books')
        create_permission('collect_library_fine', 'Collect library fine')
        
        # HOSTEL
        create_permission('create_hostel_room', 'Create hostel room')
        create_permission('edit_hostel_room', 'Edit hostel room')
        create_permission('view_hostel_rooms', 'View hostel rooms')
        
        create_permission('allocate_hostel', 'Allocate student to hostel')
        create_permission('deallocate_hostel', 'Remove student from hostel')
        create_permission('view_hostel_allocations', 'View hostel allocations')
        
        # LAB
        create_permission('add_lab_item', 'Add item to lab inventory')
        create_permission('update_lab_inventory', 'Update lab inventory')
        create_permission('view_lab_inventory', 'View lab inventory')
        create_permission('reorder_lab_items', 'View items needing reorder')
        
        # COMMUNICATION
        create_permission('create_notice', 'Create notice')
        create_permission('edit_notice', 'Edit notice')
        create_permission('view_notices', 'View notices')
        create_permission('delete_notice', 'Delete notice')
        
        create_permission('create_event', 'Create event')
        create_permission('view_events', 'View events')
        
        create_permission('create_announcement', 'Create announcement')
        create_permission('view_announcements', 'View announcements')
        
        create_permission('create_homework', 'Create homework')
        create_permission('view_homework', 'View homework')
        create_permission('submit_homework', 'Submit homework')
        create_permission('evaluate_homework', 'Evaluate homework submissions')
        create_permission('view_homework_submissions', 'View homework submissions')
        
        create_permission('upload_document', 'Upload document')
        create_permission('view_documents', 'View documents')
        
        # SETTINGS
        create_permission('view_config', 'View system configuration')
        create_permission('edit_config', 'Edit system configuration')
        
        create_permission('create_academic_year', 'Create academic year')
        create_permission('view_academic_years', 'View academic years')
        create_permission('set_current_year', 'Set current academic year')
        
        create_permission('view_audit_logs', 'View audit logs')
        create_permission('view_system_logs', 'View system logs')
        
        # ADMIN/DASHBOARD
        create_permission('view_dashboard', 'View dashboard')
        create_permission('view_analytics', 'View analytics/reports')
        create_permission('export_data', 'Export system data')
        
        # USER MANAGEMENT
        create_permission('create_user', 'Create user')
        create_permission('edit_user', 'Edit user')
        create_permission('view_users', 'View users')
        create_permission('deactivate_user', 'Deactivate user')
        create_permission('reset_password', 'Reset user password')
        
        create_permission('manage_roles', 'Manage roles')
        create_permission('manage_permissions', 'Manage permissions')

        # STUDENT MANAGEMENT (extended)
        create_permission('create_student', 'Create student')
        create_permission('edit_student', 'Edit student')
        create_permission('view_students', 'View students')
        create_permission('delete_student', 'Delete student')
        create_permission('view_student_profile', 'View student profile')
        create_permission('promote_students', 'Promote students')

        # PARENT MANAGEMENT
        create_permission('create_parent', 'Create parent record')
        create_permission('edit_parent', 'Edit parent record')
        create_permission('view_parent', 'View parent records')
        create_permission('view_parents', 'View parents list')

        # STAFF MANAGEMENT
        create_permission('create_staff', 'Create staff member')
        create_permission('edit_staff', 'Edit staff member')
        create_permission('view_staff', 'View staff members')
        create_permission('manage_users', 'Manage user accounts')
        create_permission('manage_staff_attendance', 'Manage staff attendance')
        create_permission('manage_staff_leaves', 'Manage staff leaves')

        # BULK OPERATIONS
        create_permission('bulk_upload_students', 'Bulk upload students via CSV')
        create_permission('bulk_export_students', 'Export students to CSV')
        create_permission('bulk_assign_fees', 'Bulk assign fees to students')
        create_permission('bulk_mark_attendance', 'Bulk mark attendance')
        create_permission('bulk_promote', 'Bulk promote students')

        # EXPENSE MANAGEMENT
        create_permission('create_expense', 'Create expense record')
        create_permission('view_expenses', 'View expenses')
        create_permission('approve_expense', 'Approve expense')
        create_permission('reject_expense', 'Reject expense')
        create_permission('manage_expense_categories', 'Manage expense categories')
        create_permission('view_financial_overview', 'View financial overview')
        create_permission('manage_salary_structures', 'Manage salary structures')
        create_permission('process_salary', 'Process salary payment')
        create_permission('view_salary_payments', 'View salary payments')

        # CURRICULUM MANAGEMENT
        create_permission('create_curriculum', 'Create curriculum plan')
        create_permission('view_curriculum', 'View curriculum plans')
        create_permission('edit_curriculum', 'Edit curriculum/topic progress')
        create_permission('manage_weekly_syllabus', 'Manage weekly syllabus')

        # BACKUP & RESTORE
        create_permission('create_backup', 'Create system backup')
        create_permission('view_backups', 'View backup list')
        create_permission('restore_backup', 'Restore from backup')
        create_permission('delete_backup', 'Delete backup')

        # BRANDING
        create_permission('view_branding', 'View school branding')
        create_permission('edit_branding', 'Edit school branding')

        # FEATURE TOGGLES
        create_permission('view_features', 'View feature toggles')
        create_permission('toggle_features', 'Toggle features for school')

        # ALERTS
        create_permission('create_alert', 'Create alert')
        create_permission('view_alerts', 'View alerts')
        create_permission('manage_alerts', 'Manage alert rules')

        # ADVANCED FEATURES
        create_permission('generate_id_card', 'Generate student ID card')
        create_permission('manage_promotions', 'Manage student promotions')
        create_permission('manage_documents', 'Manage document vault')
        create_permission('manage_api_keys', 'Manage API keys')
        create_permission('view_reports', 'View reports')

        # BRANCH MANAGEMENT
        create_permission('create_branch', 'Create branch')
        create_permission('edit_branch', 'Edit branch')
        create_permission('view_branches', 'View branches')
        create_permission('delete_branch', 'Delete branch')

        # ANALYTICS
        create_permission('view_student_analytics', 'View student analytics')
        create_permission('view_fee_analytics', 'View fee analytics')
        create_permission('view_attendance_analytics', 'View attendance analytics')

        # ENQUIRY/CRM
        create_permission('create_enquiry', 'Create new enquiry')
        create_permission('view_enquiries', 'View enquiries')
        create_permission('edit_enquiry', 'Edit enquiry')
        create_permission('delete_enquiry', 'Delete enquiry')
        create_permission('convert_enquiry', 'Convert enquiry to student')

        # PARENT PORTAL
        create_permission('view_child_overview', 'View child overview (parent)')
        create_permission('view_child_attendance', 'View child attendance (parent)')
        create_permission('view_child_marks', 'View child marks (parent)')
        create_permission('view_child_fees', 'View child fees (parent)')

        # PAYMENTS
        create_permission('initiate_payment', 'Initiate online payment')
        create_permission('verify_payment', 'Verify payment')
        create_permission('view_payment_history', 'View payment history')
        create_permission('initiate_refund', 'Initiate refund')
        create_permission('view_payment_analytics', 'View payment analytics')

        # AUDIT
        create_permission('view_audit_trail', 'View audit trail')
        create_permission('view_entity_history', 'View entity change history')
        create_permission('view_user_activity', 'View user activity log')
        
        db.session.commit()
        print("✓ All permissions created successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating permissions: {str(e)}")
        return False


def seed_sample_roles(school_id):
    """Create sample roles with permissions for a school"""
    try:
        # Get all permissions
        all_perms = Permission.query.all()
        
        # ADMIN ROLE - All permissions
        admin_role = Role(
            school_id=school_id,
            name='Admin',
            description='Full system access'
        )
        admin_role.permissions = all_perms
        db.session.add(admin_role)
        
        # PRINCIPAL ROLE
        principal_perms = Permission.query.filter(
            Permission.name.in_([
                'view_dashboard', 'view_analytics', 'view_classes', 'view_sections',
                'view_students', 'view_staff', 'view_parents', 'view_student_profile',
                'view_attendance', 'attendance_report',
                'view_exam_terms', 'view_grades', 'view_report_card',
                'view_fee_structure', 'collection_report', 'view_defaulters',
                'view_vehicles', 'view_routes',
                'view_books', 'view_overdue_books',
                'view_notices', 'view_announcements',
                'view_academic_years', 'view_config',
                'view_expenses', 'view_financial_overview', 'view_salary_payments',
                'view_curriculum', 'view_branding', 'view_features',
                'view_alerts', 'view_branches', 'view_reports',
                'view_student_analytics', 'view_fee_analytics', 'view_attendance_analytics',
                'view_audit_trail', 'view_entity_history',
                'view_payment_history', 'view_payment_analytics',
                'view_backups', 'export_data',
                'approve_expense', 'reject_expense'
            ])
        ).all()
        
        principal_role = Role(
            school_id=school_id,
            name='Principal',
            description='Principal access'
        )
        principal_role.permissions = principal_perms
        db.session.add(principal_role)
        
        # TEACHER ROLE
        teacher_perms = Permission.query.filter(
            Permission.name.in_([
                'view_dashboard', 'view_timetable', 'view_classes', 'view_sections',
                'mark_attendance', 'view_attendance', 'bulk_mark_attendance',
                'enter_marks', 'bulk_enter_marks', 'view_grades',
                'create_homework', 'view_homework', 'evaluate_homework',
                'view_homework_submissions', 'view_students', 'view_student_profile',
                'view_events', 'view_announcements',
                'view_curriculum', 'create_curriculum', 'edit_curriculum',
                'manage_weekly_syllabus',
                'view_alerts', 'view_branches'
            ])
        ).all()
        
        teacher_role = Role(
            school_id=school_id,
            name='Teacher',
            description='Teacher access'
        )
        teacher_role.permissions = teacher_perms
        db.session.add(teacher_role)
        
        # STUDENT ROLE
        student_perms = Permission.query.filter(
            Permission.name.in_([
                'view_dashboard', 'view_timetable', 'view_homework', 'submit_homework',
                'view_grades', 'view_report_card',
                'apply_leave', 'view_events', 'view_announcements',
                'view_books', 'view_attendance',
                'view_alerts'
            ])
        ).all()
        
        student_role = Role(
            school_id=school_id,
            name='Student',
            description='Student access'
        )
        student_role.permissions = student_perms
        db.session.add(student_role)
        
        # ACCOUNTANT ROLE
        accountant_perms = Permission.query.filter(
            Permission.name.in_([
                'view_dashboard', 'view_fee_structure', 'process_payment', 'view_payments',
                'collection_report', 'view_defaulters', 'generate_receipt',
                'view_scholarships',
                'create_expense', 'view_expenses', 'approve_expense', 'manage_expense_categories',
                'view_financial_overview', 'manage_salary_structures',
                'process_salary', 'view_salary_payments',
                'view_fee_analytics', 'view_payment_history', 'view_payment_analytics',
                'initiate_payment', 'initiate_refund',
                'bulk_assign_fees',
                'view_students', 'export_data'
            ])
        ).all()
        
        accountant_role = Role(
            school_id=school_id,
            name='Accountant',
            description='Finance management'
        )
        accountant_role.permissions = accountant_perms
        db.session.add(accountant_role)
        
        # STAFF ROLE
        staff_perms = Permission.query.filter(
            Permission.name.in_([
                'staff_checkin', 'view_attendance', 'apply_leave',
                'view_timetable', 'view_events', 'view_announcements'
            ])
        ).all()
        
        staff_role = Role(
            school_id=school_id,
            name='Staff',
            description='General staff access'
        )
        staff_role.permissions = staff_perms
        db.session.add(staff_role)
        
        # PARENT ROLE
        parent_perms = Permission.query.filter(
            Permission.name.in_([
                'view_dashboard',
                'view_child_overview', 'view_child_attendance',
                'view_child_marks', 'view_child_fees',
                'view_homework', 'view_events', 'view_announcements',
                'view_alerts', 'initiate_payment', 'view_payment_history'
            ])
        ).all()
        
        parent_role = Role(
            school_id=school_id,
            name='Parent',
            description='Parent read-only access to child data'
        )
        parent_role.permissions = parent_perms
        db.session.add(parent_role)
        
        # ADMISSIONS OFFICER ROLE
        admissions_perms = Permission.query.filter(
            Permission.name.in_([
                'view_dashboard', 'create_enquiry', 'view_enquiries',
                'edit_enquiry', 'convert_enquiry',
                'create_student', 'view_students', 'view_student_profile',
                'create_parent', 'view_parent',
                'view_alerts'
            ])
        ).all()
        
        admissions_role = Role(
            school_id=school_id,
            name='Admissions Officer',
            description='Admissions and enquiry management'
        )
        admissions_role.permissions = admissions_perms
        db.session.add(admissions_role)
        
        db.session.commit()
        print(f"✓ Sample roles created for school {school_id}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating roles: {str(e)}")
        return False


if __name__ == '__main__':
    # This is for running directly: python backend/scripts/seed_permissions.py
    from app import create_app
    
    app = create_app()
    with app.app_context():
        seed_all_permissions()
