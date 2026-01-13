# SAID 系統架構與設計說明 (Overview)

## 1. 系統架構圖
```mermaid
graph TD
    User([使用者]) <--> Frontend[React Frontend - Vite]
    Frontend <--> API[FastAPI Backend]
    API <--> SchwabAPI[Schwab Trader API]
    API <--> LLM[AI Service - OpenAI/Gemini]
    API <--> DB[(SQLite/PostgreSQL)]
    API <--> Cache[Local Cache - Pandas/Memory]
```

## 2. 資料夾結構推薦
為了保持專案清晰，建議採用以下結構：

```text
嘉信股票儀表板/
├── backend/                # Python FastAPI 後端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── account.py
│   │   │   ├── analytics.py
│   │   │   ├── auth.py
│   │   │   ├── copilot.py
│   │   │   ├── risk.py     # 風險分析 API 端點
│   │   │   └── settings.py
│   │   ├── core/           # 核心配置 (config.py)
│   │   ├── db/             # 資料庫封裝 (database.py)
│   │   ├── models/         # SQLAlchemy 模型 (persistence.py)
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 業務邏輯服務
│   │   │   ├── repository.py
│   │   │   ├── schwab_auth.py
│   │   │   └── schwab_client.py
│   │   ├── utils/          # 工具函數
│   │   │   ├── auth_utils.py
│   │   │   ├── sector_mapper.py
│   │   │   └── risk.py     # 金融風險指標計算邏輯 (Beta, VaR, Volatility)
│   │   └── main.py         # 應用程式進入點
│   ├── data/               # 靜態數據或歷史 CSV
│   ├── scripts/            # 工具腳本 (如初始化 DB, 手動授權)
│   ├── tests/              # 測試案例
│   └── requirements.txt    # 後端套件清單
├── frontend/               # React 前端 (Vite)
│   ├── src/
│   │   ├── api/            # API 客戶端定義
│   │   ├── components/     # UI 組件 (dashboard/, layout/)
│   │   ├── context/        # 全域上下文 (PrivacyContext.tsx)
│   │   ├── pages/          # 頁面級組件 (Dashboard, RiskAnalysis)
│   │   └── store/          # 狀態管理 (useAppStore.ts)
│   ├── tailwind.config.js
│   └── vite.config.ts
├── screenshots/            # 系統運作截圖
├── PROJECT_CONTEXT.md      # 專案背景與修改日誌
├── overview.md             # 系統架構與設計 (本檔案)
└── todo_progress.md        # 任務進度清單
```

## 3. 核心模組說明
- **Auth Module**: 處理 OAuth 2.0 授權碼流程，儲存加密後的 Access/Refresh Tokens。
- **Risk Engine**: 利用 `backend/app/utils/risk.py` 進行組合波動率與 VaR 計算。
- **AI Copilot**: 整合 LLM，將持倉數據 (格式化後) 傳送給 AI 進行分析。
- **Mock Service**: 在後端實作一組模擬數據生產器，當 `DEMO_MODE=true` 時不調用真實 API。
