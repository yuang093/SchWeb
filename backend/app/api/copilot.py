from fastapi import APIRouter
from pydantic import BaseModel
from app.services.repository import account_repo

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_copilot(request: ChatRequest):
    """
    Rule-Based AI Copilot 模擬引擎
    """
    user_msg = request.message.lower()
    data = account_repo.get_account_data()
    
    if "error" in data:
        return {"reply": "抱歉，我現在無法讀取您的帳戶數據。"}
    
    acc = data["accounts"][0]
    holdings = acc.get("holdings", [])
    
    # 邏輯判斷
    if any(keyword in user_msg for keyword in ["資產", "多少錢", "餘額"]):
        total = acc.get("total_balance", 0)
        return {"reply": f"您當前的總資產價值為 ${total:,.2f}。"}
    
    if any(keyword in user_msg for keyword in ["最大", "持倉", "最多"]):
        if not holdings:
            return {"reply": "您的投資組合目前沒有持倉數據。"}
        top_holding = max(holdings, key=lambda x: x.get("market_value", 0))
        symbol = top_holding.get("symbol")
        value = top_holding.get("market_value", 0)
        return {"reply": f"您目前最大的持倉是 {symbol}，市值約為 ${value:,.2f}。"}
    
    if any(keyword in user_msg for keyword in ["風險", "夏普", "波動"]):
        return {"reply": "根據初步分析，您的投資組合表現穩健。建議前往『風險分析』頁面查看詳細的夏普比率與波動率指標。"}

    # 預設通用回覆
    return {
        "reply": "這是一個很好的問題！從您的資產分佈來看，目前的配置相對集中在資訊技術產業。如果您想了解更多細節，可以問我關於最大持倉或總資產的問題。"
    }
