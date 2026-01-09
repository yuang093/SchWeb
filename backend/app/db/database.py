from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# 使用絕對路徑
# 取得 database.py 所在的絕對位置，並推算出 backend 根目錄
BASE_DIR = Path(__file__).resolve().parent.parent.parent
db_path = BASE_DIR / "sql_app.db"

# 資料庫檔案路徑
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# 建立資料庫引擎
# connect_args={"check_same_thread": False} 是 SQLite 特有的參數，允許在多個執行緒中使用同一個連線
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 建立 SessionLocal 類別，用於建立資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別，用於定義資料模型
Base = declarative_base()

# 獲取資料庫會話的相依性 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
