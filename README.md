# 📊 FinTrack - Personal Finance Tracker

FinTrack is a powerful and intuitive personal finance management application built with Flask. It helps users track their income, expenses, and budgets while providing insightful visualizations of their financial health.

## ✨ Features

- **🔐 Secure Authentication**: User registration and login system with encrypted passwords and CSRF protection.
- **💸 Transaction Management**: Easily record income and expenses with categories and dates.
- **📅 Dashboard Analytics**: A visual overview of your financial status using interactive charts.
- **📈 Detailed Reports**: Filter transactions by date range and view spending patterns.
- **💰 Budgeting**: Set monthly budgets for different categories and track your progress.
- **📄 PDF Exports**: Generate professional PDF reports of your financial data.
- **📱 Responsive Design**: Fully optimized for both desktop and mobile devices.

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: Chart.js
- **PDF Generation**: ReportLab
- **Security**: Flask-Login, Flask-WTF

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Techbytesofficial/FinTrack.git
   cd FinTrack
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the app**:
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```text
FinTrack/
├── instance/               # Local database storage
├── routes/                 # Flask Blueprints for different features
│   ├── auth.py             # User authentication logic
│   ├── reports.py          # Financial reporting logic
│   └── transactions.py     # Transaction management logic
├── static/                 # Static assets (CSS, JS, Images)
├── templates/              # HTML templates (Jinja2)
├── app.py                  # Application entry point
├── models.py               # Database models
└── requirements.txt        # Project dependencies
```

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---
*Built with ❤️ by [Antigravity](https://github.com/Techbytesofficial)*
