import axios from 'axios';

// 動態獲取 API 網址，確保在區域網路 (LAN) 下手機也能正確連線
const API_HOST = window.location.hostname;
const API_BASE_URL = `http://${API_HOST}:8000/api/v1`;

const api = axios.create({
  baseURL: API_BASE_URL,
});

export interface RiskMetrics {
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  annual_return: number;
  beta: number | string;
  var_95: number;
  current_value: number;
}

export const getRiskMetrics = async (): Promise<RiskMetrics> => {
  const response = await api.get<RiskMetrics>('/risk/metrics');
  return response.data;
};
