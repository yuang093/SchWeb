import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const getSettings = async () => {
  const response = await axios.get(`${API_BASE_URL}/settings`);
  return response.data;
};

export const updateSettings = async (settings: Record<string, string>) => {
  const response = await axios.post(`${API_BASE_URL}/settings`, { settings });
  return response.data;
};
