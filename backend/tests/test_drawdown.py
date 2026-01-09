from app.services.schwab_client import schwab_client
import json

def test_drawdown_logic():
    print("--- 測試 Drawdown 邏輯 ---")
    try:
        # 測試 get_real_account_data
        # 由於需要真實 Token，這裡我們主要檢查語法是否正確
        # 如果環境中有 token.json，這將會執行真實 API 呼叫
        data = schwab_client.get_real_account_data()
        
        if "error" in data:
            print(f"❌ 獲取數據失敗 (可能是 Token 過期或不存在): {data['error']}")
            return

        for acc in data.get("accounts", []):
            print(f"帳戶: {acc.get('account_id')}")
            for holding in acc.get("holdings", []):
                symbol = holding.get("symbol")
                drawdown = holding.get("drawdown_pct")
                asset_type = holding.get("asset_type")
                
                if asset_type == "EQUITY":
                    print(f"股票: {symbol}, Drawdown: {drawdown if drawdown is not None else '-'}")
                else:
                    print(f"其他: {symbol} ({asset_type})")
                    
    except Exception as e:
        print(f"❌ 測試過程發生異常: {str(e)}")

if __name__ == "__main__":
    test_drawdown_logic()
