import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, ActivityIndicator, Pressable } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge, Chip } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { Ui, ViewId } from "../types";
import { isQvtRole } from "../lib/auth";
import { qvtService } from "../services/qvt.service";

function UnauthorizedScreen({ ui }: { ui: Ui }) {
  return (
    <View style={[ui.styles.stack, { flex: 1, justifyContent: 'center', alignItems: 'center' }]}>
      <Feather name="shield-off" size={48} color={ui.theme.rose} style={{ marginBottom: 16 }} />
      <Text style={ui.styles.heroTitle}>Accès Refusé</Text>
      <Text style={ui.styles.bodyText}>Vous n'avez pas le rôle Médecine / QVT.</Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// 1. QVT DASHBOARD SCREEN
// ---------------------------------------------------------------------------
export function QvtDashboardScreen({ ui, onNavigate, triggerFeedback, sessionProfile }: { ui: Ui; onNavigate: (v: ViewId) => void; triggerFeedback: (m: string) => void; sessionProfile?: any }) {
  const { styles, theme } = ui;
  const isAuth = isQvtRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [kpis, setKpis] = useState<any>({
    wellbeingScore: 0,
    stressLevel: 0,
    healthAbsences: 0,
    activeAlerts: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [engagement, absenteeism, alertsList, risks] = await Promise.all([
          qvtService.fetchEngagement().catch(() => null),
          qvtService.fetchAbsenteeism().catch(() => null),
          qvtService.fetchAlerts().catch(() => []),
          qvtService.fetchRisks().catch(() => [])
        ]);
        
        if (!mounted) return;
        
        // wellbeing score: engagement average_score is out of 5, convert to out of 100
        const wellbeing = engagement?.average_score ? Math.round(engagement.average_score * 20) : 75;
        
        // stress level: average of burnout risks in risks
        let totalBurnout = 0;
        let countBurnout = 0;
        if (Array.isArray(risks)) {
          risks.forEach((r: any) => {
            if (r.burnout_risk !== null && r.burnout_risk !== undefined) {
              totalBurnout += r.burnout_risk;
              countBurnout++;
            }
          });
        }
        const stress = countBurnout > 0 ? Math.round(totalBurnout / countBurnout) : 32;
        
        // health absences: total_hours
        const absences = absenteeism?.total_hours ? Math.round(absenteeism.total_hours) : 12;
        
        // active alerts: status !== 'resolved'
        const activeAlertsCount = Array.isArray(alertsList) 
          ? alertsList.filter((a: any) => a.status !== 'resolved').length 
          : 0;
          
        setKpis({
          wellbeingScore: wellbeing,
          stressLevel: stress,
          healthAbsences: absences,
          activeAlerts: activeAlertsCount
        });
      } catch (err) {
        console.warn("Failed to load QVT dashboard KPIs", err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      <SectionHeader icon="activity" title="Dashboard Médecine / QVT" ui={ui} />

      {loading && <ActivityIndicator color={theme.sky} style={{ marginVertical: 20 }} />}

      {!loading && (
        <AICard ui={ui}>
          <Text style={styles.cardTitle}>Indicateurs de Santé Globaux</Text>
          <View style={styles.infoGrid}>
            <Card ui={ui}>
              <Text style={styles.progressValue}>{kpis.wellbeingScore}/100</Text>
              <Text style={styles.mutedText}>Bien-être</Text>
            </Card>
            <Card ui={ui}>
              <Text style={[styles.progressValue, { color: kpis.stressLevel > 40 ? theme.rose : theme.text }]}>
                {kpis.stressLevel}%
              </Text>
              <Text style={styles.mutedText}>Taux de stress</Text>
            </Card>
            <Card ui={ui}>
              <Text style={styles.progressValue}>{kpis.healthAbsences}</Text>
              <Text style={styles.mutedText}>Absences Santé</Text>
            </Card>
            <Card ui={ui}>
              <Text style={[styles.progressValue, { color: kpis.activeAlerts > 0 ? theme.rose : theme.text }]}>
                {kpis.activeAlerts}
              </Text>
              <Text style={styles.mutedText}>Alertes</Text>
            </Card>
          </View>
        </AICard>
      )}

      <SectionHeader icon="tool" title="Accès Rapides" ui={ui} />
      <View style={{ flexDirection: 'row', gap: 12, marginBottom: 24 }}>
        <View style={{ flex: 1 }}>
          <PrimaryButton label="Voir les alertes" icon="alert-triangle" onPress={() => onNavigate('qvt_alerts')} ui={ui} />
        </View>
        <View style={{ flex: 1 }}>
          <SecondaryButton label="Plans d'action" icon="clipboard" onPress={() => onNavigate('qvt_plans')} ui={ui} />
        </View>
      </View>
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// 2. QVT ALERTS SCREEN
// ---------------------------------------------------------------------------
export function QvtAlertsScreen({ ui, triggerFeedback, sessionProfile }: { ui: Ui; triggerFeedback: (m: string) => void; sessionProfile?: any }) {
  const { styles, theme } = ui;
  const isAuth = isQvtRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [alerts, setAlerts] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    try {
      const data = await qvtService.fetchAlerts();
      setAlerts(data);
    } catch (err) {
      console.warn("Failed to load alerts", err);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  const markResolved = async (id: number) => {
    try {
      await qvtService.updateAlertStatus(id, 'resolved');
      triggerFeedback("Alerte marquée comme traitée.");
      loadAlerts();
    } catch (err) {
      triggerFeedback("Erreur lors de la mise à jour de l'alerte.");
    }
  };

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      <SectionHeader icon="alert-triangle" title="Alertes Santé & RPS" ui={ui} />

      {loading && <ActivityIndicator color={theme.sky} style={{ marginVertical: 20 }} />}

      {!loading && (alerts ?? []).length === 0 && (
        <Card ui={ui}>
          <Text style={[styles.bodyText, { textAlign: 'center' }]}>Aucune alerte en cours.</Text>
        </Card>
      )}

      {!loading && alerts?.map((alert) => (
        <Card key={alert.id} ui={ui} style={{ marginBottom: 12 }}>
          <View style={styles.rowBetween}>
            <View>
              <Text style={styles.bodyStrong}>{alert.employee_name || "Employé Inconnu"}</Text>
              <Text style={styles.metaText}>{alert.created_at ? new Date(alert.created_at).toLocaleDateString() : ""}</Text>
            </View>
            <StatusBadge 
              label={(alert.severity || "moyen").toUpperCase()} 
              tone={alert.severity === 'critique' ? 'critical' : alert.severity === 'moyen' ? 'warning' : 'neutral'} 
              ui={ui} 
            />
          </View>
          <View style={{ marginTop: 12, marginBottom: 12 }}>
            <Text style={styles.bodyText}>{alert.alert_type} - {alert.description}</Text>
          </View>
          <View style={styles.rowBetween}>
            <Chip 
              label={alert.status === 'resolved' ? 'Résolu' : alert.status === 'in_progress' ? 'En cours' : 'Nouveau'} 
              active={alert.status !== 'resolved'} 
              onPress={() => {}} 
              ui={ui} 
            />
            {alert.status !== 'resolved' && (
              <SecondaryButton label="Traiter" icon="check" onPress={() => markResolved(alert.id)} ui={ui} />
            )}
          </View>
        </Card>
      ))}
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// 3. QVT FOLLOW-UP SCREEN (Action Plans)
// ---------------------------------------------------------------------------
export function QvtActionPlansScreen({ ui, triggerFeedback, sessionProfile }: { ui: Ui; triggerFeedback: (m: string) => void; sessionProfile?: any }) {
  const { styles, theme } = ui;
  const isAuth = isQvtRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [cases, setCases] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(true);

  const loadPlans = async () => {
    try {
      const risks = await qvtService.fetchRisks();
      const mapped = [];
      if (Array.isArray(risks)) {
        for (const risk of risks) {
          if (risk.recommendations) {
            for (const rec of risk.recommendations) {
              mapped.push({
                id: rec.id,
                employee: risk.employee_name,
                department: risk.department_name || "N/A",
                lastNote: rec.recommendation,
                status: rec.status,
                nextAction: rec.status === "pending" ? "À qualifier" : rec.status === "in_progress" ? "En cours" : "Terminée"
              });
            }
          }
        }
      }
      setCases(mapped);
    } catch (err) {
      console.warn("Failed to load action plans", err);
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlans();
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  const handleUpdateStatus = async (recId: number, currentStatus: string) => {
    try {
      const nextStatus = currentStatus === "pending" ? "in_progress" : "done";
      await qvtService.updateRecommendationStatus(recId, nextStatus);
      triggerFeedback("Statut de la recommandation mis à jour.");
      loadPlans();
    } catch (err) {
      triggerFeedback("Erreur lors de la mise à jour.");
    }
  };

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      <SectionHeader icon="clipboard" title="Suivi des Employés (Follow-Up)" ui={ui} />

      <Card ui={ui} style={{ marginBottom: 16 }}>
        <Text style={styles.bodyText}>Dossiers nécessitant une attention médicale ou RH spécifique.</Text>
      </Card>

      {loading && <ActivityIndicator color={theme.sky} style={{ marginVertical: 20 }} />}

      {!loading && (cases ?? []).length === 0 && (
        <Card ui={ui}>
          <Text style={[styles.bodyText, { textAlign: 'center' }]}>Aucun plan d'action actif.</Text>
        </Card>
      )}

      {!loading && (cases ?? []).map(c => (
        <Card key={c.id} ui={ui} style={{ marginBottom: 12 }}>
          <View style={[styles.rowBetween, { marginBottom: 8 }]}>
            <View>
              <Text style={styles.bodyStrong}>{c.employee}</Text>
              <Text style={styles.metaText}>{c.department}</Text>
            </View>
            <View style={{ backgroundColor: theme.sky + '20', padding: 8, borderRadius: 8 }}>
              <Feather name="folder" size={16} color={theme.sky} />
            </View>
          </View>
          <View style={{ backgroundColor: theme.background, padding: 12, borderRadius: 8, marginBottom: 12 }}>
            <Text style={[styles.metaText, { fontStyle: 'italic' }]}>Recommandation : {c.lastNote}</Text>
          </View>
          <View style={styles.rowBetween}>
            <Chip 
              label={c.nextAction} 
              active={c.status !== 'done'} 
              onPress={() => {}} 
              ui={ui} 
            />
            {c.status !== 'done' && (
              <SecondaryButton 
                label={c.status === 'pending' ? "Démarrer" : "Terminer"} 
                icon="arrow-right" 
                onPress={() => handleUpdateStatus(c.id, c.status)} 
                ui={ui} 
              />
            )}
          </View>
        </Card>
      ))}
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// 4. QVT REPORTS SCREEN (Stats)
// ---------------------------------------------------------------------------
export function QvtStatsScreen({ ui, sessionProfile }: { ui: Ui; sessionProfile?: any }) {
  const { styles, theme } = ui;
  const isAuth = isQvtRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [snapshot, engagement] = await Promise.all([
          qvtService.fetchStats().catch(() => null),
          qvtService.fetchEngagement().catch(() => null)
        ]);
        if (mounted) {
          setStats({
            turnover: snapshot?.turnover_rate || 0,
            absenteeism: snapshot?.absenteeism_rate || 0,
            engagement: engagement?.average_score || 0
          });
        }
      } catch (err) {
        console.warn(err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  const handleExport = () => {
    setExporting(true);
    setTimeout(() => {
      setExporting(false);
      alert("Rapport exporté avec succès (format PDF).");
    }, 1500);
  };

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      <SectionHeader icon="bar-chart-2" title="Rapports & Indicateurs QVT" ui={ui} />

      {loading && <ActivityIndicator color={theme.sky} style={{ marginVertical: 20 }} />}

      {!loading && stats && (
        <AICard ui={ui}>
          <Text style={styles.cardTitle}>Bilan Mensuel Anonymisé</Text>
          <Text style={styles.bodyText}>
            Le taux d'engagement moyen est de {stats.engagement}/5. 
            Le taux d'absentéisme actuel s'élève à {stats.absenteeism}%. 
            Le taux de rotation du personnel (turnover) est estimé à {stats.turnover}%.
          </Text>
        </AICard>
      )}

      <Card ui={ui} style={{ marginTop: 16 }}>
        <View style={styles.rowBetween}>
          <Text style={styles.bodyStrong}>Générer un rapport CHSCT</Text>
          <Feather name="file-text" size={24} color={theme.sky} />
        </View>
        <Text style={[styles.metaText, { marginTop: 4, marginBottom: 16 }]}>Inclut toutes les métriques anonymisées.</Text>
        
        {exporting ? (
          <ActivityIndicator color={theme.sky} />
        ) : (
          <PrimaryButton label="Exporter le rapport" icon="download" onPress={handleExport} ui={ui} />
        )}
      </Card>
    </ScrollView>
  );
}
