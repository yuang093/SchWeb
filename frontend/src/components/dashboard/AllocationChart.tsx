import { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { ArrowLeft } from 'lucide-react';
import type { Position as Holding } from '../../api/account';

interface AllocationChartProps {
  data: Holding[];
  loading?: boolean;
  selectedSector?: string | null;
  onSectorClick?: (sector: string | null) => void;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1'];

const SECTOR_TRANSLATIONS: Record<string, string> = {
  "Energy": "能源",
  "Materials": "原物料",
  "Industrials": "工業",
  "Consumer Discretionary": "非必需消費",
  "Consumer Staples": "必需消費",
  "Health Care": "醫療保健",
  "Financials": "金融",
  "Information Technology": "資訊科技",
  "Communication Services": "通訊服務",
  "Utilities": "公用事業",
  "Real Estate": "房地產",
  "ETFs": "ETF",
  "Other": "其他",
  "Options": "選擇權",
  "Cash": "現金"
};

const translateSector = (sector: string) => SECTOR_TRANSLATIONS[sector] || sector;

export default function AllocationChart({
  data,
  loading = false,
  selectedSector = null,
  onSectorClick
}: AllocationChartProps) {

  if (loading || !data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="w-full h-full min-h-[300px] bg-slate-900 border border-slate-800 rounded-xl animate-pulse flex items-center justify-center">
        <p className="text-slate-600 text-sm">
          {loading ? "計算資產比例中..." : "暫無資產數據"}
        </p>
      </div>
    );
  }

  // 1. 根據 Sector 聚合數據 (用於預設視圖)
  const sectorMap: Record<string, number> = {};
  data.forEach(item => {
    const sectorName = item.sector || 'Other';
    sectorMap[sectorName] = (sectorMap[sectorName] || 0) + (item.market_value || 0);
  });

  const sectorData = Object.entries(sectorMap).map(([name, value]) => ({
    name,
    value
  })).sort((a, b) => b.value - a.value);

  // 2. 根據選定的 Sector 過濾個別持倉數據 (用於下鑽視圖)
  const holdingsInSector = selectedSector 
    ? data
        .filter(item => item.sector === selectedSector)
        .map(item => ({
          name: item.symbol,
          value: item.market_value
        }))
        .sort((a, b) => b.value - a.value)
    : [];

  const chartData = selectedSector ? holdingsInSector : sectorData;

  const handleClick = (entry: any) => {
    if (onSectorClick) {
      // 如果已經選中該產業，則取消選中，否則選中該產業
      onSectorClick(selectedSector === entry.name ? null : entry.name);
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const total = chartData.reduce((sum, item) => sum + item.value, 0);
      const percent = ((payload[0].value / total) * 100).toFixed(1);
      const displayName = selectedSector ? payload[0].name : translateSector(payload[0].name);
      
      return (
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg shadow-xl">
          <p className="text-xs text-slate-400 mb-1">{displayName}</p>
          <p className="text-sm font-bold text-white">
            ${payload[0].value.toLocaleString()} ({percent}%)
          </p>
          {!selectedSector && (
            <p className="text-[10px] text-blue-400 mt-2">點擊查看詳細持倉</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full min-h-[400px] flex flex-col relative group">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {selectedSector && (
            <button
              onClick={() => onSectorClick?.(null)}
              className="p-1 hover:bg-slate-800 rounded-full text-slate-400 hover:text-white transition-colors"
              title="重置篩選"
            >
              <ArrowLeft size={16} />
            </button>
          )}
          <h3 className="text-lg font-semibold text-white">
            {selectedSector ? `產業: ${translateSector(selectedSector)}` : '產業分佈 (Sector Allocation)'}
          </h3>
        </div>
        {selectedSector && (
          <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20 uppercase tracking-wider font-bold">
            Holdings View
          </span>
        )}
      </div>
      
      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
              onClick={handleClick}
              style={{ cursor: 'pointer' }}
              animationBegin={0}
              animationDuration={600}
            >
              {chartData.map((_entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[index % COLORS.length]} 
                  stroke="none"
                  className="hover:opacity-80 transition-opacity"
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              layout="vertical" 
              align="right" 
              verticalAlign="middle"
              formatter={(value) => <span className="text-xs text-slate-400">{translateSector(value)}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
