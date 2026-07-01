import api from './api';

export interface DashboardAnalyticsResponse {
  turnover_rate: number;
  payroll_total: number;
  payroll_avg: number;
  absence_hours: number;
  absence_rate: number;
  engagement_score: number | null;
  satisfaction_rate: number | null;
  total_responses_satisfaction: number;
  registered_contracts: number;
  pending_leaves: number;
  generated_documents: number;
  demographics: {
    total_active: number;
    average_age: number;
    gender_distribution: Array<{ label: string; count: number; color: string }>;
  };
  payroll_by_department: Array<{ department: string; amount: number }>;
}

export const analyticsService = {
  fetchDashboard: async (): Promise<DashboardAnalyticsResponse> => {
    const response = await api.get('/api/analytics-hr/dashboard');
    return response.data;
  }
};
