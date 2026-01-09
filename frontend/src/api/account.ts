import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

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
  expiration_date?: string;
  allocation_pct?: number;
  drawdown_pct?: number;
}

export const getAccountList = async () => {
  const response = await axios.get(`${API_BASE_URL}/account/list`);
  return response.data;
};

export const getAccountSummary = async (accountHash?: string) => {
  const params = accountHash ? { account_hash: accountHash } : {};
  const response = await axios.get(`${API_BASE_URL}/account/summary`, { params });
  return response.data;
};

export const getPositions = async (accountHash?: string) => {
  const params = accountHash ? { account_hash: accountHash } : {};
  const response = await axios.get(`${API_BASE_URL}/account/positions`, { params });
  return response.data;
};

export const getAssetHistory = async () => {
  const response = await axios.get(`${API_BASE_URL}/account/history`);
  return response.data;
};
