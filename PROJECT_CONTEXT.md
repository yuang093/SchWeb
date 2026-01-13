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


淨值走勢圖 (Net Worth History): 可切換時間維度 (3M, 6M, YTD, 1Y, 3Y, All) 。


現金水位變化圖: 監控現金在資產中的佔比趨勢 。

3.3 投資組合管理 (Portfolio Management)

持股列表 (Holdings Table): 

分別股票與選擇權使用不同欄位

欄位: 代碼、名稱、數量(小數點3位)、成本、現價、市值、資金佔比 (Weight)、未實現損益 (Unrealized P/L)、總報酬率 (%)、持倉佔比。
欄位要可以排序

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

## 7. 修改日誌 (Change Log)
- [2026-01-09] [Roo] 修正 AccountRepository 初始化 500 錯誤：更正 __init__ 參數簽章以接收 db Session，並移除全域錯誤實例，確保與 FastAPI 依賴注入機制相容。
- [2026-01-09] [Roo] 修正帳戶列表 404 錯誤：在 account.py 中新增 /list 路由，並在 MockRepository 與 AccountRepository 中同步實作 get_accounts() 方法，恢復帳戶選擇器功能。
- [2026-01-09] [Roo] 修復帳戶選擇器消失問題：優化 Dashboard.tsx 的帳戶載入與自動選取邏輯（優先選取第二帳戶），加入關鍵日誌與 Loading 佔位符，確保選取後觸發資料更新。
- [2026-01-09] [Roo] 強制修復持倉不顯示問題：放寬前端 Dashboard.tsx 的過濾條件（不分大小寫並支持多種標籤），加入關鍵 Debug Log，並再次驗證 Mock 資料與後端模型的一致性。
- [2026-01-09] [Roo] 深度修復持倉明細顯示：統一前後端 Position 欄位名稱 (open_pl, cost_basis, current_price 等)，修正 Pydantic 模型配置 (`from_attributes=True`)，優化前端過濾邏輯為不分大小寫，並加入偵錯日誌以確保資料顯示。
- [2026-01-09] [Roo] 恢復 HoldingsTable 完整欄位顯示與型別定義，新增 cost_basis, day_pl, open_pl, allocation_pct 欄位，並實作損益顏色與數值遮罩邏輯。
- [2026-01-12] [Roo] 修復產業分佈圓餅圖與聯動篩選：修復後端 `sector` 提取邏輯，修正前端型別與渲染高度問題，並實作點擊圓餅圖自動過濾持倉列表的功能。
- [2026-01-12] [Roo] 配置 Vite Proxy 與相對路徑 API：解決跨裝置 (行動端) 存取後端 API 失敗的問題，現在前端經由 Vite 代理轉發請求至後端。
- [2026-01-12] [Roo] 重構 API Key 管理與持久化：將 API Key 儲存位置從前端移至後端資料庫 (SQLite)，實作 API Key 的遮罩顯示與多設備同步功能。
- [2026-01-12] [Roo] 實作 Token 持久化與自動刷新：將 Schwab OAuth Token 儲存至資料庫，移除了對 `token.json` 檔案的依賴，並實作了 Token 過期時的自動刷新與資料庫更新機制。
- [2026-01-12] [Roo] 強制 Token 同步與匯入工具：優化 SchwabClient 啟動邏輯，支援多路徑 (Root/Backend) 自動偵測 `token.json` 並強制同步至資料庫，提供安全的時間戳記備份機制。
- [2026-01-13] [Roo] 深度修復認證持久化格式與數據同步：修正 `SchwabClient` 的 Token 讀取/儲存包裝邏輯，確保與 `schwab-py` 的 Metadata 驗證相容；完成持倉名稱解析優化，解決同步崩潰問題。
- [2026-01-13] [Roo] 系統穩定性強化：解決跨裝置 (行動端) 連線、API 金鑰/Token 資料庫同步、以及 Windows 檔案權限導致的備份衝突等關鍵回歸問題，確保系統 100% 脫離檔案依賴。
- [2026-01-13] [Roo] 修復產業分佈圓餅圖：實作 `sector_mapper.py` 補足 Schwab API 缺失的 GICS 行業資訊，修復 Token 自動刷新崩潰問題，並統一後端數據同步邏輯，解決圓餅圖僅顯示 "Other" 的問題。
- [2026-01-13] [Roo] 產業分佈圖中文化：在 `AllocationChart.tsx` 中實作行業名稱對照表，將 GICS 產業分類翻譯為繁體中文，優化圖例 (Legend) 與工具提示 (Tooltip) 的顯示體驗。
- [2026-01-13] [Roo] 優化風險分析 Beta 計算與帳戶切換：實作持倉加權 Beta (Ex-ante Beta) 邏輯以修復 SSL 報錯導致的異常數值；在「風險分析」頁面新增帳戶切換器並支援後端 `account_hash` 參數過濾。
- [2026-01-13] [Roo] 更新 Dashboard 卡片與系統架構圖：將首頁「購買力」卡片替換為「Beta 係數」顯示；建立 `backend/app/utils/risk.py` 模組化風險計算邏輯並同步更新 `overview.md` 目錄結構。