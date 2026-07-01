import api from './api';

export const absencesService = {
  fetchMyAbsences: async () => {
    // Calling the endpoint from the new ydays backend
    const response = await api.get('/api/absences/');
    return response.data.absences;
  },

  fetchTeamAbsences: async (is_archived: boolean = false) => {
    // Exact same endpoint, but clearly named for managers
    const response = await api.get(`/api/absences/?is_archived=${is_archived}`);
    return response.data.absences;
  },

  declareAbsence: async (data: { employee_id: number; start_date: string; end_date: string; reason: string; absence_type: string }) => {
    const response = await api.post('/api/absences/', data);
    return response.data;
  },

  updateAbsence: async (id: number, data: Partial<{ start_date: string; end_date: string; reason: string; absence_type: string; status: string; is_archived: boolean }>) => {
    const response = await api.put(`/api/absences/${id}`, data);
    return response.data;
  },

  deleteAbsence: async (id: number) => {
    const response = await api.put(`/api/absences/${id}`, { is_archived: true });
    return response.data;
  }
};
