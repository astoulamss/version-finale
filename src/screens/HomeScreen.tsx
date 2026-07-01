
import React, { useState, useEffect } from "react";
import { View, Text, Pressable, ActivityIndicator, ScrollView } from "react-native";
import { Feather } from "@expo/vector-icons";
import { PrimaryButton } from "../components/ui/Button";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge, Chip } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";

import { EmployeeProfile, ViewId, Ui, HrNotification, RecentDocument, FeatherName, LeaveBalanceResponse, DocumentResponse, NotificationResponse } from "../types";
import { isRhRole, isManagerRole } from "../lib/auth";
import { toneColor } from "../theme/utils";

import { DocumentRow, NotificationCard, ProgressBar } from "../components/Shared";
import { fetchMyLeaveBalances, fetchMyDocuments, fetchMyNotifications, fetchManagerKpis, fetchManagerNotifications, fetchMyHistory } from "../services/dashboard.service";

import { setGlobalOffboardingTab } from "./ManagerScreens";

export function HomeScreen({
  onboardingProgress,
  onNavigate,
  onAskAi,
  onStartDocument,
  onSelectDocumentDetails,
  onNotificationClick,
  recentNotifications,
  sessionProfile,
  triggerFeedback,
  ui,
}: {
  onboardingProgress: number;
  onNavigate: (view: ViewId) => void;
  onAskAi: (prompt: string) => void;
  onStartDocument: (template: string) => void;
  onSelectDocumentDetails: (doc: RecentDocument) => void;
  onNotificationClick: (notif: HrNotification) => void;
  recentNotifications: HrNotification[];
  sessionProfile: EmployeeProfile;
  triggerFeedback: (label?: string) => void;
  ui: Ui;
}) {
  const roleId = (sessionProfile as EmployeeProfile & { roleId?: string }).roleId ?? sessionProfile.role;
  const isRh = isRhRole(roleId);
  const isManager = isManagerRole(roleId);
  const { styles, theme } = ui;
  console.log("HomeScreen Render ->", { roleId, isRh, isManager, profile: sessionProfile });

  const [leaveBalances, setLeaveBalances] = useState<LeaveBalanceResponse[]>([]);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [managerKpis, setManagerKpis] = useState<any>(null);
  const [rhKpis, setRhKpis] = useState<any>(null);
  const [rhAlerts, setRhAlerts] = useState<any[]>([]);
  const [rhTickets, setRhTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<string | null>(null);

  const [myLeaves, setMyLeaves] = useState<any[]>([]);
  const [myAbsences, setMyAbsences] = useState<any[]>([]);
  const [recentHistory, setRecentHistory] = useState<any[]>([]);
  const [lateTasksCount, setLateTasksCount] = useState<number>(0);

  const loadData = async () => {
    setLoading(true);
    setErrorState(null);
    try {
        if (isRh) {
          const { fetchRhKpis, fetchRhAlerts, fetchRhTickets } = require('../services/dashboard.service');
          const [kpis, alerts, tickets] = await Promise.all([
            fetchRhKpis(),
            fetchRhAlerts(),
            fetchRhTickets()
          ]);
          setRhKpis(kpis);
          setRhAlerts(alerts);
          setRhTickets(tickets);
        } else if (isManager) {
          const [kpis, notifs] = await Promise.all([
            fetchManagerKpis(),
            fetchManagerNotifications()
          ]);
          setManagerKpis(kpis);
          setNotifications(notifs);
        } else {
          const { fetchMyLeaves } = require('../services/dashboard.service');
          const { onboardingService } = require('../services/onboarding.service');
          const { absencesService } = require('../services/absences.service');
          const [bals, docs, notifs, leaves, plans, absences, history] = await Promise.all([
            fetchMyLeaveBalances(),
            fetchMyDocuments(),
            fetchMyNotifications(),
            fetchMyLeaves(),
            onboardingService.fetchMyPlans().catch(() => []),
            absencesService.fetchMyAbsences().catch(() => []),
            fetchMyHistory().catch(() => [])
          ]);
          setLeaveBalances(bals);
          setDocuments(docs);
          setNotifications(notifs);
          setMyLeaves(leaves);
          setMyAbsences(absences || []);
          setRecentHistory(history || []);
          
          let tasksCount = 0;
          const today = new Date();
          if (plans && plans.length > 0) {
             plans.forEach((plan: any) => {
               if (plan.tasks) {
                 tasksCount += plan.tasks.filter((t: any) => t.status !== "done" && t.due_date && new Date(t.due_date) < today).length;
               }
             });
          }
          setLateTasksCount(tasksCount);
        }
      } catch (e: any) {
        // Logging technique silencieux
        console.warn("Dashboard data load error:", e.response?.status, e.message);
        if (e.response && e.response.status >= 500) {
          setErrorState("Une erreur temporaire est survenue.");
        } else {
          setErrorState("Impossible de charger vos données. Vérifiez votre connexion puis réessayez.");
        }
      } finally {
        setLoading(false);
      }
  };

  useEffect(() => {
    loadData();
  }, [isRh, isManager]);

  if (errorState) {
    return (
      <View style={[styles.stack, { justifyContent: 'center', alignItems: 'center' }]}>
        <Feather name="wifi-off" size={48} color={theme.muted} style={{ marginBottom: 16 }} />
        <Text style={[styles.heroText, { textAlign: 'center', marginBottom: 24 }]}>{errorState}</Text>
        <PrimaryButton icon="refresh-cw" label="Réessayer" onPress={loadData} ui={ui} />
      </View>
    );
  }

  if (isRh) {
    return (
      <View style={styles.stack}>
        {/* EN-TÊTE COMMUN */}
        <View style={{ marginBottom: 8 }}>
          <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>
            Bonjour {sessionProfile.firstName || "Collaborateur"} 👋
          </Text>
          <Text style={styles.mutedText}>{sessionProfile.role || "Employé"} — {sessionProfile.department || "Informatique"}</Text>
        </View>

        <Card tone="info" ui={ui}>
          <View style={styles.rowBetween}>
            <View style={styles.flex1}>
              <Text style={styles.heroTitle}>Dashboard RH</Text>
              <Text style={styles.heroText}>Vue simplifiée : alertes, dossiers et actions à lancer sans surcharge.</Text>
            </View>
            <StatusBadge label="RH" tone="info" ui={ui} />
          </View>
          <View style={[styles.infoGrid, { flexDirection: "row" }]}>
            <Card style={styles.kpiCard} ui={ui}>
              <Text style={styles.progressValue}>{rhKpis?.total_employees ?? "—"}</Text>
              <Text style={styles.mutedText}>collaborateurs</Text>
            </Card>
            <Card style={styles.kpiCard} ui={ui}>
              <Text style={styles.progressValue}>{rhKpis?.active_alerts ?? "—"}</Text>
              <Text style={styles.mutedText}>alertes actives</Text>
            </Card>
          </View>
        </Card>

        <View style={styles.stack}>
          <SectionHeader icon="cpu" title="Demandes Collaborateurs" ui={ui} />
          <Card ui={ui}>
            {(rhTickets ?? []).length === 0 && <Text style={styles.mutedText}>Aucune demande en attente.</Text>}
            {(rhTickets ?? []).slice(0, 3).map((item: any, index: number) => (
              <Pressable key={item.id} onPress={() => triggerFeedback(`Ouverture ticket: ${item.subject}`)} style={({ pressed }) => [styles.documentRow, pressed && { opacity: 0.7 }]}>
                <View style={styles.actionIcon}><Text style={styles.bodyStrong}>{index + 1}</Text></View>
                <View style={styles.flex1}>
                  <View style={styles.rowBetween}>
                    <Text style={styles.bodyStrong}>{item.subject}</Text>
                    <StatusBadge label={item.status} tone={item.status === 'open' ? 'critical' : 'info'} ui={ui} />
                  </View>
                  <Text style={styles.mutedText}>{item.description}</Text>
                </View>
              </Pressable>
            ))}
          </Card>

          <SectionHeader icon="bell" title="Alertes récentes" ui={ui} />
          {rhAlerts?.length === 0 && <Text style={styles.mutedText}>Aucune alerte active.</Text>}
          {(rhAlerts ?? []).slice(0, 3).map((alert: any) => (
            <NotificationCard key={alert?.id} compact notification={{ id: String(alert?.id), title: alert?.alert_type, body: alert?.description || `Alerte sur ${alert?.employee_name}`, category: "Altert" as any, priority: alert?.severity === 'high' ? 'critical' : 'warning', time: new Date(alert?.created_at || Date.now()).toLocaleDateString(), unread: alert?.status !== 'resolved' }} onPress={() => onNavigate('alerts')} onMarkRead={() => triggerFeedback('Alerte consultée')} ui={ui} />
          ))}
        </View>

        <SectionHeader icon="shield" title="Actions RH" ui={ui} />
        <View style={styles.actionGrid}>
          <Pressable onPress={() => onNavigate("hr_team")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="users" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Collaborateurs</Text>
          </Pressable>
          <Pressable onPress={() => onNavigate("alerts")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="alert-triangle" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Alertes</Text>
          </Pressable>
          <Pressable onPress={() => onNavigate("offboarding")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="briefcase" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Workflows</Text>
          </Pressable>
          <Pressable onPress={() => onNavigate("notifications")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="bell" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Notifications</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  if (isManager) {
    return (
      <View style={styles.stack}>
        {/* EN-TÊTE COMMUN */}
        <View style={{ marginBottom: 8 }}>
          <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>
            Bonjour {sessionProfile.firstName || "Collaborateur"} 👋
          </Text>
          <Text style={styles.mutedText}>{sessionProfile.role || "Employé"} — {sessionProfile.department || "Informatique"}</Text>
        </View>

        <Card tone="info" ui={ui}>
          <View style={styles.rowBetween}>
            <View style={styles.flex1}>
              <Text style={styles.heroTitle}>Espace Manager RH</Text>
              <Text style={styles.heroText}>Supervision d'équipe, alertes IA et validations en un seul endroit.</Text>
            </View>
            <StatusBadge label="Manager" tone="info" ui={ui} />
          </View>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 10, marginTop: 12 }}>
            <Card style={{ flex: 1, padding: 12, alignItems: 'center' }} ui={ui}>
              <Text style={[styles.progressValue, { fontSize: 20 }]}>{managerKpis?.team_size ?? "—"}</Text>
              <Text style={[styles.mutedText, { fontSize: 11, textAlign: 'center' }]} numberOfLines={1}>collaborateurs</Text>
            </Card>
            <Card style={{ flex: 1, padding: 12, alignItems: 'center' }} ui={ui}>
              <Text style={[styles.progressValue, { fontSize: 20 }]}>{managerKpis?.absenteeism_rate ?? "—"}%</Text>
              <Text style={[styles.mutedText, { fontSize: 11, textAlign: 'center' }]} numberOfLines={1}>taux d'absentéisme</Text>
            </Card>
            <Card style={{ flex: 1, padding: 12, alignItems: 'center' }} ui={ui}>
              <Text style={[styles.progressValue, { fontSize: 20 }]}>{managerKpis?.active_alerts ?? "—"}</Text>
              <Text style={[styles.mutedText, { fontSize: 11, textAlign: 'center' }]} numberOfLines={1}>alertes & attentes</Text>
            </Card>
          </View>
        </Card>

        <SectionHeader icon="shield" title="Actions manager" ui={ui} />
        <View style={styles.actionGrid}>
          <Pressable onPress={() => onNavigate("team")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="users" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Mon équipe</Text>
          </Pressable>
          <Pressable onPress={() => onNavigate("alerts")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="alert-triangle" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Validations</Text>
          </Pressable>
          <View style={[styles.actionCard, { minHeight: 120, justifyContent: 'space-between' }]}>
            <View style={styles.rowStart}>
              <View style={[styles.actionIcon, { backgroundColor: '#6366f115' }]}>
                <Feather name="briefcase" size={19} color="#6366f1" />
              </View>
              <Text style={styles.actionLabel}>Offboarding</Text>
            </View>
            <View style={{ flexDirection: 'row', gap: 6, width: '100%', marginTop: 8 }}>
              <Pressable 
                onPress={() => {}}
                style={{ flex: 1, backgroundColor: '#6366f115', paddingVertical: 6, borderRadius: 6, alignItems: 'center' }}
              >
                <Text style={{ fontSize: 10, color: '#6366f1', fontWeight: '800' }}>En cours</Text>
              </Pressable>
              <Pressable 
                onPress={() => {}}
                style={{ flex: 1, backgroundColor: theme.surfaceAlt, paddingVertical: 6, borderRadius: 6, alignItems: 'center' }}
              >
                <Text style={{ fontSize: 10, color: theme.muted, fontWeight: '800' }}>Historique</Text>
              </Pressable>
            </View>
          </View>
          <Pressable onPress={() => onNavigate("manager_onboarding")} style={styles.actionCard}>
            <View style={styles.actionIcon}>
              <Feather name="user-plus" size={19} color={theme.sky} />
            </View>
            <Text style={styles.actionLabel}>Intégration</Text>
          </Pressable>
        </View>

        <SectionHeader icon="bell" title="Dernières notifications" ui={ui} />
        {(notifications ?? []).length > 0 ? (
          (notifications ?? []).slice(0, 3).map((notification: any) => (
            <NotificationCard key={notification.id} compact notification={{ id: String(notification.id), title: "Alerte RH", body: notification.message || '', category: "Alertes", priority: "critical", time: new Date(notification.created_at).toLocaleDateString(), unread: !notification.is_read }} onPress={() => onNavigate('notifications')} onMarkRead={() => triggerFeedback("Action notification")} ui={ui} />
          ))
        ) : (
          <Card ui={ui}>
            <Text style={styles.mutedText}>Aucune nouvelle notification.</Text>
          </Card>
        )}
      </View>
    );
  }

  if (loading) {
    return (
      <View style={[styles.stack, { flex: 1, justifyContent: "center", alignItems: "center" }]}>
        <ActivityIndicator size="large" color={theme.sky} />
      </View>
    );
  }

  return (
    <View style={styles.stack}>
      {/* BLOC 1 — HEADER SMART & COMPACT */}
      <View style={{ marginBottom: 16 }}>
        <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>
          Bonjour {sessionProfile.firstName || "Collaborateur"} 👋
        </Text>
        <Text style={styles.mutedText}>{sessionProfile.role || "Employé"} — {sessionProfile.department || "Informatique"}</Text>
      </View>

      {/* BLOC 2 — ACTION PRIORITAIRE DU JOUR */}
      {lateTasksCount > 0 ? (
        <Card tone="critical" ui={ui}>
          <View style={styles.rowStart}>
            <Feather name="alert-circle" size={20} color={theme.rose} />
            <View style={[styles.flex1, { marginLeft: 12 }]}>
              <Text style={styles.bodyStrong}>Étape onboarding en retard</Text>
              <Text style={styles.mutedText}>{lateTasksCount} tâche(s) d'intégration en retard.</Text>
            </View>
          </View>
          <View style={{ marginTop: 12 }}>
            <PrimaryButton icon="arrow-right" label="Continuer" onPress={() => onNavigate("onboarding")} ui={ui} />
          </View>
        </Card>
      ) : (
        <Card tone="info" ui={ui}>
          <View style={styles.rowStart}>
            <Feather name="info" size={20} color={theme.sky} />
            <View style={[styles.flex1, { marginLeft: 12 }]}>
              <Text style={styles.bodyStrong}>Pointage non effectué</Text>
              <Text style={styles.mutedText}>Vous n'avez pas encore pointé aujourd'hui.</Text>
            </View>
          </View>
          <View style={{ marginTop: 12 }}>
            <PrimaryButton icon="clock" label="Pointer maintenant" onPress={() => onNavigate("timesheet")} ui={ui} />
          </View>
        </Card>
      )}

      {/* BLOC 3 — QUICK ACTIONS PREMIUM (GRID 2x3) */}
      <SectionHeader icon="zap" title="Accès rapide" ui={ui} />
      <View style={[styles.actionGrid, { flexWrap: "wrap", justifyContent: "space-between" }]}>
        {[
          { id: "assistant", icon: "message-square", label: "Assistant IA" },
          { id: "leave", icon: "calendar", label: "Congés" },
          { id: "requests", icon: "tag", label: "Mes Demandes" },
        ].map((action, idx) => (
          <Pressable key={idx} onPress={() => onNavigate(action.id as ViewId)} style={[styles.card, { width: "31%", marginBottom: 8, padding: 10, alignItems: "center", minHeight: 'auto', gap: 6 }]}>
            <View style={{ width: 36, height: 36, borderRadius: 10, backgroundColor: theme.sky + '15', justifyContent: 'center', alignItems: 'center' }}>
              <Feather name={action.icon as any} size={18} color={theme.sky} />
            </View>
            <Text style={[styles.actionLabel, { fontSize: 11, textAlign: "center", lineHeight: 14 }]} numberOfLines={1}>{action.label}</Text>
          </Pressable>
        ))}
      </View>

      {/* BLOC 4 — DOCUMENTS RH */}
      <SectionHeader action="Voir tout" icon="file-text" onAction={() => onNavigate("documents")} title="Mes documents RH" ui={ui} />
      {(documents ?? []).length > 0 ? (documents ?? []).slice(0, 3).map((document: any) => (
        <DocumentRow 
           key={document.id} 
           document={{
             id: String(document.id),
             title: document.document_type?.name || "Document RH",
             category: "RH",
             date: new Date(document.created_at).toLocaleDateString(),
             status: "downloadable",
             owner: "RH"
           }} 
           onPress={() => triggerFeedback("Ouverture document")} 
           ui={ui} 
        />
      )) : (
        <Card ui={ui}>
          <Text style={styles.mutedText}>Aucun document récent.</Text>
        </Card>
      )}

      {/* BLOC 5 — MES INDICATEURS (KPIs Phase 2) */}
      <SectionHeader icon="pie-chart" title="Mes indicateurs" ui={ui} />
      <View style={[styles.actionGrid, { flexWrap: "wrap", justifyContent: "space-between" }]}>
        <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
          <Text style={[styles.progressValue, { fontSize: 22 }]} adjustsFontSizeToFit numberOfLines={1}>
            {sessionProfile.tenure}
          </Text>
          <Text style={styles.mutedText}>Ancienneté</Text>
        </Card>
        <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
          <Text style={[styles.progressValue, { fontSize: 24 }]}>2</Text>
          <Text style={styles.mutedText}>Formations dispo.</Text>
        </Card>
        <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
          <Text style={[styles.progressValue, { fontSize: 24 }]}>
            {[...(myLeaves || []), ...(myAbsences || [])].filter((l: any) => l.status === "pending").length}
          </Text>
          <Text style={styles.mutedText}>Demandes en attente</Text>
        </Card>
        <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
          <Text style={[styles.progressValue, { fontSize: 24 }]}>
            {[...(myLeaves || []), ...(myAbsences || [])].filter((l: any) => {
              const todayStr = new Date().toISOString().split('T')[0];
              const startStr = new Date(l.start_date).toISOString().split('T')[0];
              const endStr = new Date(l.end_date).toISOString().split('T')[0];
              // On considère une absence/congé actif s'il n'est pas rejeté/résolu et que nous sommes dans les dates
              const isActiveStatus = l.status === "approved" || l.status === "pending" || l.status === "received";
              return isActiveStatus && startStr <= todayStr && endStr >= todayStr;
            }).length}
          </Text>
          <Text style={styles.mutedText}>Absences actives</Text>
        </Card>
      </View>

      {/* BLOC 6 — ACTIVITÉ RÉCENTE */}
      <SectionHeader action="Historique" icon="activity" onAction={() => onNavigate("operations")} title="Activité récente" ui={ui} />
      <Card ui={ui}>
        <View style={styles.stackSmall}>
          {recentHistory.length === 0 ? (
            <Text style={[styles.mutedText, { padding: 12, textAlign: 'center' }]}>Aucune activité récente.</Text>
          ) : (
            recentHistory.slice(0, 3).map((act, i) => {
              let icon = "activity";
              let tone = theme.muted;
              if (act.record_type === "leave") { icon = "sun"; tone = "#EAB308"; }
              else if (act.record_type === "document") { icon = "file"; tone = "#3B82F6"; }
              else if (act.record_type === "absence") { icon = "clock"; tone = theme.rose; }              const dateStr = new Date(act.created_at).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });

              return (
                <View key={i} style={[styles.rowBetween, { paddingVertical: 8, borderBottomWidth: i < Math.min(recentHistory.length, 3) - 1 ? 1 : 0, borderBottomColor: theme.line }]}>
                  <View style={[styles.rowStart, { flex: 1, marginRight: 16 }]}>
                    <Feather name={icon as any} size={16} color={tone} style={{ marginRight: 12 }} />
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.bodyStrong, { fontSize: 14 }]} numberOfLines={1}>{act.action}</Text>
                      <Text style={[styles.metaText, { fontSize: 11, marginTop: 2 }]} numberOfLines={1}>{act.details}</Text>
                    </View>
                  </View>
                  <Text style={[styles.metaText, { fontSize: 12 }]}>{dateStr}</Text>
                </View>
              );
            })
          )}
        </View>
      </Card>
    </View>
  );
}
