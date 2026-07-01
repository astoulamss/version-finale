import api from './api';
import type { EmployeeProfile } from '../types';

export const adminService = {
  // Gestion des utilisateurs
  fetchUsers: async () => {
    const response = await api.get('/api/users/');
    return response.data;
  },

  // Alertes de sécurité (vraies alertes système)
  fetchAlerts: async () => {
    const response = await api.get('/api/system-alerts');
    return response.data;
  },

  // Logs système
  fetchLogs: async () => {
    const response = await api.get('/api/history/');
    return response.data;
  },

  // Logs Chatbot IA
  fetchChatbotLogs: async () => {
    const response = await api.get('/api/chatbot/logs');
    return response.data;
  },

  // Dashboard Admin
  fetchAdminDashboard: async () => {
    const response = await api.get('/api/dashboard/admin/cockpit');
    return response.data;
  },

  // Stats globales
  fetchStats: async () => {
    const response = await api.get('/api/dashboard/stats');
    return response.data;
  },

  // Actions d'écriture Admin
  createUser: async (userData: any) => {
    const response = await api.post('/api/users/', userData);
    return response.data;
  },
  resetPassword: async (userId: number, newPassword: string) => {
    const response = await api.post(`/api/users/${userId}/reset-password`, { new_password: newPassword });
    return response.data;
  },
  updateUserRole: async (userId: number, role: string) => {
    const response = await api.put(`/api/users/${userId}`, { role });
    return response.data;
  },
  updateUser: async (userId: number, data: any) => {
    const response = await api.put(`/api/users/${userId}`, data);
    return response.data;
  },
  blockUser: async (userId: number) => {
    const response = await api.delete(`/api/users/${userId}`);
    return response.data;
  },
  hardDeleteUser: async (userId: number) => {
    const response = await api.delete(`/api/users/${userId}/hard`);
    return response.data;
  }
};
