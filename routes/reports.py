import csv
import io
from flask import Blueprint, render_template, jsonify, send_file, request
from flask_login import login_required, current_user
from models import db, Transaction
from sqlalchemy import extract, func
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def view_reports():
    now = datetime.now()
    return render_template('reports.html', 
                           now_month=now.strftime('%Y-%m'),
                           now_year=now.year)

@reports_bp.route('/api/balance')
@login_required
def get_balance_api():
    income = db.session.query(func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='income').scalar() or 0.0
    expense = db.session.query(func.sum(Transaction.amount)).filter_by(user_id=current_user.id, type='expense').scalar() or 0.0
    balance = income - expense
    return jsonify({
        'income': float(income),
        'expense': float(expense),
        'balance': float(balance)
    })

@reports_bp.route('/api/category-data')
@login_required
def get_category_data():
    view_type = request.args.get('view', 'month')
    selected_month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
    selected_year = request.args.get('year', datetime.now().year, type=int)

    if view_type == 'year':
        filter_cond = (extract('year', Transaction.date) == selected_year)
    else:
        try:
            sel_date = datetime.strptime(selected_month_str, '%Y-%m')
            filter_cond = (extract('month', Transaction.date) == sel_date.month) & (extract('year', Transaction.date) == sel_date.year)
        except:
            now = datetime.now()
            filter_cond = (extract('month', Transaction.date) == now.month) & (extract('year', Transaction.date) == now.year)

    results = db.session.query(
        Transaction.category, 
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        filter_cond
    ).group_by(Transaction.category).all()
    
    return jsonify({
        'labels': [r[0] for r in results],
        'values': [float(r[1]) for r in results]
    })

@reports_bp.route('/api/monthly-data')
@login_required
def get_monthly_data():
    year = request.args.get('year', datetime.now().year, type=int)
    
    income_data = db.session.query(
        extract('month', Transaction.date), 
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        extract('year', Transaction.date) == year
    ).group_by(extract('month', Transaction.date)).all()
    
    expense_data = db.session.query(
        extract('month', Transaction.date), 
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('year', Transaction.date) == year
    ).group_by(extract('month', Transaction.date)).all()
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    income_values = [0] * 12
    expense_values = [0] * 12
    
    for m, val in income_data:
        income_values[int(m)-1] = float(val)
    for m, val in expense_data:
        expense_values[int(m)-1] = float(val)
        
    return jsonify({
        'labels': months,
        'income': income_values,
        'expense': expense_values
    })

@reports_bp.route('/export/csv')
@login_required
def export_csv():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Type', 'Amount', 'Notes'])
    
    for t in transactions:
        writer.writerow([t.date, t.category, t.type, t.amount, t.notes])
        
    output.seek(0)
    filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route('/export/pdf')
@login_required
def export_pdf():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph(f"Financial Report - {current_user.username}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Summary Table
    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')
    summary_data = [
        ['Total Income', f"${income:.2f}"],
        ['Total Expense', f"${expense:.2f}"],
        ['Net Balance', f"${(income - expense):.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[150, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    
    # Transaction Table
    data = [['Date', 'Category', 'Type', 'Amount']]
    for t in transactions:
        data.append([t.date.strftime('%Y-%m-%d'), t.category, t.type.capitalize(), f"${t.amount:.2f}"])
        
    t_table = Table(data, colWidths=[100, 150, 80, 80])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(t_table)
    
    doc.build(elements)
    buffer.seek(0)
    filename = f"report_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
