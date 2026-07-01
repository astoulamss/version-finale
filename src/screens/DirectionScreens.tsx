

import React, { useState, useEffect } from "react";
import { View, Text, ScrollView } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { Chip, StatusBadge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { Ui, ViewId } from "../types";
import { directionService } from "../services/direction.service";

function UnauthorizedScreen({ ui }: { ui: Ui }) {
  return (
    <View style={[ui.styles.stack, { flex: 1, justifyContent: 'center', alignItems: 'center' }]}>
      <Feather name="shield-off" size={48} color={ui.theme.rose} style={{ marginBottom: 16 }} />
      <Text style={ui.styles.heroTitle}>Accès Refusé</Text>
      <Text style={ui.styles.bodyText}>Vous n'avez pas les droits de Direction.</Text>
    </View>
  );
}

export function DirectionDashboardScreen({ onNavigate, ui, sessionProfile, triggerFeedback }: { onNavigate: (v: ViewId) => void; ui: Ui; sessionProfile?: any; triggerFeedback?: (msg?: string) => void }) {
  const { styles, theme } = ui;
  const isAuth = (sessionProfile?.roleId ?? sessionProfile?.role) === 'direction';
  const [snapshot, setSnapshot] = useState<any>(null);
  const [turnover, setTurnover] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [snapData, turnData, engData, absData] = await Promise.all([
          directionService.fetchSnapshot().catch(() => null),
          directionService.fetchTurnover().catch(() => null),
          directionService.fetchEngagement().catch(() => null),
          directionService.fetchAbsenteeism().catch(() => null)
        ]);
        
        // Merge stats with calculated absenteeism rate based on total headcount
        const totalEmployees = snapData?.total_employees || 1;
        const totalAbsentHours = absData?.total_hours || 0;
        const estAbsenteeismRate = Math.min(100, Math.round((totalAbsentHours / (totalEmployees * 151.67)) * 100 * 10) / 10);

        const mergedSnap = {
          ...snapData,
          avg_engagement_score: engData?.average_score || 0,
          avg_absenteeism_rate: estAbsenteeismRate,
          total_departments: snapData?.turnover_by_department ? Object.keys(snapData.turnover_by_department).length : 0
        };
        
        setSnapshot(mergedSnap);
        setTurnover(turnData);
      } catch (err: any) {
        setError(err.message || "Erreur de chargement");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  return (
    <View style={styles.stack}>
      <View style={[styles.sectionHeader, { marginTop: 0 }]}>
        <Text style={styles.screenTitle}>Pilotage Stratégique</Text>
        <View style={styles.chipWrap}>
          <Chip label="Ce mois" active ui={ui} />
        </View>
      </View>

      {loading && (
        <Card ui={ui}>
          <Text style={styles.bodyText}>Chargement des indicateurs...</Text>
        </Card>
      )}

      {error && (
        <Card tone="critical" ui={ui}>
          <Text style={styles.bodyStrong}>Erreur: {error}</Text>
        </Card>
      )}

      {!loading && !error && snapshot && (
        <>
          <SectionHeader icon="activity" title="Vue d'ensemble" ui={ui} />
          <View style={styles.statGrid}>
            <View style={{ width: "48%", marginBottom: 12 }}>
              <Card ui={ui}>
                <Text style={styles.mutedText}>Employés Actifs</Text>
                <Text style={[styles.statValue, { fontSize: 24, marginTop: 4 }]}>{snapshot.total_employees}</Text>
              </Card>
            </View>
            <View style={{ width: "48%", marginBottom: 12 }}>
              <Card ui={ui}>
                <Text style={styles.mutedText}>Départements</Text>
                <Text style={[styles.statValue, { fontSize: 24, marginTop: 4 }]}>{snapshot.total_departments}</Text>
              </Card>
            </View>
            <View style={{ width: "48%", marginBottom: 12 }}>
              <Card ui={ui}>
                <Text style={styles.mutedText}>Score Engagement</Text>
                <Text style={[styles.statValue, { fontSize: 24, marginTop: 4, color: theme.emerald }]}>{snapshot.avg_engagement_score}%</Text>
              </Card>
            </View>
            <View style={{ width: "48%", marginBottom: 12 }}>
              <Card ui={ui}>
                <Text style={styles.mutedText}>Absentéisme</Text>
                <Text style={[styles.statValue, { fontSize: 24, marginTop: 4, color: theme.amber }]}>{snapshot.avg_absenteeism_rate}%</Text>
              </Card>
            </View>
          </View>
        </>
      )}

      {!loading && !error && turnover && (
        <>
          <SectionHeader icon="trending-down" title="Prévisions Turnover (IA)" ui={ui} />
          <AICard ui={ui}>
            <Text style={styles.cardTitle}>Risque de départ</Text>
            <View style={[styles.rowStart, { marginTop: 12, marginBottom: 16 }]}>
              <View style={[styles.profileAvatar, { width: 48, height: 48, backgroundColor: theme.amberSoft, marginRight: 16 }]}>
                <Feather name="alert-triangle" size={20} color={theme.amber} />
              </View>
              <View>
                <Text style={[styles.statValue, { fontSize: 28, color: theme.amber }]}>{turnover.global_turnover_rate}%</Text>
                <Text style={styles.mutedText}>Prévision sur les 6 prochains mois</Text>
              </View>
            </View>
            <Text style={styles.bodyStrong}>Facteurs de risque principaux :</Text>
            {(turnover.risk_factors ?? []).map((factor: string, idx: number) => (
              <View key={idx} style={[styles.rowStart, { marginTop: 6 }]}>
                <Feather name="chevron-right" size={14} color={theme.muted} style={{ marginRight: 6 }} />
                <Text style={styles.bodyText}>{factor}</Text>
              </View>
            ))}
          </AICard>
        </>
      )}
    </View>
  );
}
