import api from './client';

export const getAuthStatus = async () => {
  const response = await api.get('/auth/status');
  return response.data;
};

export const getLoginUrl = async () => {
  const response = await api.get('/auth/login');
  return response.data;
};
