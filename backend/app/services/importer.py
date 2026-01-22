import csv
import io
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.persistence import Dividend, TradeHistory, AssetHistory, HoldingSnapshot, HistoricalBalance
from app.services.schwab_client import schwab_client

class ImporterService:
    def __init__(self):
        self.div_keywords = [
            'qual div reinvest', 'qualified dividend', 'non-qualified div', 
            'reinvest dividend', 'pr yr div reinvest', 'dividend'
        ]

    def _parse_amount(self, amount_str: Optional[str]) -> float:
        if not amount_str:
            return 0.0
        # 移除引號、金錢符號、逗號
        clean_str = str(amount_str).replace('"', '').replace('$', '').replace(',', '').strip()
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime.date]:
        if not date_str:
            return None
        try:
            # 嘉信 CSV 可能包含 "MM/DD/YYYY" 或 "MM/DD/YYYY as of ..."
            # 移除引號
            clean_date = str(date_str).replace('"', '').split(' as of ')[0].strip()
            return datetime.strptime(clean_date, '%m/%d/%Y').date()
        except ValueError:
            try:
                # 嘗試 ISO 格式
                return datetime.strptime(clean_date[:10], '%Y-%m-%d').date()
            except ValueError:
                return None

    def _get_account_hash_from_filename(self, filename: str) -> Optional[str]:
        """從檔名識別帳號末三碼並對應 hash"""
        try:
            accs = schwab_client.get_linked_accounts()
            for acc in accs:
                num_suffix = acc['account_number'][-3:]
                if num_suffix in filename:
                    return acc['hash_value']
        except Exception as e:
            print(f"Error mapping account from filename {filename}: {e}")
        
        # 專案特定 fallback (如有必要)
        if "323" in filename:
            return "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991"
        return None

    def process_csv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """處理上傳的 CSV 內容"""
        account_hash = self._get_account_hash_from_filename(filename)
        if not account_hash:
            return {"success": False, "error": f"無法識別帳戶: {filename}。請確保檔名包含帳號末三碼。"}

        content_str = file_content.decode('utf-8-sig')
        # 簡單判斷是 Transactions 還是 Balances (Positions)
        if "Transactions" in filename or "Action" in content_str:
            return self._import_transactions(content_str, account_hash)
        elif "Balances" in filename or "Market Value" in content_str or "Amount" in content_str:
            return self._import_balances(content_str, account_hash)
        else:
            return {"success": False, "error": "無法判斷 CSV 類型 (Transactions 或 Balances)"}

    def _import_transactions(self, csv_content: str, account_hash: str) -> Dict[str, Any]:
        db = SessionLocal()
        stats = {"dividends": 0, "trades": 0, "skipped": 0, "errors": 0}
        
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            for row in reader:
                action = row.get('Action', '').strip()
                if not action: continue
                
                action_lower = action.lower()
                symbol = row.get('Symbol', 'CASH').strip()
                date_obj = self._parse_date(row.get('Date'))
                amount = self._parse_amount(row.get('Amount'))
                description = row.get('Description', '').strip()
                
                if not date_obj:
                    continue

                # 1. 股息處理
                if any(kw in action_lower for kw in self.div_keywords) and amount > 0:
                    # 去重檢查 (CSV 通常沒有 activityId，使用組合鍵)
                    existing = db.query(Dividend).filter(
                        Dividend.account_hash == account_hash,
                        Dividend.date == date_obj,
                        Dividend.symbol == symbol,
                        Dividend.amount == amount
                    ).first()
                    
                    if not existing:
                        db.add(Dividend(
                            account_hash=account_hash,
                            date=date_obj,
                            symbol=symbol,
                            amount=amount,
                            description=f"{action}: {description}"
                        ))
                        stats["dividends"] += 1
                    else:
                        stats["skipped"] += 1
                
                # 2. 交易處理 (買賣、入金出金、DRIP)
                else:
                    side = None
                    if action_lower == 'buy': side = 'BUY'
                    elif action_lower == 'sell': side = 'SELL'
                    elif action_lower == 'reinvest shares': side = 'BUY'
                    elif any(kw in action_lower for kw in ['deposit', 'credit interest', 'funds received', 'ach receipt']): 
                        side = 'DEPOSIT'
                    elif any(kw in action_lower for kw in ['withdrawal', 'cash disbursement', 'atm']): 
                        side = 'WITHDRAWAL'
                    
                    if side:
                        qty = abs(self._parse_amount(row.get('Quantity', '0')))
                        price = abs(self._parse_amount(row.get('Price', '0')))
                        
                        # 唯一性檢查
                        existing = db.query(TradeHistory).filter(
                            TradeHistory.account_hash == account_hash,
                            TradeHistory.date == date_obj,
                            TradeHistory.symbol == symbol,
                            TradeHistory.side == side,
                            TradeHistory.quantity == (qty if side not in ['DEPOSIT', 'WITHDRAWAL'] else amount),
                            TradeHistory.price == (price if price > 0 else 1.0)
                        ).first()
                        
                        if not existing:
                            db.add(TradeHistory(
                                account_hash=account_hash,
                                date=date_obj,
                                symbol=symbol,
                                side=side,
                                quantity=qty if side not in ['DEPOSIT', 'WITHDRAWAL'] else amount,
                                price=price if price > 0 else 1.0,
                                realized_pnl=0.0,
                                description=f"{action}: {description}"
                            ))
                            stats["trades"] += 1
                        else:
                            stats["skipped"] += 1

            db.commit()
            return {"success": True, "stats": stats}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def _import_balances(self, csv_content: str, account_hash: str) -> Dict[str, Any]:
        """
        處理資產歷史匯入 (Balances CSV)
        將資料寫入 HistoricalBalance 表，並以 account_hash 進行關聯
        """
        db = SessionLocal()
        count = 0
        skipped = 0
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            for row in reader:
                # 嘉信 Balances CSV 通常有 'Date' 和 'Market Value' 或 'Amount' 欄位
                date_val = row.get('Date')
                # 支援多種金額欄位名稱
                total_val = self._parse_amount(row.get('Market Value') or row.get('Amount'))
                
                date_obj = self._parse_date(date_val)
                if not date_obj or total_val <= 0:
                    continue

                # 檢查是否已存在該帳戶在該日期的紀錄 (避免重複匯入)
                existing = db.query(HistoricalBalance).filter(
                    HistoricalBalance.date == date_obj,
                    HistoricalBalance.account_id == account_hash
                ).first()

                if existing:
                    # 如果已存在且數值不同，則更新
                    if existing.balance != total_val:
                        existing.balance = total_val
                        count += 1
                    else:
                        skipped += 1
                else:
                    # 建立新紀錄
                    db.add(HistoricalBalance(
                        date=date_obj,
                        account_id=account_hash,
                        balance=total_val
                    ))
                    count += 1

            # 確保所有變更都提交
            db.commit()
            print(f"🚀 [IMPORTER] Balances imported: {count} updated/added, {skipped} skipped.")
            return {"success": True, "stats": {"history_records": count, "skipped": skipped}}
        except Exception as e:
            print(f"❌ [IMPORTER] Error importing balances: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

importer_service = ImporterService()
