from app.db.database import SessionLocal
from app.models.persistence import Dividend
from sqlalchemy import func, extract

db = SessionLocal()
try:
    results = db.query(
        extract('year', Dividend.date).label('year'),
        func.sum(Dividend.amount),
        func.count(Dividend.id)
    ).group_by('year').all()
    
    print("Database Dividend Summary:")
    for year, total, count in results:
        print(f"  Year {year}: ${total:,.2f} ({count} records)")
finally:
    db.close()
