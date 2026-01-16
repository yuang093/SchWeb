from app.db.database import SessionLocal
from app.models.persistence import Dividend
from datetime import date

db = SessionLocal()
try:
    target_date = date(2026, 1, 14)
    results = db.query(Dividend).filter(Dividend.date == target_date).all()
    print(f"Dividends on {target_date}:")
    for r in results:
        print(f"  ID: {r.id}, Symbol: {r.symbol}, Amount: {r.amount}, Account: {r.account_hash[:10]}...")
finally:
    db.close()
