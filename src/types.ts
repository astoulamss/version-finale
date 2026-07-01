import { Feather } from "@expo/vector-icons";
import { Theme } from "./theme/colors";
import { createStyles } from "./theme/styles";

export type FeatherName = keyof typeof Feather.glyphMap;
export type Ui = {
  theme: Theme;
  styles: ReturnType<typeof createStyles>;
  isDark?: boolean;
  toggleTheme?: () => void;
};

export type AuthStep = "splash" | "login" | "otp" | "first-login" | "forgot-password" | "app";
export type ViewId = "home" | "assistant" | "documents" | "onboarding" | "profile" | "notifications" | "team" | "hr_team" | "alerts" | "offboarding" | "admin_dashboard" | "admin_accounts" | "admin_alerts" | "admin_logs" | "admin_profile" | "admin_users" | "admin_roles" | "admin_settings" | "qvt_dashboard" | "qvt_alerts" | "qvt_plans" | "qvt_stats" | "leave" | "payroll" | "requests" | "mobility" | "surveys" | "tickets" | "timesheet" | "direction_dashboard" | "operations" | "indicateurs" | "validations" | "manager_employee_detail" | "manager_onboarding" | "manager_offboarding" | "manager_alerts" | "manager_hub" | "manager_leaves" | "manager_absences" | "rh_hub" | "absences" | "employee_trainings" | "contract" | "employee_offboarding" | "announcements" | "hr_contracts" | "hr_trainings";

export interface LeaveRequest {
  id: number;
  employee_id: number;
  leave_type_id: number;
  start_date: string;
  end_date: string;
  status: 'pending' | 'approved' | 'rejected';
  reason?: string;
}

export interface TurnoverPrediction {
  employee_id: number;
  risk_level: 'High' | 'Medium' | 'Low';
  factors: string[];
}

export type NavigationItem = {
  id: ViewId;
  label: string;
  icon: string;
};

export type StatusTone = "success" | "warning" | "critical" | "info" | "neutral" | "blocked";

export type EmployeeProfile = {
  firstName: string;
  lastName: string;
  employeeId: string;
  roleId?: string;
  role: string;
  access?: string[];
  department: string;
  manager: string;
  startDate: string;
  tenure: string;
  office: string;
  email: string;
  avatarInitials: string;
  photoUrl?: string;
  phone?: string;
  location?: string;
  hireDate?: string;
  contractType?: string;
  status?: string;
  position?: string;
};

export type QuickStat = {
  id: string;
  label: string;
  value: string;
  detail: string;
  icon: string;
  tone: StatusTone;
};

export type QuickAction = {
  id: string;
  label: string;
  icon: string;
  target: Exclude<ViewId, "notifications">;
};

export type DocumentStatus = "pending" | "approved" | "rejected" | "correction" | "downloadable";

export type DocumentCategory = {
  id: string;
  title: string;
  description: string;
  icon: string;
  templates: string[];
};

export type RecentDocument = {
  id: string;
  title: string;
  category: string;
  date: string;
  status: DocumentStatus;
  owner: string;
};

export type DocumentDraft = {
  template: string;
  fields: Array<{
    label: string;
    value: string;
    editable: boolean;
  }>;
  warnings: string[];
};

export type TimelineStep = {
  id: string;
  label: string;
  detail: string;
  status: "done" | "active" | "blocked" | "todo";
};

export interface OffboardingPlan {
  id: number;
  user_id: number;
  departure_date: string;
  reason: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  notes?: string;
  created_at: string;
}

export interface Contract {
  id: number;
  user_id: number;
  contract_type: string;
  start_date: string;
  end_date?: string;
  position: string;
  salary?: string;
  created_at: string;
}

export type OnboardingTask = {
  id: string;
  title: string;
  description: string;
  deadline: string;
  status: "done" | "active" | "late" | "todo";
  resources: string[];
  contacts: string[];
  documents: string[];
};

export type OnboardingWeek = {
  id: string;
  title: string;
  theme: string;
  progress: number;
  tasks: OnboardingTask[];
};

export type HrNotification = {
  id: string;
  title: string;
  body: string;
  category: "RH" | "Onboarding" | "Documents" | "Validation" | "Paie" | "Rappels" | "Sécurité" | "Système" | "Comptes" | "Santé" | "Prévention" | "Alertes" | "Équipe";
  priority: StatusTone;
  time: string;
  unread: boolean;
};

export type TeamMember = {
  name: string;
  role: string;
  status: string;
  detail: string;
  department?: string;
  avatarInitials?: string;
  engagement?: number;
  absences?: string;
  risk?: string;
};

export type RhCollaborator = {
  id: string;
  name: string;
  role: string;
  department: string;
  status: string;
  risk: "Faible" | "Moyen" | "Élevé";
  engagement: number;
  absences: string;
  avatarInitials: string;
};

export type RhPriorityAction = {
  id: string;
  rank: string;
  name: string;
  severity: "Critique" | "Attention" | "Vigilance";
  summary: string;
  actionLabel: string;
};

export type RhAlertItem = {
  id: string;
  name: string;
  department: string;
  summary: string;
  tone: StatusTone;
  time: string;
};

export type AiReplyKind = "answer" | "clarification" | "permission-denied" | "escalation" | "error";

export type AiReply = {
  kind: AiReplyKind;
  title: string;
  text: string;
  source?: string;
  actions: string[];
  options?: string[];
};

export type ChatMessage = {
  id: string;
  role: "employee" | "ai" | "system";
  text: string;
  time: string;
  reply?: AiReply;
};

export type AiPermission = {
  label: string;
  detail: string;
  allowed: boolean;
};

export type SecurityAlert = {
  id: string;
  user: string;
  type: string;
  summary: string;
  tone: StatusTone;
  time: string;
  status: string;
};

export type UserAccount = {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "actif" | "inactif" | "suspendu" | "bloqué";
  mfa: boolean;
  lastLogin: string;
  tempAccess?: string;
};

export type AdminLog = {
  id: string;
  action: string;
  description: string;
  user: string;
  time: string;
  tone: StatusTone;
};

export type QvtAlert = {
  id: string;
  name: string;
  department: string;
  type: string;
  riskScore: number;
  severity: "Vigilance" | "Attention" | "Critique" | "Urgence";
  date: string;
  status: "Nouvelle" | "En cours" | "Clôturée";
};

export type QvtActionPlan = {
  id: string;
  name: string;
  type: string;
  owner: string;
  deadline: string;
  progress: number;
  privacy: "QVT uniquement" | "RH + QVT" | "RH + Manager + QVT";
  status: "À faire" | "En cours" | "En attente" | "Terminé";
};

export type QvtKpi = {
  id: string;
  label: string;
  value: string;
  trend: string;
  trendUpIsGood: boolean;
  tone: StatusTone;
};

export type LeaveBalanceResponse = {
  id: number;
  employee_id: number;
  leave_type_id: number;
  remaining_days: number;
  leave_type_name?: string;
};

export type DocumentResponse = {
  id: number;
  employee_id: number;
  document_type_id: number;
  file_url: string;
  created_at: string;
  document_type?: {
    id: number;
    name: string;
  };
};

export type NotificationResponse = {
  id: number;
  user_id: number;
  message: string;
  is_read: boolean;
  created_at: string;
};

