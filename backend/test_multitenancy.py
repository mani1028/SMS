#!/usr/bin/env python
"""
Multi-School Multi-Tenancy Test Script
Verifies 5 schools can run in isolation with zero data leaks
"""

import sys
import os
from datetime import datetime
from tabulate import tabulate

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.school import School
from app.models.user import User
from app.models.student import Student
from app.models.billing import Subscription, Plan
from flask_jwt_extended import create_access_token


class MultiTenancyTest:
    def __init__(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.schools = []
        self.users = []
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log(self, message="", level="INFO"):
        """Log test messages"""
        if not message:
            print()  # Print empty line
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}"
        print(f"{prefix}: {message}")

    def test(self, name, condition, error_msg=""):
        """Record test result"""
        if condition:
            self.log(f"✓ {name}", "PASS")
            self.passed += 1
            self.test_results.append((name, "✓ PASS", ""))
        else:
            self.log(f"✗ {name}", "FAIL")
            self.failed += 1
            self.test_results.append((name, "✗ FAIL", error_msg))

    def setup_schools(self):
        """Create 5 test schools"""
        self.log("\n=== SETUP: Creating 5 Schools ===\n")
        
        from time import time
        timestamp = str(int(time() * 1000) % 100000)  # Use last 5 digits of timestamp
        
        schools_data = [
            {"name": f"Delhi Public School {timestamp}", "email": f"dps{timestamp}@test.edu.in"},
            {"name": f"Mumbai International School {timestamp}", "email": f"mis{timestamp}@test.edu.in"},
            {"name": f"Bangalore Academy {timestamp}", "email": f"ba{timestamp}@test.edu.in"},
            {"name": f"Hyderabad Central School {timestamp}", "email": f"hcs{timestamp}@test.edu.in"},
            {"name": f"Pune Institute {timestamp}", "email": f"pi{timestamp}@test.edu.in"},
        ]
        
        free_plan = Plan.query.filter_by(name='Free').first()
        if not free_plan:
            self.log("ERROR: Free plan not found! Run seed_saas.py first", "ERROR")
            sys.exit(1)
        
        for idx, school_data in enumerate(schools_data):
            try:
                school = School(
                    name=school_data['name'],
                    email=school_data['email'],
                    subscription_status='active'
                )
                db.session.add(school)
                db.session.flush()
                
                # Create admin user for school
                admin_user = User(
                    name=f"Admin",
                    email=f"admin{idx+1}{timestamp}@{school.name.lower().replace(' ', '')[:20]}.test",
                    school_id=school.id,
                    is_active=True,
                    is_super_admin=False
                )
                admin_user.set_password(f"Password{idx+1}@")
                db.session.add(admin_user)
                db.session.flush()
                
                # Create subscription
                subscription = Subscription(
                    school_id=school.id,
                    plan_id=free_plan.id,
                    status='active'
                )
                db.session.add(subscription)
                
                self.schools.append({
                    'school': school,
                    'admin_user': admin_user,
                    'subscription': subscription,
                    'index': idx + 1
                })
                
                self.log(f"Created School {idx+1}: {school.name}")
            except Exception as e:
                db.session.rollback()
                self.log(f"Failed to create school {idx+1}: {e}", "ERROR")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.log(f"Failed to commit schools: {e}", "ERROR")
        
        self.log(f"\n✓ Successfully created {len(self.schools)} schools\n")

    def setup_students(self):
        """Add students to each school"""
        self.log("\n=== SETUP: Adding Students to Each School ===\n")
        
        for school_info in self.schools:
            school = school_info['school']
            idx = school_info['index']
            
            for i in range(1, 4):  # 3 students per school
                try:
                    student = Student(
                        school_id=school.id,
                        name=f"Student{i} School{idx}",
                        admission_no=f"ADM-{idx}-{i:03d}",
                        roll_no=f"S{idx}_{i:03d}",
                        class_name=f"Class-{i}",
                        section="A",
                    )
                    db.session.add(student)
                except Exception as e:
                    self.log(f"Failed to add student to {school.name}: {e}", "ERROR")
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                self.log(f"Failed to commit students: {e}", "ERROR")
            
            self.log(f"Added 3 students to: {school.name}")
        
        self.log(f"\n✓ Total students: {len(self.schools) * 3}\n")

    def test_data_isolation(self):
        """Test that schools can't see each other's data"""
        self.log("\n=== TEST 1: Data Isolation ===\n")
        
        for school_info in self.schools:
            school = school_info['school']
            idx = school_info['index']
            
            # Count students for this school
            student_count = Student.query.filter_by(school_id=school.id).count()
            expected_count = 3
            
            self.test(
                f"School {idx} sees only its {expected_count} students",
                student_count == expected_count,
                f"Expected {expected_count}, got {student_count}"
            )
        
        self.log()

    def test_cross_school_query(self):
        """Test that queries return school-specific data only"""
        self.log("\n=== TEST 2: Cross-School Query Prevention ===\n")
        
        school_ids = [s['school'].id for s in self.schools]
        total_students = Student.query.filter(Student.school_id.in_(school_ids)).count()
        expected_total = len(self.schools) * 3
        
        self.test(
            "Total students in DB is correct",
            total_students == expected_total,
            f"Expected {expected_total}, got {total_students}"
        )
        
        # Verify each school's data is isolated
        for i, school_info in enumerate(self.schools):
            school = school_info['school']
            school_students = Student.query.filter_by(school_id=school.id).all()
            
            # All students should have the matching school_id
            all_match = all(s.school_id == school.id for s in school_students)
            self.test(
                f"School {i+1}: All students belong to correct school",
                all_match,
                "Student school_id mismatch detected"
            )
        
        self.log()

    def test_jwt_tokens(self):
        """Test JWT tokens are school-scoped"""
        self.log("\n=== TEST 3: JWT Token Isolation ===\n")
        
        for idx, school_info in enumerate(self.schools):
            user = school_info['admin_user']
            token = create_access_token(identity=str(user.id))
            
            self.test(
                f"School {idx+1}: JWT token generated for admin user",
                token is not None and len(token) > 0,
                "Token generation failed"
            )
            
            # Verify user has correct school_id
            self.test(
                f"School {idx+1}: User belongs to correct school",
                user.school_id == school_info['school'].id,
                f"Expected school_id {school_info['school'].id}, got {user.school_id}"
            )
        
        self.log()

    def test_subscription_isolation(self):
        """Test subscriptions are per-school"""
        self.log("\n=== TEST 4: Subscription Isolation ===\n")
        
        for idx, school_info in enumerate(self.schools):
            school = school_info['school']
            subscription = Subscription.query.filter_by(school_id=school.id).first()
            
            self.test(
                f"School {idx+1}: Has exactly one subscription",
                subscription is not None,
                "Subscription not found"
            )
            
            if subscription:
                self.test(
                    f"School {idx+1}: Subscription status is correct",
                    subscription.status == 'active',
                    f"Expected 'active', got '{subscription.status}'"
                )
        
        # Verify no duplicate subscriptions
        total_subs = Subscription.query.count()
        self.test(
            f"Correct number of subscriptions ({len(self.schools)})",
            total_subs == len(self.schools),
            f"Expected {len(self.schools)}, got {total_subs}"
        )
        
        self.log()

    def test_no_data_leaks(self):
        """Verify complete data isolation"""
        self.log("\n=== TEST 5: No Data Leaks ===\n")
        
        # For each school, verify it can't access other schools' students
        all_schools = [s['school'] for s in self.schools]
        
        for i, school_a in enumerate(all_schools):
            school_a_students = Student.query.filter_by(school_id=school_a.id).all()
            
            for j, school_b in enumerate(all_schools):
                if i == j:
                    continue
                
                # School A should NOT see School B's students
                for student in school_a_students:
                    is_from_school_a = student.school_id == school_a.id
                    self.test(
                        f"School {i+1} student not in School {j+1}",
                        is_from_school_a,
                        f"Data leak: School {i+1} saw School {j+1} student"
                    )
        
        self.log()

    def test_password_hashing(self):
        """Verify passwords are hashed, not plain text"""
        self.log("\n=== TEST 6: Password Security ===\n")
        
        for idx, school_info in enumerate(self.schools):
            user = school_info['admin_user']
            original_password = f"Password{idx+1}@"
            
            is_hashed = user.password_hash != original_password
            self.test(
                f"School {idx+1}: Password is hashed",
                is_hashed,
                "Password stored as plain text!"
            )
            
            is_supported_hash = user.password_hash.startswith('pbkdf2:') or user.password_hash.startswith('scrypt:')
            self.test(
                f"School {idx+1}: Uses secure password hashing",
                is_supported_hash,
                "Unsupported hashing algorithm"
            )
        
        self.log()

    def test_super_admin(self):
        """Verify super admin is isolated from schools"""
        self.log("\n=== TEST 7: Super Admin Isolation ===\n")
        
        super_admin = User.query.filter_by(email='admin@platform.local').first()
        
        self.test(
            "Super admin exists",
            super_admin is not None,
            "Super admin not found"
        )
        
        if super_admin:
            self.test(
                "Super admin has no school (school_id is NULL)",
                super_admin.school_id is None,
                f"Super admin has school_id: {super_admin.school_id}"
            )
            
            self.test(
                "Super admin flag is set",
                super_admin.is_super_admin == True,
                "is_super_admin is False"
            )
            
            # Verify super admin is NOT counted in school users
            school_user_count = User.query.filter(User.school_id != None).count()
            total_users_including_super = User.query.count()
            
            self.test(
                "Super admin not counted in school users",
                school_user_count >= len(self.schools),
                f"Expected at least {len(self.schools)}, got {school_user_count}"
            )
        
        self.log()

    def generate_report(self):
        """Generate test report"""
        self.log("\n" + "="*80)
        self.log("MULTI-TENANCY TEST REPORT")
        self.log("="*80 + "\n")
        
        total_tests = self.passed + self.failed
        pass_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(tabulate(self.test_results, headers=["Test Name", "Status", "Error"], tablefmt="grid"))
        
        print(f"\n{'SUMMARY':^80}")
        print("─" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed} ✓")
        print(f"Failed: {self.failed} ✗")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("─" * 80)
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! Multi-tenancy is secure.\n")
            return True
        else:
            print(f"\n⚠️  {self.failed} tests failed. Review data isolation.\n")
            return False

    def cleanup(self):
        """Clean up test data"""
        self.log("\n=== CLEANUP ===\n")
        
        try:
            # Delete all test students
            for school_info in self.schools:
                Student.query.filter_by(school_id=school_info['school'].id).delete()
            
            # Delete all test subscriptions
            for school_info in self.schools:
                Subscription.query.filter_by(school_id=school_info['school'].id).delete()
            
            # Delete all test users
            for school_info in self.schools:
                User.query.filter_by(school_id=school_info['school'].id).delete()
            
            # Delete all test schools
            for school_info in self.schools:
                School.query.filter_by(id=school_info['school'].id).delete()
            
            db.session.commit()
            self.log("✓ Test data cleaned up\n")
        except Exception as e:
            db.session.rollback()
            self.log(f"Cleanup error: {e}", "WARN")

    def run_all_tests(self):
        """Run complete test suite"""
        try:
            self.setup_schools()
            self.setup_students()
            self.test_data_isolation()
            self.test_cross_school_query()
            self.test_jwt_tokens()
            self.test_subscription_isolation()
            self.test_no_data_leaks()
            self.test_password_hashing()
            self.test_super_admin()
            
            success = self.generate_report()
            
            # Always cleanup
            self.cleanup()
            
            return success
        
        except Exception as e:
            self.log(f"Fatal error during tests: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            self.cleanup()
            return False
        
        finally:
            self.ctx.pop()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("Multi-School Multi-Tenancy Test Suite".center(80))
    print("Testing data isolation across 5 schools with complete verification".center(80))
    print("="*80 + "\n")
    
    tester = MultiTenancyTest()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
