import api from './api';

export const myTasksService = {
  fetchMyTasks: async (status?: string, overdue?: boolean) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (overdue) params.append('overdue', 'true');
    const response = await api.get(`/api/my/tasks/?${params.toString()}`);
    return response.data;
  },

  fetchMyTasksStats: async () => {
    const response = await api.get('/api/my/tasks/stats');
    return response.data;
  },

  updateTaskStatus: async (taskId: number, status: string) => {
    const response = await api.patch(`/api/my/tasks/${taskId}/status`, { status });
    return response.data;
  }
};
