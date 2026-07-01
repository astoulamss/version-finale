import api from './api';

export const employeeService = {
  fetchSurveys: async () => {
    const response = await api.get('/api/surveys/');
    return response.data;
  },
  submitSurveyResponse: async (surveyId: string, data: any) => {
    const response = await api.post(`/api/surveys/${surveyId}/responses`, data);
    return response.data;
  },
  
  fetchTickets: async () => {
    const response = await api.get('/api/tickets');
    return response.data;
  },
  createTicket: async (data: any) => {
    const response = await api.post('/api/tickets', data);
    return response.data;
  },

  fetchMyTimesheets: async () => {
    const response = await api.get('/api/timesheets/mine');
    return response.data;
  },
  fetchTodayTimesheet: async () => {
    try {
      const response = await api.get('/api/timesheets/today');
      return response.data;
    } catch (e: any) {
      if (e.response?.status === 404) return null;
      throw e;
    }
  },
  clockIn: async () => {
    const response = await api.post('/api/timesheets/clock-in');
    return response.data;
  },
  clockOut: async () => {
    const response = await api.post('/api/timesheets/clock-out');
    return response.data;
  },

  // --- FORMATIONS ---
  fetchFormations: async () => {
    const response = await api.get('/api/formations/');
    return response.data;
  },
  fetchMyEnrollments: async () => {
    const response = await api.get('/api/formations/my-enrollments');
    return response.data;
  },
  enrollInFormation: async (formationId: number) => {
    const response = await api.post(`/api/formations/${formationId}/enroll`);
    return response.data;
  },
  unenrollFromFormation: async (formationId: number) => {
    const response = await api.delete(`/api/formations/${formationId}/enroll`);
    return response.data;
  }
};
