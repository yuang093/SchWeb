import api from './client';

export interface Position {
  symbol: string;
  quantity: number;
  price: number;
  cost_basis: number;
  market_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  day_pnl: number;
  day_pnl_pct: number;
  ytd_pnl: number | null;
  ytd_pnl_pct: number | null;
  asset_type: string;
  sector: string;
  expiration_date?: string;
  allocation_pct?: number;
  drawdown_pct?: number;
}

export const getAccountList = async () => {
  const response = await api.get('/account/list');
  return response.data;
};

export const getAccountSummary = async (accountHash?: string) => {
  const params = accountHash ? { account_hash: accountHash } : {};
  const response = await api.get('/account/summary', { params });
  return response.data;
};

export const getPositions = async (accountHash?: string) => {
  const params = accountHash ? { account_hash: accountHash } : {};
  const response = await api.get('/account/positions', { params });
  return response.data;
};

export const getAssetHistory = async () => {
  const response = await api.get('/account/history');
  return response.data;
};
