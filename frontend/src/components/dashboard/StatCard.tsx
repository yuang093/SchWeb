import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { usePrivacy } from '../../context/PrivacyContext';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changePercent?: number;
  prefix?: string;
  suffix?: string;
  loading?: boolean;
}

export default function StatCard({ 
  title, 
  value, 
  change, 
  changePercent, 
  prefix = "$", 
  suffix = "",
  loading = false 
}: StatCardProps) {
  const isPositive = change ? change >= 0 : true;
  const { maskValue } = usePrivacy();

  if (loading) {
    return (
      <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl animate-pulse">
        <div className="h-4 w-24 bg-slate-800 rounded mb-4"></div>
        <div className="h-8 w-32 bg-slate-800 rounded"></div>
      </div>
    );
  }

  const formattedValue = typeof value === 'number' 
    ? value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : value;

  const displayValue = maskValue(formattedValue, 'currency');
  const displayChange = change !== undefined ? maskValue(Math.abs(change).toLocaleString(), 'currency') : '';

  return (
    <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
      <p className="text-sm font-medium text-slate-400">{title}</p>
      <div className="mt-2 flex items-baseline justify-between">
        <h3 className="text-2xl font-bold text-white">
          {prefix}{displayValue}{suffix}
        </h3>
        {change !== undefined && (
          <div className={cn(
            "flex items-center text-xs font-semibold px-2 py-1 rounded-full",
            isPositive ? "text-emerald-400 bg-emerald-400/10" : "text-rose-400 bg-rose-400/10"
          )}>
            {isPositive ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowDownRight size={14} className="mr-1" />}
            {Math.abs(changePercent || 0).toFixed(2)}%
          </div>
        )}
      </div>
      {change !== undefined && (
        <p className={cn(
          "mt-1 text-xs font-medium",
          isPositive ? "text-emerald-500" : "text-rose-500"
        )}>
          {isPositive ? "+" : "-"}${displayChange} Today
        </p>
      )}
    </div>
  );
}
