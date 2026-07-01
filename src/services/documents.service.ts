import api from './api';
import { Platform } from 'react-native';

export const documentsService = {
  fetchAllDocuments: async () => {
    const response = await api.get('/api/documents/all');
    return response.data;
  },

  sendDocument: async (id: number) => {
    const response = await api.post(`/api/documents/${id}/send`);
    return response.data;
  },

  deleteDocument: async (id: number) => {
    const response = await api.delete(`/api/documents/${id}`);
    return response.data;
  },

  downloadDocument: async (id: number, filename: string) => {
    const response = await api.get(`/api/documents/${id}/download`, {
      responseType: 'blob'
    });
    
    const blob = new Blob([response.data], { type: 'application/pdf' });
    
    if (Platform.OS === 'web') {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename || `document_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } else {
      // Pour le mobile, on peut utiliser expo-file-system ou expo-sharing
      // L'implémentation dépendra des librairies disponibles
      console.warn("Download non supporté nativement dans ce stub, nécessiterait expo-file-system");
    }
  }
};
