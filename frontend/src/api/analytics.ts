import api from './client';

export interface HistoryPoint {
  date: string;
  total: number;
  [key: string]: string | number; // 支援動態帳戶 ID 鍵值
}

export interface HistoryResponse {
  history: HistoryPoint[];
  accounts: string[];
}

export const getHistoricalNetWorth = async (accountHash?: string): Promise<HistoryResponse> => {
  const response = await api.get('/analytics/history', {
    params: { account_hash: accountHash }
  });
  return response.data;
};
