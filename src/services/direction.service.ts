import api from './api';

export const directionService = {
  fetchDashboard: async () => {
    const response = await api.get('/api/dashboard/direction');
    return response.data;
  },
  
  fetchSnapshot: async () => {
    const response = await api.get('/api/analytics-hr/snapshot');
    return response.data;
  },

  fetchTurnover: async () => {
    const response = await api.get('/api/analytics-hr/turnover-evolution');
    return response.data;
  },

  fetchEngagement: async () => {
    const response = await api.get('/api/analytics-hr/engagement');
    return response.data;
  },

  fetchAbsenteeism: async () => {
    const response = await api.get('/api/analytics-hr/absenteeism');
    return response.data;
  }
};
