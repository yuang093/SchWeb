import axios from 'axios';

// 動態獲取 API 網址，確保在區域網路 (LAN) 下手機也能正確連線
const API_HOST = window.location.hostname;
const API_BASE_URL = `http://${API_HOST}:8000/api/v1`;

const api = axios.create({
  baseURL: API_BASE_URL,
});

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export const sendMessageToCopilot = async (message: string): Promise<string> => {
  const response = await api.post('/copilot/chat', { message });
  return response.data.reply;
};
