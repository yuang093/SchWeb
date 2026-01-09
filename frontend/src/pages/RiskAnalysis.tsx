import { useQuery } from '@tanstack/react-query';
import MainLayout from '../components/layout/MainLayout';
import StatCard from '../components/dashboard/StatCard';
import { getRiskMetrics } from '../api/risk';
import { AlertTriangle, TrendingUp, ShieldCheck, Zap, Activity } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function RiskAnalysis() {
  const { data: risk, isLoading } = useQuery({
    queryKey: ['riskMetrics'],
    queryFn: getRiskMetrics,
  });

  // Beta 標籤邏輯
  const getBetaDescription = (beta: number | string) => {
    if (typeof beta === 'string') return "N/A";
    if (beta > 1.2) return "Aggressive";
    if (beta < 0.8) return "Defensive";
    return "Balanced";
  };

  return (
    <MainLayout>
      <div className="grid gap-6">
        <header>
          <h1 className="text-3xl font-bold tracking-tight text-white">風險分析 (Risk Analysis)</h1>
          <p className="text-slate-400 mt-2">基於歷史數據與市場基準 (SPY) 計算的深度風險指標。</p>
        </header>

        {/* 第一排：核心風險指標 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="年化波動率 (Volatility)"
            value={(risk?.volatility || 0) * 100}
            suffix="%"
            prefix=""
            loading={isLoading}
          />
          <StatCard
            title="夏普比率 (Sharpe Ratio)"
            value={risk?.sharpe_ratio || 0}
            prefix=""
            loading={isLoading}
          />
          <StatCard
            title="最大回撤 (Max Drawdown)"
            value={(risk?.max_drawdown || 0) * 100}
            suffix="%"
            prefix=""
            loading={isLoading}
          />
        </div>

        {/* 第二排：深度風險指標 (Beta & VaR) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 text-blue-500/10 group-hover:text-blue-500/20 transition-colors">
              <Zap size={100} />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-slate-400 text-sm font-medium">Beta 係數 (vs SPY)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-bold text-white">
                  {isLoading ? "---" : (typeof risk?.beta === 'number' ? risk.beta.toFixed(2) : "N/A")}
                </span>
                {!isLoading && risk && typeof risk.beta === 'number' && (
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-bold",
                    risk.beta > 1.2 ? "bg-red-500/10 text-red-400" : 
                    risk.beta < 0.8 ? "bg-emerald-500/10 text-emerald-400" : 
                    "bg-blue-500/10 text-blue-400"
                  )}>
                    {getBetaDescription(risk.beta)}
                  </span>
                )}
              </div>
              <p className="text-slate-500 text-xs mt-2 italic">
                相對於標普 500 指數的敏感度。1.0 代表同步。
              </p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 text-rose-500/10 group-hover:text-rose-500/20 transition-colors">
              <Activity size={100} />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-slate-400 text-sm font-medium">單日風險值 (VaR 95%)</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-bold text-rose-400">
                  {isLoading ? "---" : `$${Math.abs(risk?.var_95 || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                </span>
              </div>
              <p className="text-slate-500 text-xs mt-2 italic">
                在 95% 信心水準下，單日預期最大損失金額。
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4 text-amber-400">
              <AlertTriangle size={24} />
              <h3 className="text-lg font-semibold">風險評估說明</h3>
            </div>
            <div className="space-y-4 text-sm text-slate-400">
              <div>
                <p className="text-white font-medium mb-1">年化波動率</p>
                <p>反映投資組合價格變動的劇烈程度。當前值為 {( (risk?.volatility || 0) * 100).toFixed(2)}%，代表投資組合的預期年化收益可能在此範圍內震盪。</p>
              </div>
              <div>
                <p className="text-white font-medium mb-1">夏普比率</p>
                <p>每承受一單位風險所獲得的超額收益。數值越高代表性價比越好。目前為 {risk?.sharpe_ratio?.toFixed(2) || '0.00'} (大於 1 為佳)。</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4 text-blue-400">
              <TrendingUp size={24} />
              <h3 className="text-lg font-semibold">績效基準分析</h3>
            </div>
            <div className="space-y-4 text-sm text-slate-400">
              <div className="flex items-center justify-between p-3 bg-slate-950 rounded-lg">
                <span>年化收益率 (預估)</span>
                <span className="text-emerald-400 font-bold">{( (risk?.annual_return || 0) * 100).toFixed(2)}%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-950 rounded-lg">
                <span>無風險利率 (基準)</span>
                <span className="text-slate-200">4.00%</span>
              </div>
              <div className="flex items-center gap-2 mt-4 text-emerald-500/80">
                <ShieldCheck size={16} />
                <span className="text-xs italic">計算基於 SQLite 資料庫中的歷史資產紀錄。</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
