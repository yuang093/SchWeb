import os
import sys
from datetime import date
from sqlalchemy import func, extract

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.persistence import Dividend

def audit_dividends():
    db = SessionLocal()
    account_hash = "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991"
    
    lines = []
    def log(msg):
        print(msg)
        lines.append(msg)

    log(f"=== Dividend Audit for Account 323 ({account_hash[:10]}...) ===")
    
    # 1. 按年份統計
    years = db.query(
        extract('year', Dividend.date).label('year'),
        func.sum(Dividend.amount).label('total'),
        func.count(Dividend.id).label('count')
    ).filter(Dividend.account_hash == account_hash).group_by('year').order_by('year').all()
    
    log("\n[1] Yearly Statistics:")
    for y in years:
        log(f"  Year {int(y.year)}: ${y.total:,.2f} ({y.count} records)")
    
    # 2. 檢查重複 (同一天、同金額、同描述)
    duplicates = db.query(
        Dividend.date,
        Dividend.amount,
        Dividend.description,
        func.count(Dividend.id).label('count')
    ).filter(Dividend.account_hash == account_hash).group_by(
        Dividend.date,
        Dividend.amount,
        Dividend.description
    ).having(func.count(Dividend.id) > 1).all()
    
    log(f"\n[2] Found {len(duplicates)} Duplicate Groups (Same Date, Amount, Description):")
    for d in duplicates[:10]: # 只列出前 10 個
        log(f"  Date: {d.date}, Amount: ${d.amount}, Count: {d.count}, Desc: {d.description}")
    
    # 3. 2023 年深度分析
    log("\n[3] 2023 Deep Dive (Checking for TD/Schwab overlap):")
    div_2023 = db.query(Dividend).filter(
        Dividend.account_hash == account_hash,
        extract('year', Dividend.date) == 2023
    ).order_by(Dividend.date).all()
    
    td_count = 0
    schwab_count = 0
    td_total = 0
    schwab_total = 0
    
    for div in div_2023:
        desc = div.description or ""
        # 簡易判定：Schwab 通常含 "Qual Div" 或 "Reinvest"，且有 symbol。
        # TD 歷史資料可能格式不同
        is_schwab = any(k in desc for k in ["Qual Div", "Reinvest", "DRIP"])
        
        if is_schwab:
            schwab_count += 1
            schwab_total += div.amount
        else:
            td_count += 1
            td_total += div.amount
            
    log(f"  2023 Schwab-like: {schwab_count} records, ${schwab_total:,.2f}")
    log(f"  2023 TD-like: {td_count} records, ${td_total:,.2f}")
    
    # 4. 檢查是否有「同一天、同金額、但描述不同」的疑似重複 (例如不同平台匯入)
    potential_dupes = db.query(
        Dividend.date,
        Dividend.amount,
        func.count(Dividend.id).label('count')
    ).filter(Dividend.account_hash == account_hash).group_by(
        Dividend.date,
        Dividend.amount
    ).having(func.count(Dividend.id) > 1).all()
    
    log(f"\n[4] Found {len(potential_dupes)} Potential Duplicates (Same Date & Amount, different desc):")
    for p in potential_dupes[:5]:
        records = db.query(Dividend).filter(
            Dividend.account_hash == account_hash,
            Dividend.date == p.date,
            Dividend.amount == p.amount
        ).all()
        log(f"  Date: {p.date}, Amount: ${p.amount}")
        for r in records:
            log(f"    - ID: {r.id}, Desc: {r.description}")

    with open("audit_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    db.close()

if __name__ == "__main__":
    audit_dividends()
