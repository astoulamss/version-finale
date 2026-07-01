import api from './api';

export const managerService = {
  fetchOffboardingPlans: async () => {
    const response = await api.get('/api/offboarding/');
    return response.data;
  },
  toggleTask: async (taskId: string, currentStatus: string) => {
    const newStatus = currentStatus === "completed" ? "pending" : "completed";
    const response = await api.put(`/api/offboarding/tasks/${taskId}`, { status: newStatus });
    return response.data;
  },
  createOffboardingPlan: async (employeeId: number, departureDate: string, departureReason: string) => {
    const response = await api.post('/api/offboarding/', {
      employee_id: employeeId,
      departure_date: departureDate,
      departure_reason: departureReason
    });
    return response.data;
  },
  
  // Tasks endpoints
  fetchTasksStats: async () => {
    const response = await api.get('/api/manager/tasks/stats/summary');
    return response.data;
  },
  
  // Leaves endpoints
  fetchLeaveHistory: async () => {
    const response = await api.get('/api/history/?record_type=leave');
    return response.data;
  },
  
  // Absences endpoints
  fetchAbsenceHistory: async () => {
    const response = await api.get('/api/history/?record_type=absence');
    return response.data;
  },
  
  // Team endpoints
  fetchTeamMembers: async () => {
    const response = await api.get('/api/employees/');
    return response.data;
  },
  fetchTasks: async (status?: string, assignedTo?: number, overdue?: boolean) => {
    const params = new URLSearchParams();
    if (status && status !== 'all') params.append('status', status);
    if (assignedTo) params.append('assigned_to', assignedTo.toString());
    if (overdue) params.append('overdue', 'true');
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await api.get(`/api/manager/tasks/${queryString}`);
    return response.data;
  },
  createTask: async (taskData: any) => {
    const response = await api.post('/api/manager/tasks/', taskData);
    return response.data;
  },
  updateTask: async (taskId: number, updateData: any) => {
    const response = await api.put(`/api/manager/tasks/${taskId}`, updateData);
    return response.data;
  },
  deleteTask: async (taskId: number) => {
    const response = await api.delete(`/api/manager/tasks/${taskId}`);
    return response.data;
  }
};

export const fetchEmployeeDetail = async (id: number): Promise<any> => {
  // /api/employees/{id}/manager-view n'existe pas côté backend : on compose la
  // fiche employé (/api/employees/{id}) avec son score de risque d'équipe
  // (/api/manager/risks), au format plat attendu par ManagerEmployeeDetailScreen.
  const [employeeRes, risksRes] = await Promise.all([
    api.get(`/api/employees/${id}`),
    api.get('/api/manager/risks'),
  ]);

  const employee = employeeRes.data;
  const risk = (risksRes.data || []).find((r: any) => r.employee_id === id);

  return {
    ...employee,
    prenom: employee.user?.prenom,
    nom: employee.user?.nom,
    position: employee.position?.title ?? 'Non renseigné',
    department: employee.department?.name ?? 'Non renseigné',
    turnover_risk: risk?.turnover_risk ?? null,
    burnout_risk: risk?.burnout_risk ?? null,
    engagement_score: risk?.engagement_risk ?? null,
  };
};

export const fetchTeamOnboarding = async (): Promise<any[]> => {
  const response = await api.get('/api/onboarding/');
  return response.data;
};
