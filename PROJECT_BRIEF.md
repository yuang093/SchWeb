Project: Schwab AI Investment Dashboard (SAID)
1. 專案概述 (Overview)
開發一個基於 Web 的投資組合管理儀表板，串接 Charles Schwab Trader API。該系統旨在提供超越券商原生介面的數據分析，包含即時資產監控、風險指標分析 (VAR, Beta)、GICS 產業分佈以及 AI 投資輔助建議。系統需具備 Demo 模式以便在無 API 連線時展示功能。

2. 技術架構 (Tech Stack)
Frontend: React (Vite/Next.js), TypeScript, Tailwind CSS, Recharts (圖表).

Backend: Python (FastAPI), Pandas (數據分析), NumPy (金融計算).

Database: SQLite/PostgreSQL (儲存歷史快照、交易記錄).

External API: Schwab Trader API (OAuth 2.0).

Docs: Markdown (overview.md, todo_progress.md).

3. 功能需求清單 (Feature Requirements)
3.1 核心系統與基礎設施 (Infrastructure)

身份驗證 (Auth): 實作 Schwab OAuth 流程登入，包含 Token 管理與自動刷新 (Refresh Token) 。


數據整合 (Data Integration): 聚合帳戶餘額、持倉、訂單狀態 。


Demo 模式: 提供一個切換開關，開啟時使用預設的 Mock Data (假資料) 呈現所有圖表與卡片，方便展示與 UI 測試 。


緩存機制 (Caching): 針對非即時變動數據 (如基本面資料) 建立快取，避免觸發 API Rate Limit 。

3.2 總覽儀表板 (Dashboard)
作為登入後的首頁，提供高視角的資產快照：

關鍵指標卡片 (KPI Cards):

總資產 (Total Net Liquidation) 。

當日盈虧 (Day P/L) & 盈虧百分比 。

年度至今盈虧 (YTD P/L) & 百分比 。

現金水位 (Cash Balance) 與 購買力 (Buying Power) 。

核心圖表:


淨值走勢圖 (Net Worth History): 可切換時間維度 (YTD, 1Y, 3Y, All) 。


現金水位變化圖: 監控現金在資產中的佔比趨勢 。

3.3 投資組合管理 (Portfolio Management)

持股列表 (Holdings Table): 

欄位: 代碼、名稱、數量、平均成本、現價、市值、資金佔比 (Weight)、未實現損益 (Unrealized P/L)、總報酬率 (%)。


功能: 支援點擊欄位排序 (Sorting)、關鍵字搜尋篩選 。


分類標籤: 支援自定義標籤 (如: 股息股、成長股、ETF) 與 GICS 自動分類 。

資產分佈分析 (Allocation):


圓餅圖 1 (Asset Class): 股票 vs 現金 vs 選擇權 vs 債券 。


圓餅圖 2 (Sector): 依照 GICS (Global Industry Classification Standard) 顯示產業分佈 (如 Technology, Healthcare) 。


細分產業圖 (Industry Group): 顯示更細項的產業曝險 (如 Semiconductor, Software) 。

3.4 風險分析 (Risk Analysis)
此模組需運用 Python numpy/scipy 進行計算：


波動性指標: 計算投資組合的年化波動率 (Annualized Volatility) 。


風險值 (VaR): 計算 Value at Risk (95% 或 99% 信賴區間)，預估極端情況下的最大虧損 。


Beta 係數: 計算投資組合相對於大盤 (SPY) 的 Beta 值，衡量系統性風險 。


多空分析: 顯示 多頭 (Long) vs 空頭 (Short) 的資金比例 。


集中度分析: 計算前 5 大持股佔總資產的比例 (Top 5 Concentration)，若過高需顯示警示 。


槓桿監控: 顯示當前槓桿比率 (Leverage Ratio) 。

3.5 績效與收益 (Performance & Income)

績效分析: 比較投資組合 vs 基準指數 (S&P 500, Nasdaq) 的績效走勢 。


收益記錄: 記錄股息 (Dividend) 與已實現損益 (Realized P/L)，並繪製每月收入柱狀圖 。

3.6 AI 輔助投資 (AI Copilot)
整合 LLM (如 OpenAI/Gemini API)：

根據持倉結構提供簡單的再平衡建議。

針對特定股票進行新聞摘要或基本面解讀 。

4. 文件與專案管理 (Documentation)

overview.md: 系統架構圖、API 串接說明、修改歷程 (Changelog) 。


todo_progress.md: 拆解後的任務清單，包含 [ ] Todo, [x] Done, [-] In Progress 狀態 。

5. UI/UX 設計準則
風格: 現代化深色模式 (Dark Mode)，類似彭博終端機或 IB TWS 的專業感。

響應式: 支援 Desktop 為主，但需適配 Tablet。


卡片式設計: 所有功能模組以 Card 形式呈現，版面乾淨 。

## 6. 開發準則 (Development Guidelines)
* **Atomic Tasks Only:** 請嚴格遵守「原子化任務」原則。
* **Small Scope:** 每個 Step 的任務範圍必須限制在 **15 分鐘內** 可完成的工作量。
* **No Monoliths:** 禁止一次性生成過長的程式碼。如果是複雜功能（如 Dashboard UI），請拆解為：1. 建立空組件, 2. 定義 Type, 3. 實作 API 呼叫, 4. 綁定資料, 5. 美化樣式。
* **TDD First:** 涉及邏輯計算時，優先撰寫測試案例。