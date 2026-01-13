import api from './client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export const sendMessageToCopilot = async (message: string): Promise<string> => {
  const response = await api.post('/copilot/chat', { message });
  return response.data.reply;
};
