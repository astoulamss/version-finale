import api from './api';

export const onboardingService = {
  fetchMyPlans: async () => {
    const response = await api.get('/api/onboarding/me');
    return response.data;
  },

  getAllPlans: async () => {
    const response = await api.get('/api/onboarding/');
    return response.data;
  },

  createPlan: async (data: any) => {
    const response = await api.post('/api/onboarding/', data);
    return response.data;
  },

  updatePlan: async (id: number, data: any) => {
    const response = await api.put(`/api/onboarding/${id}`, data);
    return response.data;
  },

  deletePlan: async (id: number) => {
    const response = await api.delete(`/api/onboarding/${id}`);
    return response.data;
  },

  addTask: async (planId: number, data: any) => {
    const response = await api.post(`/api/onboarding/${planId}/tasks`, data);
    return response.data;
  },

  updateTaskStatus: async (taskId: number, status: string) => {
    const response = await api.put(`/api/onboarding/tasks/${taskId}`, { status });
    return response.data;
  },

  deleteTask: async (taskId: number) => {
    const response = await api.delete(`/api/onboarding/tasks/${taskId}`);
    return response.data;
  }
};
