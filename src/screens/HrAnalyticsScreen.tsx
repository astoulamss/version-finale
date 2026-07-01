import React, { useState, useEffect } from 'react';

import { View, Text, ScrollView, ActivityIndicator, Pressable } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Ui, EmployeeProfile } from '../types';
import { Card, AICard } from '../components/ui/Card';
import { DonutChart } from '../components/ui/DonutChart';

import { PrimaryButton } from '../components/ui/Button';
import { analyticsService, DashboardAnalyticsResponse } from '../services/analytics.service';
import { isRhRole } from '../lib/auth';

export function HrAnalyticsScreen({ ui, sessionProfile }: { ui: Ui, sessionProfile: EmployeeProfile }) {
  const { styles, theme } = ui;
  const isRh = isRhRole(sessionProfile.roleId ?? sessionProfile.role);

  const [data, setData] = useState<DashboardAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const res = await analyticsService.fetchDashboard();
      setData(res);
    } catch (error) {
      console.error("Erreur lors de la récupération des statistiques", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isRh) {
      fetchDashboardData();
    }
  }, [isRh]);

  if (!isRh) {
    return (
      <View style={styles.stack}>
        <Text style={styles.bodyText}>Accès non autorisé à l'Analytics RH.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>

      {/* HEADER SECTION */}
      <View style={[styles.rowBetween, { marginBottom: 24 }]}>
        <View>
          <Text style={styles.mutedText}>Voici un aperçu stratégique des indicateurs de l'entreprise.</Text>
        </View>
        <PrimaryButton
          icon="refresh-cw"
          label={loading ? "Actualisation..." : "Rafraîchir"}
          onPress={fetchDashboardData}
          disabled={loading}
          ui={ui}
        />
      </View>

      {loading && !data ? (
        <View style={{ padding: 40, alignItems: 'center' }}>
          <ActivityIndicator size="large" color={theme.sky} />
          <Text style={[styles.mutedText, { marginTop: 16 }]}>Calcul des statistiques en cours...</Text>
        </View>
      ) : data ? (
        <>

          <Text style={[styles.bodyStrong, { fontSize: 18, marginBottom: 16, marginTop: 8 }]}>Indicateurs Clés de Performance</Text>

          <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 16, marginBottom: 32 }}>

            {/* 1. Turnover Global */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.rose + '20' }}>
                  <Feather name="user-minus" size={20} color={theme.rose} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Turnover Global</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy, marginBottom: 4 }}>
                {data.turnover_rate}%
              </Text>
              <View style={{ width: '100%', height: 4, backgroundColor: theme.line, borderRadius: 2, marginTop: 8 }}>
                <View style={{ width: `${Math.min(data.turnover_rate, 100)}%`, height: 4, backgroundColor: theme.rose, borderRadius: 2 }} />
              </View>
            </Card>

            {/* 2. Masse Salariale */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.emerald + '20' }}>
                  <Feather name="dollar-sign" size={20} color={theme.emerald} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Masse Salariale</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy, marginBottom: 4 }}>
                {data.payroll_total.toLocaleString('fr-FR')} €
              </Text>
              <Text style={styles.metaText}>Moyenne: {data.payroll_avg.toLocaleString('fr-FR')} €</Text>
            </Card>

            {/* 3. Heures d'absence */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.amber + '20' }}>
                  <Feather name="clock" size={20} color={theme.amber} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Heures d'absence</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy, marginBottom: 4 }}>
                {data.absence_hours}h
              </Text>
              <Text style={styles.metaText}>Taux d'absentéisme : {data.absence_rate}%</Text>
            </Card>

            {/* 4. Score d'Engagement */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.sky + '20' }}>
                  <Feather name="star" size={20} color={theme.sky} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Score d'Engagement</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy, marginBottom: 4 }}>
                {data.engagement_score !== null ? `${data.engagement_score}%` : "N/A"}
              </Text>
              {data.engagement_score !== null && (
                <View style={{ width: '100%', height: 4, backgroundColor: theme.line, borderRadius: 2, marginTop: 8 }}>
                  <View style={{ width: `${data.engagement_score}%`, height: 4, backgroundColor: theme.sky, borderRadius: 2 }} />
                </View>
              )}
            </Card>

            {/* 5. Taux de Satisfaction */}
            <AICard ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: 'rgba(99, 102, 241, 0.1)' }}>
                  <Feather name="heart" size={20} color="#6366F1" />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Taux de Satisfaction</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: '#6366F1', marginBottom: 4 }}>
                {data.satisfaction_rate !== null ? `${data.satisfaction_rate}%` : "N/A"}
              </Text>
              <Text style={styles.metaText}>Basé sur {data.total_responses_satisfaction} réponses</Text>
            </AICard>

            {/* 6. Contrats Enregistrés */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.surfaceAlt }}>
                  <Feather name="file-text" size={20} color={theme.navy} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Contrats Enregistrés</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy }}>
                {data.registered_contracts}
              </Text>
            </Card>

            {/* 7. Congés en attente */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.surfaceAlt }}>
                  <Feather name="calendar" size={20} color={theme.navy} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Congés en attente</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy }}>
                {data.pending_leaves}
              </Text>
            </Card>

            {/* 8. Documents Générés */}
            <Card ui={ui} style={{ width: '48%' }}>
              <View style={[styles.rowStart, { marginBottom: 12 }]}>
                <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.surfaceAlt }}>
                  <Feather name="folder" size={20} color={theme.navy} />
                </View>
                <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Documents Générés</Text>
              </View>
              <Text style={{ fontSize: 24, fontWeight: '800', color: theme.navy }}>
                {data.generated_documents}
              </Text>
            </Card>

            <Text style={[styles.bodyStrong, { fontSize: 18, marginBottom: 16, marginTop: 8 }]}>Vue d'Ensemble & Répartition</Text>

            <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 16, marginBottom: 32 }}>


              {/* Demographics & Distribution */}
              <AICard ui={ui} style={{ width: '48%' }}>
                <View style={[styles.rowStart, { marginBottom: 12 }]}>
                  <View style={{ padding: 8, borderRadius: 8, backgroundColor: 'rgba(99, 102, 241, 0.1)' }}>
                    <Feather name="pie-chart" size={20} color="#6366F1" />
                  </View>
                  <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Démographie</Text>
                </View>

                <View style={{ flexDirection: 'column', alignItems: 'center', marginTop: 8 }}>
                  <DonutChart data={data.demographics.gender_distribution} size={100} strokeWidth={12} />

                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', marginTop: 12, gap: 8 }}>
                    {data.demographics.gender_distribution.map((g, i) => (
                      <View key={i} style={[styles.rowStart]}>
                        <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: g.color, marginRight: 4 }} />
                        <Text style={[styles.metaText, { fontSize: 10 }]}>{g.label} ({g.count})</Text>
                      </View>
                    ))}
                  </View>

                  <View style={[styles.rowBetween, { width: '100%', marginTop: 16, borderTopWidth: 1, borderColor: theme.line, paddingTop: 16 }]}>
                    <View style={{ alignItems: 'center' }}>
                      <Text style={{ fontSize: 20, fontWeight: '800', color: '#6366F1' }}>{data.demographics.total_active}</Text>
                      <Text style={[styles.metaText, { fontSize: 10 }]}>Total Actifs</Text>
                    </View>
                    <View style={{ alignItems: 'center' }}>
                      <Text style={{ fontSize: 20, fontWeight: '800', color: theme.navy }}>{data.demographics.average_age}a</Text>
                      <Text style={[styles.metaText, { fontSize: 10 }]}>Âge Moy.</Text>
                    </View>
                  </View>
                </View>
              </AICard>

              {/* Payroll Distribution */}
              <Card ui={ui} style={{ width: '48%' }}>
                <View style={[styles.rowStart, { marginBottom: 12 }]}>
                  <View style={{ padding: 8, borderRadius: 8, backgroundColor: theme.emerald + '20' }}>
                    <Feather name="bar-chart-2" size={20} color={theme.emerald} />
                  </View>
                  <Text style={[styles.bodyStrong, { marginLeft: 8, color: theme.navy, flexShrink: 1, fontSize: 13 }]} numberOfLines={2}>Salaires</Text>
                </View>

                <View style={{ marginTop: 8, flex: 1, justifyContent: 'center' }}>
                  {(() => {
                    const maxPayroll = Math.max(...data.payroll_by_department.map(d => d.amount), 1);
                    return data.payroll_by_department.map((dept, index) => {
                      const percentage = (dept.amount / maxPayroll) * 100;
                      return (
                        <View key={index} style={{ marginBottom: 12 }}>
                          <View style={[styles.rowBetween, { marginBottom: 4 }]}>
                            <Text style={[styles.bodyText, { fontSize: 11, flexShrink: 1 }]} numberOfLines={1}>{dept.department || 'Non assigné'}</Text>
                            <Text style={[styles.bodyStrong, { fontSize: 11, marginLeft: 4, flexShrink: 0 }]}>
                              {dept.amount > 1000 ? `${(dept.amount / 1000).toFixed(1)}k` : dept.amount} €
                            </Text>
                          </View>
                          <View style={{ width: '100%', height: 4, backgroundColor: theme.line, borderRadius: 2 }}>
                            <View style={{ width: `${percentage}%`, height: 4, backgroundColor: theme.emerald, borderRadius: 2 }} />
                          </View>
                        </View>
                      );
                    });
                  })()}
                  {data.payroll_by_department.length === 0 && (
                    <Text style={styles.metaText}>Aucune donnée.</Text>
                  )}
                </View>
              </Card>

            </View>

          </View>
        </>
      ) : null}

    </ScrollView>
  );
}
