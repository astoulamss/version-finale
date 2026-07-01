import api from './api';
import { LeaveBalanceResponse, DocumentResponse, NotificationResponse } from '../types';

/**
 * Fetch the leave balances for the currently logged in user
 */
export const fetchMyLeaveBalances = async (): Promise<LeaveBalanceResponse[]> => {
  const response = await api.get<LeaveBalanceResponse[]>('/api/leaves/balances/me');
  return response.data;
};

/**
 * Fetch the documents belonging to the currently logged in user
 */
export const fetchMyDocuments = async (): Promise<DocumentResponse[]> => {
  const response = await api.get<DocumentResponse[]>('/api/documents/my-documents');
  return response.data;
};

/**
 * Fetch the notifications for the currently logged in user
 */
export const fetchMyNotifications = async (): Promise<NotificationResponse[]> => {
  const response = await api.get<NotificationResponse[]>('/api/notifications/');
  return response.data;
};

/**
 * Fetch the leaves for the currently logged in user
 */
export const fetchMyLeaves = async (): Promise<any[]> => {
  const response = await api.get('/api/leaves/my-leaves');
  return response.data;
};

/**
 * Fetch recent history for the currently logged in user
 */
export const fetchMyHistory = async (): Promise<any[]> => {
  const response = await api.get('/api/history/');
  return response.data;
};

/**
 * Fetch the employee profile for the currently logged in user
 */
export const fetchMyEmployeeProfile = async (): Promise<any> => {
  const response = await api.get('/api/employees/me');
  return response.data;
};

/**
 * Fetch the team members (or all employees for RH)
 */
export const fetchTeamMembers = async (): Promise<any[]> => {
  const response = await api.get('/api/employees/');
  return response.data;
};

/**
 * Fetch the team absences/leaves
 */
export const fetchTeamAbsences = async (isRhRole: boolean): Promise<any[]> => {
  const endpoint = isRhRole ? '/api/leaves/' : '/api/leaves/team';
  const response = await api.get(endpoint);
  return response.data;
};

/**
 * Fetch Manager KPIs
 */
export const fetchManagerKpis = async (): Promise<any> => {
  const response = await api.get('/api/dashboard/manager/cockpit');
  const data = response.data;
  if (data && data.kpis) {
    return {
      team_size: data.kpis.effectif_total,
      absenteeism_rate: parseFloat(data.kpis.absence_rate.replace('%', '')) || 0,
      active_alerts: data.kpis.active_alerts_total
    };
  }
  return {
    team_size: 0,
    absenteeism_rate: 0,
    active_alerts: 0
  };
};

/**
 * Fetch Manager Notifications
 */
export const fetchManagerNotifications = async (): Promise<any[]> => {
  try {
    const response = await api.get('/api/notifications/');
    return response.data;
  } catch (e) {
    return [];
  }
};

/**
 * Fetch RH KPIs
 */
export const fetchRhKpis = async (): Promise<any> => {
  try {
    const response = await api.get('/api/dashboard/stats');
    return {
      total_employees: response.data.total_employees || 0,
      active_alerts: response.data.leaves_pending || 0
    };
  } catch (e) {
    return { total_employees: 0, active_alerts: 0 };
  }
};

/**
 * Fetch RH Alerts
 */
export const fetchRhAlerts = async (): Promise<any[]> => {
  try {
    const response = await api.get('/api/alerts/');
    return response.data;
  } catch (e) {
    return [];
  }
};

/**
 * Fetch RH Tickets (Priority actions)
 */
export const fetchRhTickets = async (): Promise<any[]> => {
  try {
    const response = await api.get('/api/tickets/');
    return response.data;
  } catch (e) {
    return [];
  }
};

/**
 * Mark a single notification as read
 */
export const markNotificationRead = async (id: string): Promise<any> => {
  const response = await api.put(`/api/notifications/${id}/read`);
  return response.data;
};

/**
 * Mark all notifications as read
 */
export const markAllNotificationsRead = async (): Promise<any> => {
  const response = await api.put('/api/notifications/read-all');
  return response.data;
};

/**
 * Register an Expo push token with the backend (called at login/app start)
 */
export const registerExpoPushToken = async (token: string, platform?: string): Promise<void> => {
  await api.post('/api/notifications/register-device', { token, platform });
};

/**
 * Unregister an Expo push token from the backend (called at logout)
 */
export const unregisterExpoPushToken = async (token: string): Promise<void> => {
  await api.delete('/api/notifications/unregister-device', { data: { token } });
};

/**
 * Fetch unread notification count for badge
 */
export const fetchUnreadNotificationCount = async (): Promise<number> => {
  try {
    const response = await api.get<{ unread_count: number }>('/api/notifications/unread-count');
    return response.data.unread_count || 0;
  } catch {
    return 0;
  }
};
