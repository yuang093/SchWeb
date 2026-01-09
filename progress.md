# 開發日誌 (DevLog)

## 2025-12-30

### 初始化開發
- **技術決策**：
    - 使用 `backend` 與 `frontend` 分離的目錄結構。
    - 後端採用 FastAPI 框架，因其非同步特性與 Pydantic 驗證，適合處理 API 串接與數據計算。
    - 前端採用 Vite + React + TypeScript + Tailwind CSS，確保開發速度與類型安全。
- **進度**：
    - [x] 1. 專案環境初始化 (2025-12-30)
    - [x] 2. 後端 FastAPI 骨架 (2025-12-30)
    - [x] 3. Schwab OAuth 2.0 實作 (2025-12-30)
        - 完成環境變數與 Pydantic 模型。
        - 實作 Base64 工具與測試。
        - 完成授權網址產生與 Callback 接收邏輯。
        - 實作 TokenStorage 與自動刷新機制。
    - [x] 4. Demo 模式與 Mock Data 基礎 (2025-12-30)
        - 實作 `Settings.DEMO_MODE` 開關。
        - 建立 `account.json` 模擬資產持倉。
        - 實作 `AccountRepository` 支持數據切換。
    - [x] 5. 前端基礎建設 (UI Setup) (2025-12-30)
        - 安裝並設定 Tailwind CSS 與深色模式。
        - 實作響應式 Sidebar。
        - 建立 MainLayout 容器。
        - 整合 Lucide-React 圖標庫。

## 階段二：數據整合與 Dashboard 核心

### 2025-12-30
- **技術決策**：
    - 使用 `recharts` 作為圖表庫，因其與 React 整合性高且支援響應式容器。
    - 使用 `zustand` 進行輕量化全域狀態管理 (Demo Mode 切換)。
    - 後端擴充 `AccountRepository` 與 API 路由以支持歷史數據。
- **進度**：
    - [x] 後端：實作 `GET /summary` 與 `GET /history` API。
    - [x] 前端：安裝 Recharts 並實作 `NetWorthChart` 面積圖。
    - [x] 前端：使用 Zustand 實作 `isDemoMode` 全域開關。
    - [x] UI：在 Sidebar 整合模式切換開關 (Toggle Switch)。
