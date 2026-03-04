"""
Bulk Operations Service
CSV upload for students, bulk fee assignment, bulk attendance, bulk promotion
"""
from app.extensions import db
from app.models.student import Student, StudentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.finance import StudentFeeInstallment, FeeStructure, FeeComponent, FeePlan
from app.models.advanced import PromotionBatch, PromotionRecord
from app.models.academics import Class, Section
from datetime import datetime, date
import csv
import io
import logging

logger = logging.getLogger(__name__)


class BulkOperationsService:
    """Service for all bulk CRUD operations"""

    # ── Bulk Student Upload ────────────────────────────────────

    @staticmethod
    def bulk_upload_students(school_id, csv_data, update_existing=False):
        """
        Parse CSV and create/update students in bulk.
        Expected CSV columns: name, admission_no, class_name, section, roll_no,
                              email, phone, gender, dob, parent_name, parent_phone, address
        """
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            results = {'created': 0, 'updated': 0, 'errors': [], 'total': 0}

            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                results['total'] += 1
                try:
                    name = row.get('name', '').strip()
                    admission_no = row.get('admission_no', '').strip()

                    if not name or not admission_no:
                        results['errors'].append({
                            'row': row_num,
                            'error': 'name and admission_no are required',
                            'data': row
                        })
                        continue

                    existing = Student.query.filter_by(
                        school_id=school_id, admission_no=admission_no
                    ).first()

                    if existing and not update_existing:
                        results['errors'].append({
                            'row': row_num,
                            'error': f'Student with admission_no {admission_no} already exists',
                            'data': row
                        })
                        continue

                    dob = None
                    if row.get('dob'):
                        try:
                            dob = datetime.strptime(row['dob'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            pass

                    if existing and update_existing:
                        existing.name = name
                        existing.class_name = row.get('class_name', existing.class_name).strip()
                        existing.section = row.get('section', existing.section or '').strip() or existing.section
                        existing.roll_no = row.get('roll_no', existing.roll_no or '').strip() or existing.roll_no
                        existing.email = row.get('email', existing.email or '').strip() or existing.email
                        existing.phone = row.get('phone', existing.phone or '').strip() or existing.phone
                        existing.gender = row.get('gender', existing.gender or '').strip() or existing.gender
                        existing.dob = dob or existing.dob
                        existing.address = row.get('address', existing.address or '').strip() or existing.address
                        existing.parent_name = row.get('parent_name', existing.parent_name or '').strip() or existing.parent_name
                        existing.parent_phone = row.get('parent_phone', existing.parent_phone or '').strip() or existing.parent_phone
                        results['updated'] += 1
                    else:
                        student = Student(
                            school_id=school_id,
                            name=name,
                            admission_no=admission_no,
                            class_name=row.get('class_name', '').strip(),
                            section=row.get('section', '').strip() or None,
                            roll_no=row.get('roll_no', '').strip() or None,
                            email=row.get('email', '').strip() or None,
                            phone=row.get('phone', '').strip() or None,
                            gender=row.get('gender', '').strip() or None,
                            dob=dob,
                            address=row.get('address', '').strip() or None,
                            parent_name=row.get('parent_name', '').strip() or None,
                            parent_phone=row.get('parent_phone', '').strip() or None,
                            status=StudentStatus.ACTIVE,
                            is_active=True
                        )
                        db.session.add(student)
                        results['created'] += 1

                except Exception as e:
                    results['errors'].append({
                        'row': row_num,
                        'error': str(e),
                        'data': row
                    })

            db.session.commit()
            return {
                'success': True,
                'message': f"Processed {results['total']} rows: {results['created']} created, "
                           f"{results['updated']} updated, {len(results['errors'])} errors",
                'data': results
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk student upload error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_student_csv_template():
        """Return CSV template for bulk student upload"""
        headers = ['name', 'admission_no', 'class_name', 'section', 'roll_no',
                    'email', 'phone', 'gender', 'dob', 'parent_name', 'parent_phone', 'address']
        sample = ['John Doe', 'ADM-2025-001', 'Class 10', 'A', '1',
                   'john@email.com', '9876543210', 'male', '2010-05-15',
                   'Jane Doe', '9876543211', '123 Street, City']
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(sample)
        return {'success': True, 'data': {'csv_template': output.getvalue()}}

    # ── Bulk Fee Assignment ────────────────────────────────────

    @staticmethod
    def bulk_assign_fees(school_id, class_id=None, section_id=None, student_ids=None,
                         fee_plan_id=None, academic_year=None, installments_data=None):
        """
        Assign fee installments in bulk to students.
        Can target: all students in a class/section, or a specific list of student_ids.
        """
        try:
            if not fee_plan_id or not installments_data:
                return {'success': False, 'error': 'fee_plan_id and installments_data are required'}

            # Determine target students
            from app.models.user import User
            query = User.query.filter_by(school_id=school_id, is_active=True)

            if student_ids:
                query = query.filter(User.id.in_(student_ids))
            # Note: class/section filtering would require joining with student enrollment
            # For now, accept student_ids or all active users

            students = query.all()
            if not students:
                return {'success': False, 'error': 'No students found'}

            results = {'assigned': 0, 'skipped': 0, 'errors': []}

            for student in students:
                for inst in installments_data:
                    try:
                        existing = StudentFeeInstallment.query.filter_by(
                            school_id=school_id,
                            student_id=student.id,
                            fee_plan_id=fee_plan_id,
                            installment_number=inst.get('installment_number')
                        ).first()

                        if existing:
                            results['skipped'] += 1
                            continue

                        due_date = datetime.strptime(inst['due_date'], '%Y-%m-%d').date()
                        installment = StudentFeeInstallment(
                            school_id=school_id,
                            student_id=student.id,
                            fee_plan_id=fee_plan_id,
                            installment_number=inst['installment_number'],
                            due_date=due_date,
                            amount=inst['amount']
                        )
                        db.session.add(installment)
                        results['assigned'] += 1
                    except Exception as e:
                        results['errors'].append({
                            'student_id': student.id,
                            'error': str(e)
                        })

            db.session.commit()
            return {
                'success': True,
                'message': f"Fee assigned to {results['assigned']} records, "
                           f"{results['skipped']} skipped, {len(results['errors'])} errors",
                'data': results
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk fee assignment error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ── Bulk Attendance Marking ────────────────────────────────

    @staticmethod
    def bulk_mark_attendance(school_id, marked_by_id, attendance_date, records,
                              section_id=None, subject_id=None):
        """
        Mark attendance for multiple students at once.
        records: list of {user_id, status, remarks}
        """
        try:
            if not records:
                return {'success': False, 'error': 'No attendance records provided'}

            if isinstance(attendance_date, str):
                attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()

            results = {'marked': 0, 'updated': 0, 'errors': []}

            for record in records:
                try:
                    user_id = record.get('user_id') or record.get('student_id')
                    status = record.get('status', AttendanceStatus.PRESENT)

                    if not user_id:
                        results['errors'].append({'record': record, 'error': 'user_id required'})
                        continue

                    existing = Attendance.query.filter_by(
                        school_id=school_id,
                        user_id=user_id,
                        section_id=section_id,
                        subject_id=subject_id,
                        attendance_date=attendance_date
                    ).first()

                    if existing:
                        existing.status = status
                        existing.remarks = record.get('remarks', existing.remarks)
                        existing.marked_by_id = marked_by_id
                        results['updated'] += 1
                    else:
                        att = Attendance(
                            school_id=school_id,
                            user_id=user_id,
                            section_id=section_id,
                            subject_id=subject_id,
                            attendance_date=attendance_date,
                            status=status,
                            remarks=record.get('remarks'),
                            marked_by_id=marked_by_id
                        )
                        db.session.add(att)
                        results['marked'] += 1

                except Exception as e:
                    results['errors'].append({'record': record, 'error': str(e)})

            db.session.commit()
            return {
                'success': True,
                'message': f"Attendance: {results['marked']} marked, "
                           f"{results['updated']} updated, {len(results['errors'])} errors",
                'data': results
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk attendance error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ── Bulk Promotion ─────────────────────────────────────────

    @staticmethod
    def bulk_promote_students(school_id, from_class_name, to_class_name,
                               academic_year, initiated_by_id, student_ids=None,
                               auto_assign_section=True):
        """
        Promote students from one class to another in bulk.
        If student_ids is None, promotes ALL active students in from_class.
        """
        try:
            query = Student.query.filter_by(
                school_id=school_id,
                class_name=from_class_name,
                status=StudentStatus.ACTIVE
            )
            if student_ids:
                query = query.filter(Student.id.in_(student_ids))

            students = query.all()
            if not students:
                return {'success': False, 'error': f'No active students found in {from_class_name}'}

            # Create promotion batch
            from_class = Class.query.filter_by(school_id=school_id, name=from_class_name).first()
            to_class = Class.query.filter_by(school_id=school_id, name=to_class_name).first()

            batch = PromotionBatch(
                school_id=school_id,
                from_academic_year=academic_year,
                to_academic_year=academic_year,
                from_class_id=from_class.id if from_class else 0,
                to_class_id=to_class.id if to_class else 0,
                total_students=len(students),
                initiated_by_id=initiated_by_id,
                status='completed'
            )
            db.session.add(batch)
            db.session.flush()

            promoted = 0
            errors = []

            for student in students:
                try:
                    record = PromotionRecord(
                        school_id=school_id,
                        batch_id=batch.id,
                        student_id=student.id,
                        from_class=student.class_name,
                        from_section=student.section,
                        from_roll_no=student.roll_no,
                        to_class=to_class_name,
                        status='promoted'
                    )
                    db.session.add(record)

                    # Update student record
                    student.class_name = to_class_name
                    if auto_assign_section:
                        student.section = student.section  # keep same section
                    promoted += 1

                except Exception as e:
                    errors.append({'student_id': student.id, 'error': str(e)})

            batch.promoted_count = promoted
            batch.completed_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'message': f"Promoted {promoted}/{len(students)} students from {from_class_name} to {to_class_name}",
                'data': {
                    'batch_id': batch.id,
                    'promoted': promoted,
                    'total': len(students),
                    'errors': errors
                }
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk promotion error: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ── Export Students ────────────────────────────────────────

    @staticmethod
    def export_students_csv(school_id, class_name=None, status=None):
        """Export students to CSV string"""
        try:
            query = Student.query.filter_by(school_id=school_id)
            if class_name:
                query = query.filter_by(class_name=class_name)
            if status:
                query = query.filter_by(status=status)
            else:
                query = query.filter_by(is_active=True)

            students = query.order_by(Student.class_name, Student.roll_no).all()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['name', 'admission_no', 'class_name', 'section', 'roll_no',
                              'email', 'phone', 'gender', 'dob', 'parent_name', 'parent_phone',
                              'address', 'status'])

            for s in students:
                writer.writerow([
                    s.name, s.admission_no, s.class_name, s.section, s.roll_no,
                    s.email, s.phone, s.gender,
                    s.dob.isoformat() if s.dob else '',
                    s.parent_name, s.parent_phone, s.address,
                    s.status.value if s.status else 'active'
                ])

            return {
                'success': True,
                'data': {
                    'csv_data': output.getvalue(),
                    'total': len(students)
                }
            }
        except Exception as e:
            logger.error(f"Export students error: {str(e)}")
            return {'success': False, 'error': str(e)}
