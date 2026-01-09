import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface HistoryPoint {
  date: string;
  total: number;
  [key: string]: string | number; // 支援動態帳戶 ID 鍵值
}

export interface HistoryResponse {
  history: HistoryPoint[];
  accounts: string[];
}

export const getHistoricalNetWorth = async (): Promise<HistoryResponse> => {
  const response = await axios.get(`${API_BASE_URL}/analytics/history`);
  return response.data;
};
