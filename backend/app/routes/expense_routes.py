"""
Expense Management Routes
Expense tracking, salary management, financial overview
"""
from flask import Blueprint, request
from app.core.auth import token_required, permission_required
from app.core.response import success_response, error_response
from app.core.middleware import admin_required, limit_request_size
from app.services.expense_service import ExpenseService, SalaryService
import logging

logger = logging.getLogger(__name__)

expense_bp = Blueprint('expenses', __name__, url_prefix='/expenses')


# ── Categories ─────────────────────────────────────────────

@expense_bp.route('/categories', methods=['POST'])
@token_required
@permission_required('manage_expense_categories')
def create_category(current_user):
    try:
        data = request.get_json()
        result = ExpenseService.create_category(
            school_id=current_user.school_id,
            name=data.get('name'),
            code=data.get('code'),
            description=data.get('description'),
            parent_category_id=data.get('parent_category_id'),
            budget_amount=data.get('budget_amount', 0)
        )
        if result['success']:
            return success_response("Category created", result['data'], 201)
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/categories', methods=['GET'])
@token_required
@permission_required('view_expenses', 'manage_expense_categories')
def get_categories(current_user):
    try:
        result = ExpenseService.get_categories(current_user.school_id)
        if result['success']:
            return success_response("Categories", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ── Expenses CRUD ──────────────────────────────────────────

@expense_bp.route('', methods=['POST'])
@token_required
@permission_required('create_expense')
def create_expense(current_user):
    try:
        data = request.get_json()
        result = ExpenseService.create_expense(
            school_id=current_user.school_id,
            created_by_id=current_user.id,
            **data
        )
        if result['success']:
            return success_response("Expense created", result['data'], 201)
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('', methods=['GET'])
@token_required
@permission_required('view_expenses')
def get_expenses(current_user):
    try:
        result = ExpenseService.get_expenses(
            school_id=current_user.school_id,
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 20, type=int),
            category_id=request.args.get('category_id', type=int),
            status=request.args.get('status'),
            start_date=request.args.get('start_date'),
            end_date=request.args.get('end_date'),
            branch_id=request.args.get('branch_id', type=int)
        )
        if result['success']:
            return success_response("Expenses", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/<int:expense_id>/approve', methods=['PUT'])
@token_required
@permission_required('approve_expense')
def approve_expense(current_user, expense_id):
    try:
        result = ExpenseService.approve_expense(
            current_user.school_id, expense_id, current_user.id
        )
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/<int:expense_id>/reject', methods=['PUT'])
@token_required
@permission_required('reject_expense')
def reject_expense(current_user, expense_id):
    try:
        result = ExpenseService.reject_expense(current_user.school_id, expense_id)
        if result['success']:
            return success_response(result['message'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ── Financial Overview ─────────────────────────────────────

@expense_bp.route('/overview', methods=['GET'])
@token_required
@permission_required('view_financial_overview', 'view_expenses')
def financial_overview(current_user):
    try:
        result = ExpenseService.get_financial_overview(
            school_id=current_user.school_id,
            year=request.args.get('year', type=int),
            month=request.args.get('month', type=int)
        )
        if result['success']:
            return success_response("Financial overview", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


# ── Salary Management ─────────────────────────────────────

@expense_bp.route('/salary/structures', methods=['POST'])
@token_required
@permission_required('manage_salary_structures')
def create_salary_structure(current_user):
    try:
        data = request.get_json()
        result = SalaryService.create_salary_structure(
            school_id=current_user.school_id, **data
        )
        if result['success']:
            return success_response("Salary structure created", result['data'], 201)
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/salary/structures', methods=['GET'])
@token_required
@permission_required('view_salary_payments', 'manage_salary_structures')
def get_salary_structures(current_user):
    try:
        result = SalaryService.get_salary_structures(current_user.school_id)
        if result['success']:
            return success_response("Salary structures", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/salary/process', methods=['POST'])
@token_required
@permission_required('process_salary')
def process_salary(current_user):
    try:
        data = request.get_json()
        result = SalaryService.process_salary(
            school_id=current_user.school_id,
            staff_id=data.get('staff_id'),
            month=data.get('month'),
            year=data.get('year'),
            processed_by_id=current_user.id,
            salary_structure_id=data.get('salary_structure_id'),
            bonus=data.get('bonus', 0),
            extra_deductions=data.get('extra_deductions', 0),
            remarks=data.get('remarks')
        )
        if result['success']:
            return success_response("Salary processed", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/salary/bulk-process', methods=['POST'])
@token_required
@permission_required('process_salary')
@limit_request_size(500)
def bulk_process_salaries(current_user):
    try:
        data = request.get_json()
        result = SalaryService.bulk_process_salaries(
            school_id=current_user.school_id,
            month=data.get('month'),
            year=data.get('year'),
            processed_by_id=current_user.id,
            staff_ids=data.get('staff_ids')
        )
        if result['success']:
            return success_response(result['message'], result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)


@expense_bp.route('/salary/payments', methods=['GET'])
@token_required
@permission_required('view_salary_payments')
def get_salary_payments(current_user):
    try:
        result = SalaryService.get_salary_payments(
            school_id=current_user.school_id,
            month=request.args.get('month', type=int),
            year=request.args.get('year', type=int),
            staff_id=request.args.get('staff_id', type=int),
            status=request.args.get('status')
        )
        if result['success']:
            return success_response("Salary payments", result['data'])
        return error_response(result.get('error'), 400)
    except Exception as e:
        return error_response(str(e), 500)
