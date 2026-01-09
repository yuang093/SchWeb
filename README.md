# Schwab AI Investment Dashboard (SAID)

一個現代化的 Web 投資組合管理儀表板，基於 Charles Schwab Trader API 設計。

## 🌟 核心功能
*   **總覽儀表板**：即時監控總資產、當日盈虧、現金水位及 30 天淨值走勢。
*   **投資組合管理**：自動計算產業分佈比例，詳細列出持倉明細與市值變化。
*   **風險分析模組**：利用金融演算法計算年化波動率、夏普比率及最大回撤。
*   **AI Copilot**：數據感知的智慧助理，支援自然語言詢問帳戶現況。
*   **Demo 模式**：支援一鍵切換模擬數據，方便無 API 連線時展示。

## 🛠️ 技術棧
*   **前端**：React (Vite), TypeScript, Tailwind CSS, Recharts, Zustand, React Query.
*   **後端**：Python (FastAPI), Pandas, NumPy.

## 🚀 快速啟動 (Windows)

1.  **環境準備**：
    *   確保已安裝 Node.js (v18+) 與 Python (3.9+)。
    *   在根目錄建立並啟動 Python 虛擬環境：`python -m venv venv` 接著 `./venv/Scripts/activate`。
    *   安裝後端依賴：`pip install -r backend/requirements.txt`。
    *   安裝前端依賴：`cd frontend; npm install`。

2.  **一鍵啟動**：
    *   在根目錄找到 `start_app.ps1`。
    *   右鍵點擊選擇「使用 PowerShell 執行」。

## 📁 專案結構
*   `backend/`：FastAPI 服務、金融計算邏輯與 Mock Data。
*   `frontend/`：React 前端原始碼與 UI 組件。
*   `todo_progress.md`：詳細的開發進度追蹤表。

## 📝 備註
目前專案運行於 **Demo 模式**，數據來源為 `backend/mock_data/account.json`。如需對接真實 API，請至 `backend/app/core/config.py` 修改設定。
