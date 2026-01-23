import time
import threading
import logging
from datetime import datetime
from app.services.schwab_client import schwab_client
from app.db.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self.is_running = False

    def update_holdings(self):
        """
        核心排程任務：更新所有連結帳戶的持倉、餘額與交易紀錄
        這會觸發全自動快照與交易同步
        """
        logger.info(f"⏰ [SCHEDULER] 開始執行定時更新任務: {datetime.now()}")
        try:
            # 1. 獲取所有帳戶
            accounts = schwab_client.get_linked_accounts()
            if not accounts:
                logger.warning("⚠️ [SCHEDULER] 未找到任何帳戶，跳過更新。")
                return

            for acc in accounts:
                acc_hash = acc.get("hash_value")
                if not acc_hash:
                    continue

                logger.info(f"📸 [SCHEDULER] 正在為帳戶 ...{acc_hash[-4:]} 執行快照與同步")
                
                # 呼叫 get_real_account_data 會觸發:
                # - _sync_real_data_to_db (餘額與持倉快照)
                # - fetch_transactions (交易紀錄自動同步)
                schwab_client.get_real_account_data(acc_hash)

            logger.info("✅ [SCHEDULER] 所有帳戶更新完成。")
        except Exception as e:
            logger.error(f"❌ [SCHEDULER] 排程更新失敗: {e}")

    def _run_loop(self):
        """
        背景執行迴圈
        """
        # 初始執行一次
        self.update_holdings()
        
        # 之後每 6 小時執行一次
        # (嘉信 API 限制頻繁請求，且餘額通常一天更新一次，6小時是安全且合理的範圍)
        interval = 6 * 3600 
        
        while not self._stop_event.is_set():
            # 睡眠期間每分鐘檢查一次 stop_event，以便快速停止
            for _ in range(interval // 60):
                if self._stop_event.is_set():
                    break
                time.sleep(60)
            
            if not self._stop_event.is_set():
                self.update_holdings()

    def start(self):
        if self._thread is None:
            self.is_running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("🚀 [SCHEDULER] 背景排程器已啟動。")

    def stop(self):
        if self._thread:
            self.is_running = False
            self._stop_event.set()
            logger.info("🛑 [SCHEDULER] 正在停止排程器...")
            # 不等待 join 以免阻塞主進程退出
            self._thread = None

# 全域單例
task_scheduler = TaskScheduler()
