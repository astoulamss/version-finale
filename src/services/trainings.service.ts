import api from './api';

export interface Formation {
  id: number;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  target_department_id: number | null;
  target_department_name?: string | null;
}

export interface CreateFormationPayload {
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  target_department_id?: number | null;
}

export const trainingsService = {
  getAllFormationsRH: async (): Promise<Formation[]> => {
    const res = await api.get('/api/formations/rh/all');
    return res.data;
  },

  createFormation: async (data: CreateFormationPayload): Promise<Formation> => {
    const res = await api.post('/api/formations/', data);
    return res.data;
  },

  updateFormation: async (id: number, data: CreateFormationPayload): Promise<Formation> => {
    const res = await api.put(`/api/formations/${id}`, data);
    return res.data;
  },

  deleteFormation: async (id: number): Promise<void> => {
    await api.delete(`/api/formations/${id}`);
  },

  getParticipants: async (id: number): Promise<any[]> => {
    const res = await api.get(`/api/formations/${id}/participants`);
    return res.data;
  }
};
