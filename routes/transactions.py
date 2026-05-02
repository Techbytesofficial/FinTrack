from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Transaction, Budget
from datetime import datetime
from sqlalchemy import extract

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/')
@transactions_bp.route('/dashboard')
@login_required
def dashboard():
    view_type = request.args.get('view', 'month')
    selected_month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
    selected_year = request.args.get('year', datetime.now().year, type=int)

    try:
        selected_date = datetime.strptime(selected_month_str, '%Y-%m')
    except ValueError:
        selected_date = datetime.now()
        selected_month_str = selected_date.strftime('%Y-%m')

    # Get overall total balance (cumulative)
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='income').scalar() or 0.0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='expense').scalar() or 0.0
    total_balance = total_income - total_expense

    # Filter base for stats
    if view_type == 'year':
        filter_cond = (extract('year', Transaction.date) == selected_year)
        budget_filter = (Budget.month.like(f"{selected_year}-%"))
        period_label = str(selected_year)
    else:
        filter_cond = (extract('month', Transaction.date) == selected_date.month) & (extract('year', Transaction.date) == selected_date.year)
        budget_filter = (Budget.month == selected_month_str)
        period_label = selected_date.strftime('%b %Y')

    # Get stats
    income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        filter_cond
    ).scalar() or 0.0
    
    expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        filter_cond
    ).scalar() or 0.0
    
    # Recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(5).all()
    
    # Category-wise spending
    monthly_spending = db.session.query(
        Transaction.category, 
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        filter_cond
    ).group_by(Transaction.category).all()
    
    # Get budgets
    if view_type == 'year':
        yearly_budgets = db.session.query(
            Budget.category, 
            db.func.sum(Budget.limit_amount)
        ).filter(
            Budget.user_id == current_user.id,
            budget_filter
        ).group_by(Budget.category).all()
        budget_map = {b[0]: b[1] for b in yearly_budgets}
    else:
        budgets = Budget.query.filter_by(user_id=current_user.id, month=selected_month_str).all()
        budget_map = {b.category: b.limit_amount for b in budgets}
    
    alerts = []
    for cat, total in monthly_spending:
        if cat in budget_map:
            limit = budget_map[cat]
            percent = (total / limit) * 100
            if percent >= 100:
                alerts.append({'category': cat, 'status': 'Alert', 'percent': percent, 'level': 'danger'})
            elif percent >= 80:
                alerts.append({'category': cat, 'status': 'Warning', 'percent': percent, 'level': 'warning'})

    return render_template('dashboard.html', 
                           total_balance=total_balance,
                           balance=income - expense,
                           income=income, 
                           expense=expense, 
                           recent=recent_transactions,
                           alerts=alerts,
                           selected_month=selected_month_str,
                           selected_year=selected_year,
                           view_type=view_type,
                           period_label=period_label)

@transactions_bp.route('/transactions')
@login_required
def view_transactions():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    t_type = request.args.get('type')
    search = request.args.get('search')
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if category:
        query = query.filter_by(category=category)
    if t_type:
        query = query.filter_by(type=t_type)
    if search:
        query = query.filter(Transaction.notes.ilike(f'%{search}%') | Transaction.category.ilike(f'%{search}%'))
        
    pagination = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).paginate(page=page, per_page=10)
    
    categories = ['Salary', 'Freelance', 'Business', 'Investment', 'Gift', 'Food', 'Travel', 'Bills', 'Shopping', 'Health', 'Education', 'Entertainment', 'Other']
    
    return render_template('transactions.html', 
                           pagination=pagination, 
                           categories=categories,
                           selected_category=category,
                           selected_type=t_type,
                           search=search)

@transactions_bp.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        t_type = request.form.get('type')
        category = request.form.get('category')
        if category == 'Other':
            category = request.form.get('custom_category')
        date_str = request.form.get('date')
        notes = request.form.get('notes')
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
        
        new_transaction = Transaction(
            user_id=current_user.id,
            amount=amount,
            type=t_type,
            category=category,
            date=date,
            notes=notes
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions.dashboard'))
        
    categories_income = ['Salary', 'Freelance', 'Business', 'Investment', 'Gift', 'Other']
    categories_expense = ['Food', 'Travel', 'Bills', 'Shopping', 'Health', 'Education', 'Entertainment', 'Other']
    
    return render_template('add_transaction.html', 
                           categories_income=categories_income, 
                           categories_expense=categories_expense)

@transactions_bp.route('/transaction/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('transactions.view_transactions'))
        
    if request.method == 'POST':
        transaction.amount = float(request.form.get('amount'))
        transaction.type = request.form.get('type')
        transaction.category = request.form.get('category')
        if transaction.category == 'Other':
            transaction.category = request.form.get('custom_category')
        date_str = request.form.get('date')
        transaction.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        transaction.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Transaction updated!', 'success')
        return redirect(url_for('transactions.view_transactions'))
        
    categories_income = ['Salary', 'Freelance', 'Business', 'Investment', 'Gift', 'Other']
    categories_expense = ['Food', 'Travel', 'Bills', 'Shopping', 'Health', 'Education', 'Entertainment', 'Other']
    
    return render_template('add_transaction.html', 
                           transaction=transaction,
                           categories_income=categories_income, 
                           categories_expense=categories_expense)

@transactions_bp.route('/transaction/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('transactions.view_transactions'))
        
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted.', 'success')
    return redirect(url_for('transactions.view_transactions'))

@transactions_bp.route('/budget', methods=['GET', 'POST'])
@login_required
def manage_budget():
    if request.method == 'POST':
        category = request.form.get('category')
        if category == 'Other':
            category = request.form.get('custom_category')
        amount = float(request.form.get('amount'))
        month = request.form.get('month') # YYYY-MM
        
        budget = Budget.query.filter_by(user_id=current_user.id, category=category, month=month).first()
        if budget:
            budget.limit_amount = amount
        else:
            new_budget = Budget(user_id=current_user.id, category=category, limit_amount=amount, month=month)
            db.session.add(new_budget)
            
        db.session.commit()
        flash('Budget updated!', 'success')
        return redirect(url_for('transactions.dashboard'))
        
    categories_expense = ['Food', 'Travel', 'Bills', 'Shopping', 'Health', 'Education', 'Entertainment', 'Other']
    return render_template('manage_budget.html', categories=categories_expense)
