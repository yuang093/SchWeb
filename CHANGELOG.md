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
