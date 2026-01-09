import { LayoutDashboard, Wallet, BarChart3, Settings, HelpCircle, Menu, X, Cpu, Power, LineChart, Sparkles, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { usePrivacy } from '../../context/PrivacyContext';
import { Link, useLocation } from 'react-router-dom';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { name: '總覽儀表板', icon: LayoutDashboard, path: '/' },
  { name: '投資組合', icon: Wallet, path: '/portfolio' },
  { name: '風險分析', icon: BarChart3, path: '/risk' },
  { name: 'AI Copilot', icon: Cpu, path: '/ai' },
  { name: '系統設定', icon: Settings, path: '/settings' },
];

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);
  const { isLiveMode, setLiveMode } = useAppStore();
  const { isPrivacyMode, togglePrivacyMode } = usePrivacy();
  const location = useLocation();

  return (
    <>
      {/* Mobile Toggle */}
      <button 
        className="fixed top-4 left-4 z-50 p-2 bg-gray-800 text-white rounded-md lg:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar Container */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 border-r border-slate-800 transform transition-transform duration-300 ease-in-out lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-8 border-b border-slate-800/50 mb-4">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-400 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                <LineChart size={22} className="text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-slate-900 rounded-full flex items-center justify-center">
                <Sparkles size={10} className="text-amber-400" />
              </div>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center">
                <span className="text-xl font-bold text-white tracking-tight">Schwab</span>
                <span className="text-xl font-bold text-blue-400 tracking-tight">.AI</span>
              </div>
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-[0.2em] leading-none mt-1">
                Investment Pilot
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group",
                    isActive 
                      ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-inner" 
                      : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                  )}
                >
                  <item.icon size={20} className={cn(
                    "transition-colors",
                    isActive ? "text-blue-400" : "group-hover:text-blue-400"
                  )} />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Mode Switcher */}
          <div className="px-6 py-4 space-y-3">
            {/* Privacy Mode Toggle */}
            <div className="flex items-center justify-between p-3 bg-slate-950/50 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2">
                {isPrivacyMode ? (
                  <EyeOff size={14} className="text-amber-400" />
                ) : (
                  <Eye size={14} className="text-blue-400" />
                )}
                <span className="text-xs font-bold text-slate-300">
                  {isPrivacyMode ? 'PRIVACY ON' : 'PRIVACY OFF'}
                </span>
              </div>
              <button 
                onClick={togglePrivacyMode}
                title="隱藏敏感金額"
                className={cn(
                  "relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none",
                  isPrivacyMode ? "bg-amber-600" : "bg-slate-700"
                )}
              >
                <span className={cn(
                  "inline-block h-3 w-3 transform rounded-full bg-white transition-transform",
                  isPrivacyMode ? "translate-x-5" : "translate-x-1"
                )} />
              </button>
            </div>

            {/* Live/Demo Mode Toggle */}
            <div className="flex items-center justify-between p-3 bg-slate-950/50 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2">
                <Power size={14} className={isLiveMode ? "text-emerald-500" : "text-amber-500"} />
                <span className="text-xs font-bold text-slate-300">
                  {isLiveMode ? 'LIVE MODE' : 'DEMO MODE'}
                </span>
              </div>
              <button 
                onClick={() => setLiveMode(!isLiveMode)}
                className={cn(
                  "relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none",
                  isLiveMode ? "bg-emerald-600" : "bg-amber-600"
                )}
              >
                <span className={cn(
                  "inline-block h-3 w-3 transform rounded-full bg-white transition-transform",
                  isLiveMode ? "translate-x-5" : "translate-x-1"
                )} />
              </button>
            </div>
          </div>

          {/* Footer Info */}
          <div className="p-4 border-t border-slate-800">
            <div className="flex items-center gap-3 px-4 py-3 text-slate-500 hover:text-white cursor-pointer transition-colors">
              <HelpCircle size={20} />
              <span className="text-sm">幫助中心</span>
            </div>
            <div className="mt-4 px-4 py-2 bg-slate-800/50 rounded-lg">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>API 狀態</span>
                <span className="flex items-center gap-1">
                  <span className={cn(
                    "w-2 h-2 rounded-full animate-pulse",
                    isLiveMode ? "bg-green-500" : "bg-amber-500"
                  )}></span>
                  {isLiveMode ? 'Connected' : 'Simulated'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
