import api from './api';

export const qvtService = {
  fetchDashboard: async () => {
    const response = await api.get('/api/dashboard/medecine-travail');
    return response.data;
  },
  fetchStats: async () => {
    const response = await api.get('/api/analytics-hr/snapshot');
    return response.data;
  },
  fetchEngagement: async () => {
    const response = await api.get('/api/analytics-hr/engagement');
    return response.data;
  },
  fetchAbsenteeism: async () => {
    const response = await api.get('/api/analytics-hr/absenteeism');
    return response.data;
  },
  fetchAlerts: async () => {
    const response = await api.get('/api/alerts/');
    return response.data;
  },
  updateAlertStatus: async (alertId: number, status: string) => {
    const response = await api.put(`/api/alerts/${alertId}`, { status });
    return response.data;
  },
  fetchRisks: async () => {
    const response = await api.get('/api/manager/risks');
    return response.data;
  },
  updateRecommendationStatus: async (recId: number, status: string) => {
    const response = await api.put(`/api/manager/risks/recommendations/${recId}/status`, { status });
    return response.data;
  }
};
