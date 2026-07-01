import api from './api';

export const leavesService = {
  fetchMyLeaves: async () => {
    const response = await api.get('/api/leaves/my-leaves');
    return response.data;
  },

  fetchMyBalances: async () => {
    const response = await api.get('/api/leaves/balances/me');
    return response.data;
  },

  fetchLeaveTypes: async () => {
    const response = await api.get('/api/leaves/types');
    return response.data;
  },


  fetchAllLeaves: async () => {
    const response = await api.get('/api/leaves/');
    return response.data;
  },

  fetchTeamLeaves: async () => {
    const response = await api.get('/api/leaves/team');
    return response.data;
  },

  fetchAllBalances: async () => {
    const response = await api.get('/api/leaves/balances');
    return response.data;
  },

  submitLeave: async (data: any) => {
    const response = await api.post('/api/leaves/', data);
    return response.data;
  },

  updateLeaveStatus: async (leaveId: number, status: string) => {
    const response = await api.put(`/api/leaves/${leaveId}`, { status });
    return response.data;
  },

  deleteLeave: async (leaveId: number) => {
    const response = await api.delete(`/api/leaves/${leaveId}`);
    return response.data;
  },

  editLeave: async (leaveId: number, data: any) => {
    const response = await api.patch(`/api/leaves/${leaveId}`, data);
    return response.data;
  }
};
