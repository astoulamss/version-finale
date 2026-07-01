import api from './api';

export const offboardingService = {
  fetchMyPlans: async () => {
    const response = await api.get('/api/offboarding/me');
    return response.data;
  },

  updateTaskStatus: async (taskId: number, status: string) => {
    const response = await api.put(`/api/offboarding/tasks/${taskId}`, { status });
    return response.data;
  }
};
