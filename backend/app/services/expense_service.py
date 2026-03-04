"""
Expense Management Service
Track expenses, salaries, maintenance costs, financial overview
"""
from app.extensions import db
from app.models.expense import Expense, ExpenseCategory, SalaryStructure, SalaryPayment
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
import logging

logger = logging.getLogger(__name__)


class ExpenseService:
    """Service for expense management"""

    # ── Expense Categories ─────────────────────────────────────

    @staticmethod
    def create_category(school_id, name, code, description=None, parent_category_id=None, budget_amount=0):
        try:
            category = ExpenseCategory(
                school_id=school_id,
                name=name,
                code=code,
                description=description,
                parent_category_id=parent_category_id,
                budget_amount=budget_amount
            )
            db.session.add(category)
            db.session.commit()
            return {'success': True, 'data': category.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create category error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_categories(school_id):
        try:
            categories = ExpenseCategory.query.filter_by(
                school_id=school_id, parent_category_id=None, is_active=True
            ).all()
            return {'success': True, 'data': [c.to_dict() for c in categories]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── Expenses CRUD ──────────────────────────────────────────

    @staticmethod
    def create_expense(school_id, created_by_id, **kwargs):
        try:
            expense_date = kwargs.get('expense_date')
            if isinstance(expense_date, str):
                expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()

            expense = Expense(
                school_id=school_id,
                branch_id=kwargs.get('branch_id'),
                category_id=kwargs.get('category_id'),
                title=kwargs.get('title'),
                description=kwargs.get('description'),
                amount=kwargs.get('amount'),
                expense_date=expense_date or date.today(),
                payment_method=kwargs.get('payment_method', 'cash'),
                reference_number=kwargs.get('reference_number'),
                receipt_url=kwargs.get('receipt_url'),
                vendor_name=kwargs.get('vendor_name'),
                vendor_contact=kwargs.get('vendor_contact'),
                status='pending',
                created_by_id=created_by_id,
                is_recurring=kwargs.get('is_recurring', False),
                recurring_frequency=kwargs.get('recurring_frequency'),
                tags=kwargs.get('tags', [])
            )
            db.session.add(expense)
            db.session.commit()
            return {'success': True, 'data': expense.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create expense error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_expenses(school_id, page=1, per_page=20, category_id=None,
                     status=None, start_date=None, end_date=None, branch_id=None):
        try:
            query = Expense.query.filter_by(school_id=school_id)
            if category_id:
                query = query.filter_by(category_id=category_id)
            if status:
                query = query.filter_by(status=status)
            if branch_id:
                query = query.filter_by(branch_id=branch_id)
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date >= start_date)
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date <= end_date)

            paginated = query.order_by(Expense.expense_date.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            return {
                'success': True,
                'data': {
                    'expenses': [e.to_dict() for e in paginated.items],
                    'total': paginated.total,
                    'page': page,
                    'pages': paginated.pages
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def approve_expense(school_id, expense_id, approved_by_id):
        try:
            expense = Expense.query.filter_by(school_id=school_id, id=expense_id).first()
            if not expense:
                return {'success': False, 'error': 'Expense not found'}
            expense.status = 'approved'
            expense.approved_by_id = approved_by_id
            expense.approved_at = datetime.utcnow()
            db.session.commit()
            return {'success': True, 'message': 'Expense approved'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def reject_expense(school_id, expense_id):
        try:
            expense = Expense.query.filter_by(school_id=school_id, id=expense_id).first()
            if not expense:
                return {'success': False, 'error': 'Expense not found'}
            expense.status = 'rejected'
            db.session.commit()
            return {'success': True, 'message': 'Expense rejected'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    # ── Financial Overview ─────────────────────────────────────

    @staticmethod
    def get_financial_overview(school_id, year=None, month=None):
        try:
            if not year:
                year = date.today().year

            # Monthly expense totals
            query = db.session.query(
                extract('month', Expense.expense_date).label('month'),
                func.sum(Expense.amount).label('total')
            ).filter(
                Expense.school_id == school_id,
                extract('year', Expense.expense_date) == year,
                Expense.status.in_(['approved', 'paid'])
            ).group_by(extract('month', Expense.expense_date))

            monthly_expenses = {int(r.month): float(r.total) for r in query.all()}

            # Category-wise totals
            cat_query = db.session.query(
                ExpenseCategory.name,
                func.sum(Expense.amount).label('total')
            ).join(ExpenseCategory, Expense.category_id == ExpenseCategory.id
            ).filter(
                Expense.school_id == school_id,
                extract('year', Expense.expense_date) == year,
                Expense.status.in_(['approved', 'paid'])
            ).group_by(ExpenseCategory.name)

            category_totals = {r.name: float(r.total) for r in cat_query.all()}

            # Total for year
            total_expense = sum(monthly_expenses.values())

            # Salary totals
            salary_query = db.session.query(
                func.sum(SalaryPayment.net_amount)
            ).filter(
                SalaryPayment.school_id == school_id,
                SalaryPayment.year == year,
                SalaryPayment.status.in_(['processed', 'paid'])
            ).scalar()

            total_salary = float(salary_query) if salary_query else 0

            # Budget vs actual for categories
            budget_query = ExpenseCategory.query.filter_by(school_id=school_id, is_active=True).all()
            budget_comparison = []
            for cat in budget_query:
                spent = category_totals.get(cat.name, 0)
                budget = float(cat.budget_amount or 0)
                budget_comparison.append({
                    'category': cat.name,
                    'budget': budget,
                    'spent': spent,
                    'remaining': budget - spent,
                    'utilization_pct': round((spent / budget * 100), 1) if budget > 0 else 0
                })

            return {
                'success': True,
                'data': {
                    'year': year,
                    'total_expenses': total_expense,
                    'total_salaries': total_salary,
                    'grand_total': total_expense + total_salary,
                    'monthly_expenses': monthly_expenses,
                    'category_totals': category_totals,
                    'budget_comparison': budget_comparison
                }
            }
        except Exception as e:
            logger.error(f"Financial overview error: {str(e)}")
            return {'success': False, 'error': str(e)}


class SalaryService:
    """Service for staff salary management"""

    @staticmethod
    def create_salary_structure(school_id, **kwargs):
        try:
            structure = SalaryStructure(school_id=school_id, **kwargs)
            db.session.add(structure)
            db.session.commit()
            return {'success': True, 'data': structure.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_salary_structures(school_id):
        try:
            structures = SalaryStructure.query.filter_by(school_id=school_id, is_active=True).all()
            return {'success': True, 'data': [s.to_dict() for s in structures]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def process_salary(school_id, staff_id, month, year, processed_by_id,
                       salary_structure_id=None, bonus=0, extra_deductions=0, remarks=None):
        try:
            existing = SalaryPayment.query.filter_by(
                school_id=school_id, staff_id=staff_id, month=month, year=year
            ).first()
            if existing:
                return {'success': False, 'error': f'Salary already processed for {month}/{year}'}

            structure = None
            if salary_structure_id:
                structure = SalaryStructure.query.get(salary_structure_id)

            basic = float(structure.basic_salary) if structure else 0
            allowances = float(structure.gross_salary - float(structure.basic_salary)) if structure else 0
            deductions = float(structure.total_deductions) + float(extra_deductions) if structure else float(extra_deductions)
            net = basic + allowances + float(bonus) - deductions

            payment = SalaryPayment(
                school_id=school_id,
                staff_id=staff_id,
                salary_structure_id=salary_structure_id,
                month=month,
                year=year,
                basic_amount=basic,
                allowances=allowances,
                deductions=deductions,
                bonus=bonus,
                net_amount=net,
                status='processed',
                processed_by_id=processed_by_id,
                remarks=remarks
            )
            db.session.add(payment)
            db.session.commit()
            return {'success': True, 'data': payment.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def bulk_process_salaries(school_id, month, year, processed_by_id, staff_ids=None):
        """Process salary for all staff in one go"""
        try:
            from app.models.user import User
            query = User.query.filter_by(school_id=school_id, is_active=True)
            if staff_ids:
                query = query.filter(User.id.in_(staff_ids))

            staff_list = query.all()
            results = {'processed': 0, 'skipped': 0, 'errors': []}

            for staff in staff_list:
                existing = SalaryPayment.query.filter_by(
                    school_id=school_id, staff_id=staff.id, month=month, year=year
                ).first()
                if existing:
                    results['skipped'] += 1
                    continue

                try:
                    payment = SalaryPayment(
                        school_id=school_id,
                        staff_id=staff.id,
                        month=month,
                        year=year,
                        basic_amount=0,
                        allowances=0,
                        deductions=0,
                        bonus=0,
                        net_amount=0,
                        status='pending',
                        processed_by_id=processed_by_id
                    )
                    db.session.add(payment)
                    results['processed'] += 1
                except Exception as e:
                    results['errors'].append({'staff_id': staff.id, 'error': str(e)})

            db.session.commit()
            return {
                'success': True,
                'message': f"Processed: {results['processed']}, Skipped: {results['skipped']}",
                'data': results
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_salary_payments(school_id, month=None, year=None, staff_id=None, status=None):
        try:
            query = SalaryPayment.query.filter_by(school_id=school_id)
            if month:
                query = query.filter_by(month=month)
            if year:
                query = query.filter_by(year=year)
            if staff_id:
                query = query.filter_by(staff_id=staff_id)
            if status:
                query = query.filter_by(status=status)

            payments = query.order_by(SalaryPayment.year.desc(), SalaryPayment.month.desc()).all()
            return {'success': True, 'data': [p.to_dict() for p in payments]}
        except Exception as e:
            return {'success': False, 'error': str(e)}
