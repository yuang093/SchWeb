import { useState, useEffect } from 'react';
import MainLayout from '../components/layout/MainLayout';
import { getSettings, updateSettings } from '../api/settings';
import { Save, Shield, Key, Link as LinkIcon, CheckCircle2 } from 'lucide-react';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    SCHWAB_API_KEY: '',
    SCHWAB_API_SECRET: '',
    SCHWAB_REDIRECT_URI: '',
  });

  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await getSettings();
        setFormData({
          SCHWAB_API_KEY: data.SCHWAB_API_KEY || '',
          SCHWAB_API_SECRET: data.SCHWAB_API_SECRET || '',
          SCHWAB_REDIRECT_URI: data.SCHWAB_REDIRECT_URI || '',
        });
      } catch (error) {
        console.error('Failed to load settings:', error);
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
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

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-white">系統設定</h1>
          <p className="text-slate-400 mt-1">管理您的 Schwab API 金鑰與連線參數</p>
        </header>

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
                  placeholder={loading ? "載入中..." : "輸入您的 API Key"}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
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
                  placeholder={loading ? "載入中..." : "輸入您的 API Secret"}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
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

            <div className="pt-4 flex items-center justify-between">
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
          </form>
        </div>

        <div className="mt-8 p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl">
          <h4 className="text-sm font-bold text-blue-400 mb-1">提示：</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            更換 API 金鑰後，系統會嘗試重新讀取。如果認證失敗，您可能仍需手動執行一次後端的授權腳本 (`python backend/scripts/auth_schwab.py`) 以更新 token.json。
          </p>
        </div>
      </div>
    </MainLayout>
  );
}
