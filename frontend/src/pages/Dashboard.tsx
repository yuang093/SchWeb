import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import MainLayout from '../components/layout/MainLayout'
import StatCard from '../components/dashboard/StatCard'
import NetWorthChart from '../components/dashboard/NetWorthChart'
import HoldingsTable from '../components/dashboard/HoldingsTable'
import AllocationChart from '../components/dashboard/AllocationChart'
import AccountSelector from '../components/dashboard/AccountSelector'
import { getAccountSummary, getPositions, getAccountList } from '../api/account'
import { getHistoricalNetWorth } from '../api/analytics'
import { useAppStore } from '../store/useAppStore'
import { usePrivacy } from '../context/PrivacyContext'
import { Coins, HandCoins } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function Dashboard() {
  const [selectedAccountHash, setSelectedAccountHash] = useState<string>('');
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const { isLiveMode } = useAppStore();
  const { maskValue } = usePrivacy();

  const { data: accounts, isLoading: isAccountsLoading } = useQuery({
    queryKey: ['accountList'],
    queryFn: getAccountList,
  });

  useEffect(() => {
    if (accounts && accounts.length > 0) {
      const validAccounts = accounts.filter((a: any) => a.hash_value && a.hash_value !== 'ERROR');
      if (isLiveMode) {
        if (!selectedAccountHash && validAccounts.length > 0) {
          setSelectedAccountHash(validAccounts[0].hash_value);
        }
      } else {
        if (!selectedAccountHash) {
          setSelectedAccountHash(accounts[0].hash_value || '');
        }
      }
    }
  }, [accounts, selectedAccountHash, isLiveMode]);

  const queryEnabled = isLiveMode ? !!selectedAccountHash : true;

  const { data: summary, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['accountSummary', selectedAccountHash],
    queryFn: () => getAccountSummary(selectedAccountHash),
    enabled: queryEnabled,
    refetchInterval: 30000,
  });

  const { data: history, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['historicalNetWorth'],
    queryFn: getHistoricalNetWorth,
  });

  const { data: positions, isLoading: isPositionsLoading } = useQuery({
    queryKey: ['accountPositions', selectedAccountHash],
    queryFn: () => getPositions(selectedAccountHash),
    enabled: queryEnabled,
  });

  const filteredPositions = useMemo(() => {
    if (!positions) return [];
    if (!selectedSector) return positions;
    return positions.filter((h: any) => h.sector === selectedSector);
  }, [positions, selectedSector]);

  const cashPositions = useMemo(() => {
    return filteredPositions.filter((h: any) => h.asset_type === 'CASH_EQUIVALENT');
  }, [filteredPositions]);

  const stockPositions = useMemo(() => {
    return filteredPositions.filter((h: any) => h.asset_type !== 'OPTION' && h.asset_type !== 'CASH_EQUIVALENT');
  }, [filteredPositions]);

  const optionPositions = useMemo(() => {
    return filteredPositions.filter((h: any) => h.asset_type === 'OPTION');
  }, [filteredPositions]);

  return (
    <MainLayout>
      <div className="grid gap-6">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">總覽儀表板</h1>
            <p className="text-slate-400 mt-1 text-sm md:base">歡迎回來，這是您的資產即時狀況。
              <span className={cn("ml-2 font-bold text-sm", isLiveMode ? "text-green-400" : "text-yellow-400")}>
                {isLiveMode ? "LIVE" : "MOCK"}
              </span>
            </p>
          </div>
          {accounts && accounts.length > 0 && (
            <AccountSelector
              accounts={accounts}
              selectedHash={selectedAccountHash}
              onSelect={setSelectedAccountHash}
              disabled={isAccountsLoading || (isLiveMode && accounts.some((a: any) => a.hash_value === 'ERROR'))}
            />
          )}
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="總資產 (Net Worth)" value={summary?.total_balance || 0} loading={isSummaryLoading} />
          <StatCard title="當日盈虧 (Day P/L)" value={summary?.day_pl || 0} change={summary?.day_pl} changePercent={summary?.day_pl_percent} loading={isSummaryLoading} />
          <StatCard title="現金餘額 (Cash)" value={summary?.cash_balance || 0} loading={isSummaryLoading} />
          <StatCard title="購買力 (Buying Power)" value={summary?.buying_power || 0} loading={isSummaryLoading} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between group hover:border-blue-500/30 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-500 shrink-0">
                <HandCoins size={20} />
              </div>
              <div>
                <p className="text-[10px] md:text-xs text-slate-500 font-medium uppercase tracking-wider">累計股息 (YTD Dividends)</p>
                <h4 className="text-base md:text-lg font-bold text-white">
                  {isSummaryLoading ? "---" : `$${maskValue((summary?.total_dividends || 0).toLocaleString(), 'currency')}`}
                </h4>
              </div>
            </div>
            <div className="hidden sm:block text-[10px] text-emerald-500 font-bold bg-emerald-500/5 px-2 py-1 rounded">PASSIVE INCOME</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between group hover:border-blue-500/30 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-500 shrink-0">
                <Coins size={20} />
              </div>
              <div>
                <p className="text-[10px] md:text-xs text-slate-500 font-medium uppercase tracking-wider">已實現損益 (Realized P&L)</p>
                <h4 className={cn("text-base md:text-lg font-bold", (summary?.realized_pnl || 0) >= 0 ? "text-white" : "text-rose-400")}>
                  {isSummaryLoading ? "---" : `${(summary?.realized_pnl || 0) >= 0 ? '+' : ''}$${maskValue((summary?.realized_pnl || 0).toLocaleString(), 'currency')}`}
                </h4>
              </div>
            </div>
            <div className="hidden sm:block text-[10px] text-blue-400 font-bold bg-blue-500/5 px-2 py-1 rounded">TRADING RECORD</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-4 md:p-6">
            <NetWorthChart 
              data={history?.history || []} 
              accounts={history?.accounts || []}
              loading={isHistoryLoading} 
            />
          </div>
          <div className="lg:col-span-1 h-full min-h-[350px]">
            <AllocationChart
               data={positions ?? []}
               loading={isPositionsLoading}
               selectedSector={selectedSector}
               onSectorClick={setSelectedSector}
            />
          </div>
        </div>

        <div className="grid gap-4">
          <h3 className="text-lg md:text-xl font-bold text-white px-1">持倉明細 (Holdings)</h3>
          {isPositionsLoading && <div className="text-slate-500 px-1">正在載入持倉數據...</div>}
          {!isPositionsLoading && optionPositions.length > 0 && <HoldingsTable title="選擇權持倉 (Option Holdings)" data={optionPositions} loading={false} />}
          {!isPositionsLoading && stockPositions.length > 0 && <HoldingsTable title="股票與共同基金 (Stock & Funds)" data={stockPositions} loading={false} />}
          {!isPositionsLoading && cashPositions.length > 0 && <HoldingsTable title="現金與等價物 (Cash & Equivalents)" data={cashPositions} loading={false} />}
          {!isPositionsLoading && !positions?.length && isLiveMode && !accounts?.some((a: any) => a.hash_value === 'ERROR') && (
            <div className="w-full h-32 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center">
              <p className="text-slate-500 text-sm font-medium">此帳戶當前沒有持倉。</p>
            </div>
          )}
          {isLiveMode && accounts?.some((a: any) => a.hash_value === 'ERROR') && (
            <div className="w-full p-4 bg-rose-900/50 border border-rose-600 rounded-xl text-rose-300">
              ⚠️ 帳戶載入錯誤：請執行 `python backend/scripts/auth_schwab.py` 重新授權。
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
