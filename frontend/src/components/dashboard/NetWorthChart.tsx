import { useState, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { HistoryPoint } from '../../api/analytics';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { usePrivacy } from '../../context/PrivacyContext';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface NetWorthChartProps {
  data: HistoryPoint[];
  accounts: string[];
  selectedAccountHash?: string;
  loading?: boolean;
}

type TimeRange = '1W' | '1M' | '3M' | '6M' | 'YTD' | '1Y' | '2Y' | 'ALL';

export default function NetWorthChart({ data, accounts, selectedAccountHash, loading = false }: NetWorthChartProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('ALL');
  const { isPrivacyMode, maskValue } = usePrivacy();

  const activeDataKey = useMemo(() => {
    console.log('DEBUG: NetWorthChart selectedAccountHash:', selectedAccountHash);
    console.log('DEBUG: NetWorthChart available accounts:', accounts);
    
    if (!selectedAccountHash) return 'total';
    
    // 1. 精確匹配
    if (accounts.includes(selectedAccountHash)) return selectedAccountHash;
    
    // 2. 部分匹配 (應對不同格式的 Hash)
    const partialMatch = accounts.find(acc =>
      acc.toLowerCase().includes(selectedAccountHash.toLowerCase()) ||
      selectedAccountHash.toLowerCase().includes(acc.toLowerCase())
    );
    if (partialMatch) return partialMatch;

    // 3. 回退到 Live Sync 或 Total
    if (accounts.includes('total_sync')) return 'total_sync';
    
    // 4. 最終回退：如果連 total 都沒，且 data 有點，則取點中第一個非 date 的 key
    if (!accounts.includes('total') && data.length > 0) {
      const firstPointKeys = Object.keys(data[0]);
      const fallbackKey = firstPointKeys.find(k => k !== 'date' && k !== 'total');
      if (fallbackKey) return fallbackKey;
    }

    return 'total';
  }, [selectedAccountHash, accounts, data]);

  const filteredData = useMemo(() => {
    console.log('DEBUG: NetWorthChart Data Sample:', data?.[0]);
    if (!data || data.length === 0) return [];

    let startDate = new Date();
    const lastDate = new Date(data[data.length - 1].date);
    
    switch (timeRange) {
      case '1W': startDate.setDate(lastDate.getDate() - 7); break;
      case '1M': startDate.setMonth(lastDate.getMonth() - 1); break;
      case '3M': startDate.setMonth(lastDate.getMonth() - 3); break;
      case '6M': startDate.setMonth(lastDate.getMonth() - 6); break;
      case 'YTD': startDate = new Date(lastDate.getFullYear(), 0, 1); break;
      case '1Y': startDate.setFullYear(lastDate.getFullYear() - 1); break;
      case '2Y': startDate.setFullYear(lastDate.getFullYear() - 2); break;
      case 'ALL': return data;
    }

    return data.filter(item => new Date(item.date) >= startDate);
  }, [data, timeRange]);

  if (loading) {
    return (
      <div className="w-full h-full min-h-[300px] bg-slate-900/50 rounded-xl animate-pulse flex items-center justify-center border border-slate-800">
        <p className="text-slate-500 text-sm font-medium">載入圖表中...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="w-full h-full min-h-[300px] bg-slate-900 rounded-xl flex items-center justify-center border border-slate-800">
        <p className="text-slate-500 text-sm font-medium">尚無歷史趨勢數據</p>
      </div>
    );
  }

  const formatYAxis = (value: number) => {
    if (isPrivacyMode) return '***';
    if (Math.abs(value) >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (Math.abs(value) >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value.toFixed(0)}`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg shadow-xl">
          <p className="text-xs text-slate-400 mb-1">{label}</p>
          <p className="text-sm font-bold text-blue-400">
            ${maskValue(payload[0].value.toLocaleString(undefined, { minimumFractionDigits: 2 }), 'currency')}
          </p>
        </div>
      );
    }
    return null;
  };

  const timeRanges: TimeRange[] = ['1W', '1M', '3M', '6M', 'YTD', '1Y', '2Y', 'ALL'];

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-white whitespace-nowrap">資產淨值走勢</h3>
        </div>
        <div className="flex gap-1 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          {timeRanges.map((range) => (
            <button 
              key={range} 
              onClick={() => setTimeRange(range)}
              className={cn(
                "px-2.5 py-1 text-[10px] md:text-xs font-medium rounded-md transition-colors whitespace-nowrap", 
                range === timeRange ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              )}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-[250px] md:min-h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={filteredData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 10 }}
              minTickGap={60}
              tickFormatter={(str) => {
                const parts = str.split('-');
                if (parts.length >= 3) {
                  return `${parts[1]}/${parts[2]}`;
                }
                return str;
              }}
            />
            <YAxis 
              hide={false}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickFormatter={formatYAxis}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey={activeDataKey}
              stroke="#3b82f6"
              connectNulls={true}
              strokeWidth={3}
              isAnimationActive={true}
              fillOpacity={1}
              fill="url(#colorValue)"
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
