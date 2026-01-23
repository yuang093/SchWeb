import api from './client';

export const getSettings = async () => {
  const response = await api.get('/settings');
  return response.data;
};

export const updateSettings = async (settings: Record<string, string>) => {
  const response = await api.post('/settings', { settings });
  return response.data;
};

export const importCsv = async (file: File, accountHash: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('account_hash', accountHash);
  const response = await api.post('/settings/import-csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const resetHistory = async () => {
  const response = await api.delete('/settings/reset-history');
  return response.data;
};
