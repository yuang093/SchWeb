# 專案進度追蹤 (Todo Progress)

## Phase 1: 基礎架構建立 (Done)
... (省略部分完成項目) ...

## Phase 4: 進階功能與優化 (In Progress)
### 4.1 持倉顯示優化 (Done)
- [x] 後端：優化持倉數據映射 (cost_basis, total_pnl 等)
- [x] 前端：`HoldingsTable` 精度調整 (股數 3 位)

### 4.2 持倉排序功能與專業化 UI (Done)
- [x] 前端：實作 `HoldingsTable` 點擊排序機制 (SortConfig)
- [x] 前端：專業化看盤表 UI (排序圖示、字體與對齊調整)

### 4.3 數據計算修復與欄位擴充 (Done)
- [x] 後端：實作強制的盈虧與百分比計算邏輯，解決 0.00% 問題
- [x] 前端：嚴格對齊 9+1 欄位順序，強化正負數顏色標示

### 4.4 持倉分類顯示 (Current)
- [ ] 後端：`schwab_client.py` 增加 `asset_type` 欄位，用於區分持倉類型
- [ ] 前端：`Dashboard.tsx` 拆分 `HoldingsTable` 為 Stock/Option 兩部分
- [ ] 前端：`HoldingsTable.tsx` 新增 `title` Prop 顯示表格標題
- [ ] 驗證分表功能與 UI 呈現結果

## Phase 5: 進階功能 (Planned)
... (省略後續項目) ...
