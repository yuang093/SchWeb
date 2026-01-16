# Changelog

## [2026-01-15] - 重大修復：Dashboard 指標重構與數據精確化

### Fixed
- **累積股息 (Total Dividends) 顯示異常**: 修正 `repository.py` 邏輯，將股息統計範圍由「年度 (YTD)」改為「全期累計」。
- **數據重複問題**: 識別並清除 Schwab API 與 CSV 歷史匯入導致的 133 筆重複股息紀錄。
- **DRIP 識別**: 實作股息再投入 (DRIP) 識別邏輯，確保 `Qual Div Reinvest` 等交易正確計入收益。

### Added
- **數據匯入工具**: 新增 `import_transactions_csv.py`，支援從嘉信 CSV 批次補入歷史交易與股息。
- **數據稽核工具**: 新增 `audit_dividend_breakdown.py` 與 `cleanup_dividends_v2.py` 用於數據診斷與去重。

### Changed
- **Dashboard KPI 重構**: 將「已實現損益 (Realized P&L)」更換為「總報酬 (Total Return)」，改用基於淨投入本金的績效計算法。
- **本金校正**: 引入 `MANUAL_ADJUSTMENTS` 處理 TD Ameritrade 移轉前的歷史本金 ($47,400.37)，大幅提升總報酬率的準確度。

## [2026-01-16] - 風險分析指標優化與數據源遷移

### Changed
- **Market Data Source 遷移**: 績效基準 (SPY) 數據源從 `yfinance` 遷移至 **Schwab Market Data API**，解決 Windows 下的 SSL 證書驗證問題並提高穩定性。
- **Beta 計算邏輯**: 固定使用「過去 1 年」窗口進行迴歸分析，並實作基於持倉標的的「權重 Beta」作為異常值 Fallback 機制。
- **夏普比率 (Sharpe Ratio)**: 引入配置化的 `RISK_FREE_RATE` (4%)，並優化年化回報計算，避免短期數據導致的數值極端化。

### Fixed
- **波動率 (Volatility) 異常**: 透過 Business Day Resampling (排除週末/假期) 與單日異常變動過濾 (abs > 20%)，修復了波動率飆升問題（從 148% 回復至約 10% 的正常水平）。
- **Benchmark 顯示**: 修復了基準回報率可能顯示為 -99.99% 的極端值問題。

### Added
- **Schwab Client 擴充**: 在 `schwab_client.py` 中實作 `get_price_history` 方法，支援獲取個股與指數的歷史價格數據。

## [2026-01-16] - CSV 匯入功能與系統設定優化

### Added
- **CSV 資料匯入**: 系統設定頁面新增「CSV 資料匯入」功能，支援拖拽上傳嘉信 Transactions 與 Balances 檔案，具備自動去重、DRIP 識別與資產歷史同步功能。
- **認證狀態檢查**: 後端新增 `/auth/status` API，前端 Settings 頁面可即時顯示嘉信 API 連線狀態。
- **一鍵授權按鈕**: Settings 頁面新增「連接嘉信 / 重新授權」按鈕，簡化 OAuth 授權流程。

### Fixed
- **前端錯誤處理**: 修復後端伺服器異常時 Settings 頁面欄位消失的問題，加入連線錯誤警告與欄位保護狀態。

## [2026-01-16] - 風險指標第二階段：精確化報酬率與風險值

### Changed
- **年化報酬率 (Annual Return) 重構**: 廢除不穩定的日回報累推法，改用 **「總報酬年化法 (Total Return Annualization)」**。直接引用經過本金校正後的總報酬率並結合持有天數進行反推，解決了轉帳造成的數值偏差（由 300% 修正為實測的 4%-8%）。
- **最大回撤 (Max Drawdown) 修復**: 計算邏輯從基於「帳戶餘額」改為基於「調整後的幾何累計收益率」，完全排除了大額轉帳對回撤指標的誤導。
- **風險值 (VaR) 優化**: 改用 **「參數法 (Parametric VaR)」** 取代歷史模擬法，以 95% 信心水準結合實際年化波動率，提供更具參考價值的單日預期最大虧損估算。

### Fixed
- **資金流干擾**: 實作異常值過濾機制 (Outlier Filter)，自動識別並歸零因帳戶轉帳導致的極端日回報脈衝（絕對值 > 10%）。
