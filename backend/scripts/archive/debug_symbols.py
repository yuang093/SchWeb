from app.db.database import SessionLocal
from app.models.persistence import Dividend
from datetime import date

db = SessionLocal()
try:
    target_date = date(2024, 4, 30)
    amount = 110.88
    records = db.query(Dividend).filter(
        Dividend.date == target_date,
        Dividend.amount == amount
    ).all()
    print(f"Records on {target_date} with amount ${amount}:")
    for r in records:
        print(f"  ID: {r.id}, Symbol: '{r.symbol}', Desc: '{r.description}'")
finally:
    db.close()
