// Default Chart.js configurations
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";

let monthlyChart = null;
let categoryChart = null;

function setReportView(view) {
    document.getElementById('reportView').value = view;
    
    // Update toggle classes
    document.getElementById('toggleMonth').classList.toggle('active', view === 'month');
    document.getElementById('toggleYear').classList.toggle('active', view === 'year');
    
    updateFilters();
}

function updateFilters() {
    const view = document.getElementById('reportView').value;
    const monthContainer = document.getElementById('monthContainer');
    const yearContainer = document.getElementById('yearContainer');
    
    if (view === 'month') {
        monthContainer.style.display = 'flex';
        yearContainer.style.display = 'none';
    } else {
        monthContainer.style.display = 'none';
        yearContainer.style.display = 'flex';
    }
    loadAllCharts();
}

async function loadAllCharts() {
    const view = document.getElementById('reportView').value;
    const month = document.getElementById('reportMonth').value;
    const year = view === 'month' ? month.split('-')[0] : document.getElementById('reportYear').value;
    
    // Update Titles
    if (view === 'month') {
        const monthName = new Date(month + '-01').toLocaleString('default', { month: 'long', year: 'numeric' });
        document.getElementById('categoryTitle').textContent = `Spending by Category (${monthName})`;
        document.getElementById('trendTitle').textContent = `Monthly Trend (${year})`;
    } else {
        document.getElementById('categoryTitle').textContent = `Spending by Category (Year ${year})`;
        document.getElementById('trendTitle').textContent = `Monthly Trend (${year})`;
    }

    // 1. Monthly Income vs Expenses (Always show the year's trend)
    const monthlyRes = await fetch(`/api/monthly-data?year=${year}`);
    const monthlyData = await monthlyRes.json();
    
    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(document.getElementById('monthlyChart'), {
        type: 'bar',
        data: {
            labels: monthlyData.labels,
            datasets: [
                {
                    label: 'Income',
                    data: monthlyData.income,
                    backgroundColor: 'rgba(16, 185, 129, 0.6)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Expenses',
                    data: monthlyData.expense,
                    backgroundColor: 'rgba(239, 68, 68, 0.6)',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { position: 'top' } }
        }
    });

    // 2. Category Distribution
    const categoryRes = await fetch(`/api/category-data?view=${view}&month=${month}&year=${year}`);
    const categoryData = await categoryRes.json();
    
    if (categoryChart) categoryChart.destroy();
    categoryChart = new Chart(document.getElementById('categoryChart'), {
        type: 'doughnut',
        data: {
            labels: categoryData.labels,
            datasets: [{
                data: categoryData.values,
                backgroundColor: [
                    '#6366f1', '#ec4899', '#8b5cf6', '#10b981', 
                    '#f59e0b', '#ef4444', '#06b6d4', '#f43f5e'
                ],
                borderWidth: 0,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { position: 'right', labels: { padding: 20 } }
            }
        }
    });

    // 3. Summary Stats (Calculate based on category data)
    const totalExpense = categoryData.values.reduce((a, b) => a + b, 0);
    const totalIncome = monthlyData.income.reduce((a, b) => a + b, 0); // This is yearly or monthly?
    
    // For summary, let's use the specific income for the selected period if monthly
    let periodIncome = totalIncome;
    if (view === 'month') {
        const mIdx = parseInt(month.split('-')[1]) - 1;
        periodIncome = monthlyData.income[mIdx];
    }

    // Avg Expense
    const days = (view === 'month') ? 30 : 365; // Simplified
    document.getElementById('avgExpense').textContent = `$${(totalExpense / days).toFixed(2)}`;
    
    // Top Category
    if (categoryData.values.length > 0) {
        const maxIdx = categoryData.values.indexOf(Math.max(...categoryData.values));
        document.getElementById('topCategory').textContent = categoryData.labels[maxIdx];
    } else {
        document.getElementById('topCategory').textContent = 'N/A';
    }
    
    // Savings Rate
    const savingsRate = periodIncome > 0 ? ((periodIncome - totalExpense) / periodIncome * 100) : 0;
    document.getElementById('savingsRate').textContent = `${savingsRate.toFixed(1)}%`;
    document.getElementById('savingsRate').style.color = savingsRate > 0 ? 'var(--success)' : 'var(--danger)';
}

document.addEventListener('DOMContentLoaded', loadAllCharts);
