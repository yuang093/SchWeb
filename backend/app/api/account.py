from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from app.services.repository import account_repo

router = APIRouter()

@router.get("/list")
async def get_account_list():
    """
    獲取所有可用的帳戶清單 (用於下拉選單)
    """
    return account_repo.get_account_list()

@router.get("/summary")
async def get_account_summary(account_hash: Optional[str] = Query(None)):
    """
    獲取指定帳戶的摘要資訊
    """
    return account_repo.get_account_summary(account_hash)

@router.get("/positions")
async def get_account_positions(account_hash: Optional[str] = Query(None)):
    """
    獲取指定帳戶的持倉清單
    """
    return account_repo.get_positions(account_hash)

@router.get("/history")
async def get_account_history():
    """
    獲取帳戶資產歷史數據 (用於圖表)
    """
    return account_repo.get_history_from_db()
