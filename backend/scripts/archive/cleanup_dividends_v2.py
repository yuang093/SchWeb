from app.db.database import SessionLocal
from app.models.persistence import Dividend
from sqlalchemy import func

def cleanup_duplicates():
    db = SessionLocal()
    account_hash = "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991"
    
    # 找出重複的組 (日期, 金額) - 忽略 Symbol
    # 我們優先保留有明確 Symbol (非 CURRENCY_USD) 的記錄
    dupe_groups = db.query(
        Dividend.date,
        Dividend.amount,
        func.count(Dividend.id).label('cnt')
    ).filter(Dividend.account_hash == account_hash).group_by(
        Dividend.date,
        Dividend.amount
    ).having(func.count(Dividend.id) > 1).all()
    
    print(f"Found {len(dupe_groups)} potential duplicate groups (Date+Amount match).")
    
    total_deleted = 0
    for g in dupe_groups:
        records = db.query(Dividend).filter(
            Dividend.account_hash == account_hash,
            Dividend.date == g.date,
            Dividend.amount == g.amount
        ).order_by(Dividend.symbol != 'CURRENCY_USD', Dividend.id).all()
        
        # 排序後，第一個應該是我們想保留的 (優先保留非 CURRENCY_USD，或 ID 最小的)
        # 其實 order_by(Dividend.symbol != 'CURRENCY_USD' DESC) 會把 True 排在前面
        # 所以我們應該用 DESC
        records = db.query(Dividend).filter(
            Dividend.account_hash == account_hash,
            Dividend.date == g.date,
            Dividend.amount == g.amount
        ).all()
        
        # 挑選出要保留的一個
        # 策略：如果有包含 'Qual Div' 的描述，優先保留
        # 否則如果有 Symbol 不是 CURRENCY_USD，優先保留
        to_keep = records[0]
        for r in records:
            if r.symbol != 'CURRENCY_USD':
                to_keep = r
                break
        
        # 刪除其餘的
        for r in records:
            if r.id != to_keep.id:
                db.delete(r)
                total_deleted += 1
                
    db.commit()
    print(f"Cleanup complete. Deleted {total_deleted} duplicate records.")
    
    # 重新統計
    years = db.query(
        func.extract('year', Dividend.date).label('year'),
        func.sum(Dividend.amount).label('total')
    ).filter(Dividend.account_hash == account_hash).group_by('year').all()
    
    print("\nFinal Yearly Statistics for 323:")
    grand_total = 0
    for y in years:
        print(f"  Year {int(y.year)}: ${y.total:,.2f}")
        grand_total += y.total
    print(f"  Grand Total: ${grand_total:,.2f}")
    
    db.close()

if __name__ == "__main__":
    cleanup_duplicates()
