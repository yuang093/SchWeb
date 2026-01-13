import sys
import os
import pandas as pd
import yfinance as yf

# 加入 backend 目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.schwab_client import schwab_client

def debug_portfolio_beta_with_yf():
    print("🔍 開始偵錯 Portfolio Beta 計算 (使用 yfinance 獲取個股 Beta)...")
    
    try:
        accounts = schwab_client.get_linked_accounts()
        if not accounts:
            print("❌ 找不到任何連結的帳戶")
            return
        
        for acc in accounts:
            account_hash = acc['hash_value']
            print(f"\n--- 帳戶: {acc['account_name']} ({acc['account_number']}) ---")
            
            data = schwab_client.get_real_account_data(account_hash)
            if "error" in data:
                print(f"❌ 獲取數據失敗: {data['error']}")
                continue
                
            account_info = data['accounts'][0]
            holdings = account_info['holdings']
            total_value = account_info['total_balance']
            
            print(f"總資產價值: ${total_value:,.2f}")
            print(f"{'Symbol':<10} | {'Market Value':<15} | {'Weight %':<10} | {'Beta (YF)':<10} | {'Weighted Beta'}")
            print("-" * 80)
            
            portfolio_beta = 0
            valid_weight_total = 0
            
            symbols = [h['symbol'] for h in holdings if h['asset_type'] in ['EQUITY', 'COLLECTIVE_INVESTMENT']]
            
            # 批量獲取 yfinance info (這可能會比較慢)
            # 為了偵錯，我們只取權重較大的前幾名，或者全部
            for h in holdings:
                symbol = h['symbol']
                if h['asset_type'] not in ['EQUITY', 'COLLECTIVE_INVESTMENT']:
                    continue
                
                mkt_val = h['market_value']
                weight = (mkt_val / total_value)
                
                # 處理 Schwab 符號格式 (例如 BRK.B -> BRK-B)
                yf_symbol = symbol.replace('.', '-')
                
                beta = 0
                try:
                    ticker = yf.Ticker(yf_symbol)
                    beta = ticker.info.get('beta', 0)
                except:
                    beta = 0
                
                if beta is None: beta = 0
                
                weighted_beta = weight * float(beta)
                portfolio_beta += weighted_beta
                valid_weight_total += weight
                
                print(f"{symbol:<10} | ${mkt_val:>14,.2f} | {weight*100:>8.2f}% | {float(beta):>10.2f} | {weighted_beta:>12.4f}")
            
            print("-" * 80)
            print(f"計算得出的總組合 Beta: {portfolio_beta:.4f}")
            print(f"有效權重總計: {valid_weight_total*100:.2f}%")

    except Exception as e:
        print(f"❌ 偵錯過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_portfolio_beta_with_yf()
