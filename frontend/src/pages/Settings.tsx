import { useState, useEffect, useCallback } from 'react';
import MainLayout from '../components/layout/MainLayout';
import { getSettings, updateSettings, importCsv, resetHistory } from '../api/settings';
import { getAuthStatus, getLoginUrl, submitAuthCode } from '../api/auth';
import { getAccountList } from '../api/account';
import { Save, Shield, Key, Link as LinkIcon, CheckCircle2, Upload, FileText, AlertCircle, Loader2, ExternalLink, Send, Trash2, User } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  
  // 認證狀態
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  // 帳戶清單與選擇
  const [accounts, setAccounts] = useState<any[]>([]);
  const [targetAccountHash, setTargetAccountHash] = useState('');

  // 匯入狀態
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    stats?: any;
    error?: string;
    filename?: string;
    type?: 'balances' | 'transactions';
  } | null>(null);

  const [isResetting, setIsResetting] = useState(false);

  const [formData, setFormData] = useState({
    SCHWAB_API_KEY: '',
    SCHWAB_API_SECRET: '',
    SCHWAB_REDIRECT_URI: '',
  });

  const [authCode, setAuthCode] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [submittingCode, setSubmittingCode] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInitialData() {
      setLoading(true);
      setError(null);
      try {
        // 並行獲取設定、認證狀態與帳戶清單
        const [settingsData, authData, accountsData] = await Promise.all([
          getSettings(),
          getAuthStatus(),
          getAccountList()
        ]);
        
        setFormData({
          SCHWAB_API_KEY: settingsData.SCHWAB_API_KEY || '',
          SCHWAB_API_SECRET: settingsData.SCHWAB_API_SECRET || '',
          SCHWAB_REDIRECT_URI: settingsData.SCHWAB_REDIRECT_URI || '',
        });
        
        setIsAuthenticated(authData.authenticated);

        // 過濾出有效的帳戶供匯入選擇
        const validAccounts = accountsData.filter((a: any) => a.hash_value && a.hash_value !== 'ERROR');
        setAccounts(validAccounts);
        if (validAccounts.length > 0) {
          setTargetAccountHash(validAccounts[0].hash_value);
        }
      } catch (error: any) {
        console.error('Failed to load initial data:', error);
        setError('無法載入設定或認證狀態。請確保後端伺服器已啟動。');
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    try {
      await updateSettings(formData);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('儲存失敗，請檢查後端連線');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleConnectSchwab = async () => {
    try {
      const { login_url } = await getLoginUrl();
      if (login_url) {
        // 使用 window.open 開啟授權網址，避免當前頁面被跳轉
        window.open(login_url, '_blank');
        setShowCodeInput(true);
      } else {
        alert('無法獲取授權網址，請檢查 API Key 設定。');
      }
    } catch (error) {
      console.error('Failed to get login URL:', error);
      alert('請求失敗，請稍後再試。');
    }
  };

  const handleSubmitCode = async () => {
    if (!authCode.trim()) {
      alert('請輸入授權代碼或網址');
      return;
    }
    
    setSubmittingCode(true);
    try {
      const result = await submitAuthCode(authCode.trim());
      alert(result.message || '授權成功！');
      
      // 重新檢查認證狀態
      const authData = await getAuthStatus();
      setIsAuthenticated(authData.authenticated);
      
      if (authData.authenticated) {
        setShowCodeInput(false);
        setAuthCode('');
      }
    } catch (error: any) {
      console.error('Auth failed:', error);
      const errMsg = error.response?.data?.error || '請檢查代碼是否正確或已過期';
      alert('授權失敗：' + errMsg);
    } finally {
      setSubmittingCode(false);
    }
  };

  const handleResetHistory = async () => {
    if (!confirm('確定要刪除所有資產歷史紀錄嗎？此動作將清空所有匯入與同步的走勢數據，且無法復原。')) {
      return;
    }

    setIsResetting(true);
    try {
      const result = await resetHistory();
      alert(result.message || '已成功清空歷史資料');
      window.location.reload();
    } catch (error: any) {
      console.error('Reset failed:', error);
      alert('重置失敗：' + (error.response?.data?.detail || '伺服器錯誤'));
    } finally {
      setIsResetting(false);
    }
  };

  const onDropBalances = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    if (!targetAccountHash) {
      alert('請先選擇目標帳戶');
      return;
    }

    const file = acceptedFiles[0];
    setImporting(true);
    setImportResult(null);
    
    try {
      const result = await importCsv(file, targetAccountHash);
      setImportResult({
        success: true,
        stats: result.stats,
        filename: file.name,
        type: 'balances'
      });
    } catch (error: any) {
      setImportResult({
        success: false,
        error: error.response?.data?.detail || '檔案處理失敗',
        filename: file.name
      });
    } finally {
      setImporting(false);
    }
  }, [targetAccountHash]);

  const onDropTransactions = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    if (!targetAccountHash) {
      alert('請先選擇目標帳戶');
      return;
    }
    const file = acceptedFiles[0];
    setImporting(true);
    setImportResult(null);
    try {
      const result = await importCsv(file, targetAccountHash);
      setImportResult({
        success: true,
        stats: result.stats,
        filename: file.name,
        type: 'transactions'
      });
    } catch (error: any) {
      setImportResult({
        success: false,
        error: error.response?.data?.detail || '檔案處理失敗',
        filename: file.name,
        type: 'transactions'
      });
    } finally {
      setImporting(false);
    }
  }, [targetAccountHash]);

  const { getRootProps: getRootPropsBalances, getInputProps: getInputPropsBalances, isDragActive: isDragActiveBalances } = useDropzone({
    onDrop: onDropBalances,
    accept: { 'text/csv': ['.csv'] },
    multiple: false
  });

  const { getRootProps: getRootPropsTransactions, getInputProps: getInputPropsTransactions, isDragActive: isDragActiveTransactions } = useDropzone({
    onDrop: onDropTransactions,
    accept: { 'text/csv': ['.csv'] },
    multiple: false
  });

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-white">系統設定</h1>
          <p className="text-slate-400 mt-1">管理您的 Schwab API 金鑰與連線參數</p>
        </header>

        <div className="space-y-8">
          {/* 錯誤提示 */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3 text-red-500">
              <AlertCircle className="mt-0.5 shrink-0" size={18} />
              <div>
                <p className="text-sm font-bold">連線異常</p>
                <p className="text-xs opacity-80 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* 1. API 認證區塊 */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-slate-800 bg-slate-900/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-500">
                  <Shield size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Schwab API 認證</h3>
                  <p className="text-sm text-slate-500">此設定將儲存在資料庫中，並優先於 .env 檔案</p>
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="space-y-4">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-2">
                    <Key size={14} />
                    App Key (SCHWAB_API_KEY)
                  </label>
                  <input
                    type="text"
                    name="SCHWAB_API_KEY"
                    value={formData.SCHWAB_API_KEY}
                    onChange={handleChange}
                    disabled={loading}
                    placeholder={loading ? "正在與伺服器連線..." : "輸入您的 API Key"}
                    className={`w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  />
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-2">
                    <Shield size={14} />
                    App Secret (SCHWAB_API_SECRET)
                  </label>
                  <input
                    type="password"
                    name="SCHWAB_API_SECRET"
                    value={formData.SCHWAB_API_SECRET}
                    onChange={handleChange}
                    disabled={loading}
                    placeholder={loading ? "正在與伺服器連線..." : "輸入您的 API Secret"}
                    className={`w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  />
                  <p className="text-[11px] text-slate-500 mt-1.5">基於安全考慮，現有金鑰將以遮罩方式顯示。</p>
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-2">
                    <LinkIcon size={14} />
                    Redirect URI (SCHWAB_REDIRECT_URI)
                  </label>
                  <input
                    type="text"
                    name="SCHWAB_REDIRECT_URI"
                    value={formData.SCHWAB_REDIRECT_URI}
                    onChange={handleChange}
                    placeholder={loading ? "載入中..." : "https://127.0.0.1"}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                  />
                </div>
              </div>

              <div className="pt-4 space-y-6">
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    {success && (
                      <span className="flex items-center gap-2 text-emerald-500 font-medium">
                        <CheckCircle2 size={16} />
                        設定已成功儲存
                      </span>
                    )}
                  </div>
                  <button
                    type="submit"
                    disabled={saving || loading}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg shadow-blue-600/20"
                  >
                    {saving ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        儲存中...
                      </>
                    ) : (
                      <>
                        <Save size={18} />
                        儲存設定
                      </>
                    )}
                  </button>
                </div>

                {/* 嘉信連線狀態與按鈕 */}
                <div className="border-t border-slate-800 pt-6">
                  <div className="bg-slate-950/50 rounded-xl p-4 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full ${isAuthenticated ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`} />
                      <div>
                        <h4 className="text-sm font-bold text-white">嘉信連線狀態</h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {isAuthenticated ? '已成功連線並取得授權' : '尚未連線或 Token 已過期'}
                        </p>
                      </div>
                    </div>
                    
                    <button
                      type="button"
                      onClick={handleConnectSchwab}
                      disabled={loading}
                      className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg
                        ${isAuthenticated
                          ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20'}`}
                    >
                      {isAuthenticated ? (
                        <>
                          <ExternalLink size={18} />
                          重新授權 (Re-authorize)
                        </>
                      ) : (
                        <>
                          <LinkIcon size={18} />
                          連接嘉信 (Connect to Schwab)
                        </>
                      )}
                    </button>
                  </div>

                  {/* 手動輸入授權碼區塊 */}
                  {(showCodeInput || !isAuthenticated) && (
                    <div className="mt-4 p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-4 animate-in fade-in slide-in-from-top-2">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="text-blue-500 shrink-0 mt-0.5" size={16} />
                        <p className="text-xs text-slate-400 leading-relaxed">
                          授權完成後，嘉信會跳轉回您的 Redirect URI。請複製跳轉後網址中的 <code className="text-blue-400 font-mono">code</code> 參數，或直接將**完整網址**貼入下方輸入框。
                        </p>
                      </div>
                      
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={authCode}
                          onChange={(e) => setAuthCode(e.target.value)}
                          placeholder="在此處貼入 code 或跳轉後的網址..."
                          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                        <button
                          type="button"
                          onClick={handleSubmitCode}
                          disabled={submittingCode || !authCode}
                          className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all"
                        >
                          {submittingCode ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Send size={16} />
                          )}
                          確認授權
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </form>
          </div>

          {/* 2. 資料匯入區塊 */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-slate-800 bg-slate-900/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-500">
                  <Upload size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">資料匯入 (CSV Import)</h3>
                  <p className="text-sm text-slate-500">上傳嘉信匯出的資產或交易紀錄 CSV</p>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-8">
              {/* 帳戶選擇器 (共用) */}
              <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-4 space-y-3">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-400">
                  <User size={14} className="text-blue-500" />
                  1. 選擇匯入目標帳戶
                </label>
                <select
                  value={targetAccountHash}
                  onChange={(e) => setTargetAccountHash(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all cursor-pointer"
                >
                  {accounts.length > 0 ? (
                    accounts.map((acc) => (
                      <option key={acc.hash_value} value={acc.hash_value}>
                        {acc.account_name} - (...{acc.account_number.slice(-3)})
                      </option>
                    ))
                  ) : (
                    <option value="">(尚未載入帳戶，請先完成嘉信連線)</option>
                  )}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 匯入資產走勢 */}
                <div className="space-y-3">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-400">
                    <FileText size={14} className="text-emerald-500" />
                    2a. 匯入歷史資產 (Balances)
                  </label>
                  <div
                    {...getRootPropsBalances()}
                    className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer h-48 flex flex-col items-center justify-center
                      ${isDragActiveBalances ? 'border-blue-500 bg-blue-500/5' : 'border-slate-800 hover:border-slate-700 bg-slate-950/50'}
                      ${importing ? 'opacity-50 pointer-events-none' : ''}`}
                  >
                    <input {...getInputPropsBalances()} />
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center text-slate-400">
                        {importing && importResult?.type === 'balances' ? <Loader2 size={20} className="animate-spin text-blue-500" /> : <FileText size={20} />}
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">上傳 Balances CSV</p>
                        <p className="text-[10px] text-slate-500 mt-1">
                          用於繪製歷史淨值走勢
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 匯入交易紀錄 */}
                <div className="space-y-3">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-400">
                    <Send size={14} className="text-blue-500" />
                    2b. 匯入交易紀錄 (Transactions)
                  </label>
                  <div
                    {...getRootPropsTransactions()}
                    className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer h-48 flex flex-col items-center justify-center
                      ${isDragActiveTransactions ? 'border-blue-500 bg-blue-500/5' : 'border-slate-800 hover:border-slate-700 bg-slate-950/50'}
                      ${importing ? 'opacity-50 pointer-events-none' : ''}`}
                  >
                    <input {...getInputPropsTransactions()} />
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-10 h-10 bg-slate-900 rounded-full flex items-center justify-center text-slate-400">
                        {importing && importResult?.type === 'transactions' ? <Loader2 size={20} className="animate-spin text-blue-500" /> : <Upload size={20} />}
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">上傳 Transactions CSV</p>
                        <p className="text-[10px] text-slate-500 mt-1">
                          用於校正風險指標與本金
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {importResult && (
                <div className={`p-4 rounded-lg border flex gap-4 ${importResult.success ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
                  <div className={importResult.success ? 'text-emerald-500' : 'text-red-500'}>
                    {importResult.success ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                  </div>
                  <div className="flex-1">
                    <h4 className={`text-sm font-bold ${importResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                      {importResult.success ? '匯入成功' : '匯入失敗'}
                    </h4>
                    <p className="text-xs text-slate-400 mt-1">
                      檔案：{importResult.filename}
                    </p>
                    {importResult.success && importResult.stats && (
                      <div className="mt-3 grid grid-cols-2 gap-2">
                        {importResult.stats.dividends !== undefined && (
                          <div className="bg-slate-950/50 p-2 rounded border border-slate-800">
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">新股息</p>
                            <p className="text-lg text-white font-mono">{importResult.stats.dividends}</p>
                          </div>
                        )}
                        {importResult.stats.trades !== undefined && (
                          <div className="bg-slate-950/50 p-2 rounded border border-slate-800">
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">新交易</p>
                            <p className="text-lg text-white font-mono">{importResult.stats.trades}</p>
                          </div>
                        )}
                        {importResult.stats.history_records !== undefined && (
                          <div className="bg-slate-950/50 p-2 rounded border border-slate-800 col-span-2">
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">資產歷史紀錄</p>
                            <p className="text-lg text-white font-mono">{importResult.stats.history_records} 筆</p>
                          </div>
                        )}
                        {importResult.stats.skipped !== undefined && (
                          <div className="bg-slate-950/50 p-2 rounded border border-slate-800 col-span-2">
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">跳過重複筆數</p>
                            <p className="text-sm text-slate-400">{importResult.stats.skipped}</p>
                          </div>
                        )}
                        {importResult.stats.transaction_history !== undefined && (
                          <div className="bg-slate-950/50 p-2 rounded border border-slate-800 col-span-2">
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">交易紀錄 (TransactionHistory)</p>
                            <p className="text-lg text-white font-mono">{importResult.stats.transaction_history} 筆</p>
                          </div>
                        )}
                      </div>
                    )}
                    {importResult.error && (
                      <p className="text-xs text-red-400 mt-2 bg-red-950/30 p-2 rounded border border-red-900/50">
                        錯誤：{importResult.error}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 3. 資料管理區塊 */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-slate-800 bg-slate-900/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-rose-500/10 rounded-lg flex items-center justify-center text-rose-500">
                  <Trash2 size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">資料管理 (Data Management)</h3>
                  <p className="text-sm text-slate-500">危險操作：重置系統歷史數據</p>
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="bg-rose-500/5 border border-rose-500/10 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-rose-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <p className="text-sm font-bold text-white">清空歷史走勢</p>
                    <p className="text-xs text-slate-500 mt-1">這將刪除所有匯入的歷史餘額以及 Live 同步的快照數據。這不會影響您的 API 設定或交易紀錄。</p>
                  </div>
                </div>
                
                <button
                  type="button"
                  onClick={handleResetHistory}
                  disabled={isResetting}
                  className="bg-rose-600 hover:bg-rose-500 disabled:bg-slate-800 disabled:text-slate-500 text-white px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg shadow-rose-600/20 flex items-center gap-2 whitespace-nowrap"
                >
                  {isResetting ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />}
                  清空所有歷史走勢
                </button>
              </div>
            </div>
          </div>

          {/* 提示區 */}
          <div className="mt-8 p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl">
            <h4 className="text-sm font-bold text-blue-400 mb-1">提示：</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              更換 API 金鑰後，系統會嘗試重新讀取。如果認證失敗，您可能仍需手動執行一次後端的授權腳本 (`python backend/scripts/auth_schwab.py`) 以更新 token.json。
            </p>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
