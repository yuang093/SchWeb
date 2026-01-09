import { useState, useMemo } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { usePrivacy } from '../../context/PrivacyContext';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Holding {
  symbol: string;
  quantity: number;
  price: number;
  cost_basis: number;
  market_value: number;
  total_pnl_pct: number;
  total_pnl: number;
  day_pnl: number;
  day_pnl_pct: number;
  ytd_pnl: number | null;
  ytd_pnl_pct: number | null;
  asset_type: string;
  expiration_date?: string;
  allocation_pct?: number;
  drawdown_pct?: number;
  [key: string]: any;
}

interface HoldingsTableProps {
  data: Holding[];
  loading?: boolean;
  title: string;
}

type SortKey = 'symbol' | 'quantity' | 'price' | 'cost_basis' | 'market_value' | 'total_pnl_pct' | 'total_pnl' | 'day_pnl' | 'day_pnl_pct' | 'ytd_pnl' | 'ytd_pnl_pct' | 'expiration_date' | 'allocation_pct' | 'drawdown_pct';

const safeFormat = (value: number | undefined | null, decimals: number = 2) => {
  if (value === undefined || value === null || isNaN(value)) return "0.00";
  return value.toFixed(decimals);
};

export default function HoldingsTable({ data, loading = false, title }: HoldingsTableProps) {
  const [sortConfig, setSortConfig] = useState<{ key: SortKey, direction: 'asc' | 'desc' } | null>(null);
  const { maskValue } = usePrivacy();

  const isOptionTable = title.toLowerCase().includes('option') || (data.length > 0 && data[0].asset_type === 'OPTION');

  const handleSort = (key: SortKey) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    } else if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      setSortConfig(null);
      return;
    }
    setSortConfig({ key, direction });
  };

  const sortedData = useMemo(() => {
    if (!data) return [];
    const sortableItems = [...data];
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;

        if (typeof aVal === 'number' && typeof bVal === 'number') {
          if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
          if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        } else if (typeof aVal === 'string' && typeof bVal === 'string') {
          const comparison = aVal.localeCompare(bVal);
          return sortConfig.direction === 'asc' ? comparison : -comparison;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [data, sortConfig]);

  if (loading) {
    return (
      <div className="w-full h-64 bg-slate-900 border border-slate-800 rounded-xl animate-pulse flex items-center justify-center mb-6">
        <p className="text-slate-600">{title} 載入中...</p>
      </div>
    );
  }

  if (!sortedData || sortedData.length === 0) {
    return (
      <div className="w-full h-32 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center mb-6">
        <p className="text-slate-500 text-sm font-medium">{title} 暫無持倉資料</p>
      </div>
    );
  }

  const HeaderItem = ({ label, sortKey, align = 'right' }: { label: string, sortKey: SortKey, align?: 'left' | 'right' }) => (
    <th 
      className={cn(
        "px-4 py-4 text-[11px] font-bold text-slate-400 uppercase tracking-tight cursor-pointer hover:text-blue-400 transition-colors select-none",
        align === 'right' ? "text-right" : "text-left"
      )}
      onClick={() => handleSort(sortKey)}
    >
      <div className={cn("flex items-center gap-0.5", align === 'right' ? "justify-end" : "justify-start")}>
        {label}
        <span className="w-3 shrink-0">
          {sortConfig?.key === sortKey ? (
            sortConfig.direction === 'asc' ? <ChevronUp size={10} /> : <ChevronDown size={10} />
          ) : null}
        </span>
      </div>
    </th>
  );

  const getPnlColor = (val: number) => {
    if (val > 0) return "text-emerald-400";
    if (val < 0) return "text-rose-400";
    return "text-slate-400";
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl mb-6">
      <div className="p-4 border-b border-slate-800 bg-slate-800/50">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <div className="overflow-x-auto scrollbar-hide">
        <table className="w-full text-left border-collapse min-w-[1200px]">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-800/20">
              <HeaderItem label="代碼 (Symbol)" sortKey="symbol" align="left" />
              {isOptionTable ? (
                <>
                  <HeaderItem label="數量 (Qty)" sortKey="quantity" />
                  <HeaderItem label="價格 (Price)" sortKey="price" />
                  <HeaderItem label="市場價值 (Market Val)" sortKey="market_value" />
                  <HeaderItem label="當日變動% (Day Chg %)" sortKey="day_pnl_pct" />
                  <HeaderItem label="成本基礎 (Cost)" sortKey="cost_basis" />
                  <HeaderItem label="盈虧% (P&L %)" sortKey="total_pnl_pct" />
                  <HeaderItem label="到期日 (Exp Date)" sortKey="expiration_date" />
                  <HeaderItem label="持股百分比 (Alloc %)" sortKey="allocation_pct" />
                </>
              ) : (
                <>
                  <HeaderItem label="數量 (Qty)" sortKey="quantity" />
                  <HeaderItem label="價格 (Price)" sortKey="price" />
                  <HeaderItem label="市場價值 (Market Val)" sortKey="market_value" />
                  <HeaderItem label="當日變動% (Day Chg %)" sortKey="day_pnl_pct" />
                  <HeaderItem label="成本基礎 (Cost)" sortKey="cost_basis" />
                  <HeaderItem label="盈虧% (P&L %)" sortKey="total_pnl_pct" />
                  <HeaderItem label="最高點下跌" sortKey="drawdown_pct" />
                  <HeaderItem label="持股百分比 (Alloc %)" sortKey="allocation_pct" />
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {sortedData.map((holding, idx) => {
              const symbol = holding.symbol || "UNKNOWN";
              return (
                <tr key={`${symbol}-${idx}`} className="hover:bg-slate-800/50 transition-colors group text-[13px]">
                  <td className="px-4 py-3.5 whitespace-nowrap text-left">
                    <span className="font-bold text-blue-400 group-hover:text-blue-300 transition-colors">{symbol}</span>
                  </td>
                  {isOptionTable ? (
                    <>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-300 text-right font-mono">
                        {maskValue(safeFormat(holding.quantity, 3), 'number')}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-300 text-right font-mono">
                        ${maskValue(safeFormat(holding.price), 'currency')}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap font-medium text-white text-right font-mono">
                        ${maskValue((holding.market_value ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }), 'currency')}
                      </td>
                      <td className={cn("px-4 py-3.5 whitespace-nowrap font-bold text-right font-mono", getPnlColor(holding.day_pnl_pct))}>
                        {holding.day_pnl_pct >= 0 ? "+" : ""}{safeFormat(holding.day_pnl_pct)}%
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-300 text-right font-mono">
                        ${maskValue(safeFormat(holding.cost_basis), 'currency')}
                      </td>
                      <td className={cn("px-4 py-3.5 whitespace-nowrap font-bold text-right font-mono", getPnlColor(holding.total_pnl_pct))}>
                        {holding.total_pnl_pct >= 0 ? "+" : ""}{safeFormat(holding.total_pnl_pct)}%
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-400 text-right font-mono">
                        {holding.expiration_date || "-"}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-400 text-right font-mono">
                        {holding.allocation_pct !== undefined ? `${safeFormat(holding.allocation_pct)}%` : "-"}
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-300 text-right font-mono">
                        {maskValue(safeFormat(holding.quantity, 3), 'number')}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-300 text-right font-mono">
                        ${maskValue(safeFormat(holding.price), 'currency')}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap font-medium text-white text-right font-mono">
                        ${maskValue((holding.market_value ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }), 'currency')}
                      </td>
                      <td className={cn("px-4 py-3.5 whitespace-nowrap font-bold text-right font-mono", getPnlColor(holding.day_pnl_pct))}>
                        {holding.day_pnl_pct >= 0 ? "+" : ""}{safeFormat(holding.day_pnl_pct)}%
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-300 text-right font-mono">
                        ${maskValue(safeFormat(holding.cost_basis), 'currency')}
                      </td>
                      <td className={cn("px-4 py-3.5 whitespace-nowrap font-bold text-right font-mono", getPnlColor(holding.total_pnl_pct))}>
                        {holding.total_pnl_pct >= 0 ? "+" : ""}{safeFormat(holding.total_pnl_pct)}%
                      </td>
                      <td className={cn("px-4 py-3.5 whitespace-nowrap font-bold text-right font-mono", (holding.drawdown_pct && holding.drawdown_pct !== 0) ? "text-rose-400" : "text-slate-400")}>
                        {(holding.drawdown_pct && holding.drawdown_pct !== 0) ? `${holding.drawdown_pct.toFixed(1)}%` : "-"}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap text-slate-400 text-right font-mono">
                        {holding.allocation_pct !== undefined ? `${safeFormat(holding.allocation_pct)}%` : "-"}
                      </td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
