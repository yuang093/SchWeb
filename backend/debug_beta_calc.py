import sys
import os
import pandas as pd

# 加入 backend 目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.schwab_client import schwab_client

def debug_portfolio_beta_fixed():
    print("🔍 開始偵錯 Portfolio Beta 計算 (基於持倉加權)...")
    
    try:
        # 1. 獲取帳戶列表
        accounts = schwab_client.get_linked_accounts()
        if not accounts:
            print("❌ 找不到任何連結的帳戶")
            return
        
        # 我們分析所有帳戶
        for acc in accounts:
            account_hash = acc['hash_value']
            print(f"\n--- 帳戶: {acc['account_name']} ({acc['account_number']}) ---")
            
            # 2. 獲取即時持倉數據
            data = schwab_client.get_real_account_data(account_hash)
            if "error" in data:
                print(f"❌ 獲取數據失敗: {data['error']}")
                continue
                
            account_info = data['accounts'][0]
            holdings = account_info['holdings']
            total_value = account_info['total_balance']
            
            print(f"總資產價值: ${total_value:,.2f}")
            print(f"{'Symbol':<10} | {'Market Value':<15} | {'Weight %':<10} | {'Beta (Est.)':<10} | {'Weighted Beta'}")
            print("-" * 80)
            
            portfolio_beta = 0
            valid_weight_total = 0
            
            # 預設一些常用標的的 Beta (如果 API 真的拿不到，先用這個做 Demo 偵錯)
            default_betas = {
                "VOO": 1.0, "SPY": 1.0, "NVDA": 1.67, "TSLA": 2.3, "AAPL": 1.1, 
                "META": 1.2, "GOOG": 1.05, "MSFT": 0.9, "TSM": 1.2, "IBIT": 2.5,
                "SGOV": 0.0, "BRK.B": 0.9
            }
            
            for h in holdings:
                symbol = h['symbol']
                mkt_val = h['market_value']
                weight = (mkt_val / total_value)
                
                # 這裡目前我們先顯示權重，Beta 設為 N/A 或 嘗試從預設表拿
                beta = default_betas.get(symbol, 1.0) # 預設給 1.0 以便觀察計算
                
                # 如果是現金或 SGOV 類，Beta 應該接近 0
                if "SGOV" in symbol or "Cash" in symbol:
                    beta = 0.0
                
                weighted_beta = weight * float(beta)
                portfolio_beta += weighted_beta
                valid_weight_total += weight
                
                print(f"{symbol:<10} | ${mkt_val:>14,.2f} | {weight*100:>8.2f}% | {float(beta):>10.2f} | {weighted_beta:>12.4f}")
            
            print("-" * 80)
            print(f"計算得出的預估總組合 Beta: {portfolio_beta:.4f}")
            print(f"有效權重總計: {valid_weight_total*100:.2f}%")

    except Exception as e:
        print(f"❌ 偵錯過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_portfolio_beta_fixed()
