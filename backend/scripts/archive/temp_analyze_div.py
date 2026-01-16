import csv
from datetime import datetime

file_path = 'backend/data/yuang_XXX323_Transactions_20260115-075740.csv'
div_keywords = ['Qual Div Reinvest', 'Qualified Dividend', 'Non-Qualified Div', 'Reinvest Dividend', 'Pr Yr Div Reinvest']

totals = {2024: 0.0, 2025: 0.0, 2026: 0.0, 'All': 0.0}

with open(file_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        action = row['Action']
        amount_str = row['Amount'].replace('$', '').replace(',', '').replace('\"', '')
        try:
            amount = float(amount_str)
        except ValueError:
            continue
            
        # We only care about the positive 'income' part for dividends
        if any(kw in action for kw in div_keywords) and amount > 0:
            date_str = row['Date'].split(' as of ')[0]
            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            year = date_obj.year
            
            totals['All'] += amount
            if year in totals:
                totals[year] += amount

with open('div_analysis.txt', 'w') as out:
    out.write(f'Dividend Totals Analysis:\n')
    for k, v in totals.items():
        out.write(f'  {k}: ${v:,.2f}\n')
