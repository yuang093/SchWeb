from app.db.database import SessionLocal
from app.models.persistence import Dividend
from sqlalchemy import func

db = SessionLocal()
try:
    # Find records with same account, date, symbol, amount
    duplicates = db.query(
        Dividend.account_hash,
        Dividend.date,
        Dividend.symbol,
        Dividend.amount,
        func.count(Dividend.id)
    ).group_by(
        Dividend.account_hash,
        Dividend.date,
        Dividend.symbol,
        Dividend.amount
    ).having(func.count(Dividend.id) > 1).all()
    
    print(f"Found {len(duplicates)} duplicate groups.")
    for d in duplicates[:10]:
        print(f"  {d[1]} {d[2]} ${d[3]}: {d[4]} copies")
finally:
    db.close()
