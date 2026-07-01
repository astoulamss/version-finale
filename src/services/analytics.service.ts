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

const GENDER_COLORS: Record<string, string> = {
  'Homme': '#0EA5E9',
  'Femme': '#F43F5E',
  'Autre/Non renseigné': '#94A3B8',
};

export const analyticsService = {
  // Le backend n'expose pas d'endpoint agrégé unique : on compose la réponse
  // à partir des endpoints /snapshot, /payroll, /absenteeism, /engagement,
  // /satisfaction et /dashboard/stats qui existent réellement.
  fetchDashboard: async (): Promise<DashboardAnalyticsResponse> => {
    const [snapshot, payroll, absenteeism, engagement, satisfaction, stats] = await Promise.all([
      api.get('/api/analytics-hr/snapshot'),
      api.get('/api/analytics-hr/payroll'),
      api.get('/api/analytics-hr/absenteeism'),
      api.get('/api/analytics-hr/engagement'),
      api.get('/api/analytics-hr/satisfaction'),
      api.get('/api/dashboard/stats'),
    ]);

    const genderDistribution: Record<string, number> = snapshot.data.gender_distribution || {};
    const payrollByDepartment: Record<string, number> = payroll.data.by_department || {};

    return {
      turnover_rate: snapshot.data.turnover_rate,
      payroll_total: payroll.data.total_payroll,
      payroll_avg: payroll.data.avg_salary,
      absence_hours: absenteeism.data.total_hours,
      absence_rate: absenteeism.data.rate ?? 0,
      engagement_score: engagement.data.average_score,
      satisfaction_rate: satisfaction.data.average_score,
      total_responses_satisfaction: satisfaction.data.total_responses,
      registered_contracts: stats.data.total_contracts,
      pending_leaves: stats.data.leaves_pending,
      generated_documents: stats.data.total_documents,
      demographics: {
        total_active: snapshot.data.active_employees,
        average_age: snapshot.data.average_age ?? 0,
        gender_distribution: Object.entries(genderDistribution).map(([label, count]) => ({
          label,
          count,
          color: GENDER_COLORS[label] ?? '#94A3B8',
        })),
      },
      payroll_by_department: Object.entries(payrollByDepartment).map(([department, amount]) => ({
        department,
        amount,
      })),
    };
  }
};
