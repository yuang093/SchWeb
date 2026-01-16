from app.db.database import SessionLocal
from app.models.persistence import Dividend
from sqlalchemy import func

def cleanup_duplicates():
    db = SessionLocal()
    account_hash = "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991"
    
    # 找出重複的組 (日期, 符號, 金額)
    # 我們保留 ID 較小的那一個 (通常是較早匯入的)
    dupes = db.query(
        Dividend.date,
        Dividend.symbol,
        Dividend.amount,
        func.min(Dividend.id).label('min_id')
    ).filter(Dividend.account_hash == account_hash).group_by(
        Dividend.date,
        Dividend.symbol,
        Dividend.amount
    ).having(func.count(Dividend.id) > 1).all()
    
    print(f"Found {len(dupes)} duplicate groups to clean.")
    
    total_deleted = 0
    for d in dupes:
        # 刪除除了 min_id 以外的所有相同記錄
        deleted = db.query(Dividend).filter(
            Dividend.account_hash == account_hash,
            Dividend.date == d.date,
            Dividend.symbol == d.symbol,
            Dividend.amount == d.amount,
            Dividend.id != d.min_id
        ).delete(synchronize_session=False)
        total_deleted += deleted
        
    db.commit()
    print(f"Cleanup complete. Deleted {total_deleted} duplicate records.")
    
    # 重新統計
    years = db.query(
        func.extract('year', Dividend.date).label('year'),
        func.sum(Dividend.amount).label('total')
    ).filter(Dividend.account_hash == account_hash).group_by('year').all()
    
    print("\nNew Yearly Statistics for 323:")
    grand_total = 0
    for y in years:
        print(f"  Year {int(y.year)}: ${y.total:,.2f}")
        grand_total += y.total
    print(f"  Grand Total: ${grand_total:,.2f}")
    
    db.close()

if __name__ == "__main__":
    cleanup_duplicates()
