import api from './client';

export interface RiskMetrics {
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  annual_return: number;
  beta: number | string;
  var_95: number;
  current_value: number;
}

export const getRiskMetrics = async (accountHash?: string): Promise<RiskMetrics> => {
  // 將請求指向 analytics 模組下的 risk-metrics 端點
  const response = await api.get<RiskMetrics>('/analytics/risk-metrics', {
    params: { account_hash: accountHash }
  });
  return response.data;
};
