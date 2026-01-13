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

export const getRiskMetrics = async (): Promise<RiskMetrics> => {
  const response = await api.get<RiskMetrics>('/risk/metrics');
  return response.data;
};
