import { HrTrainingsScreen } from './HrTrainingsScreen';
import { TrainingsScreen } from './TrainingsScreen';
import { isRhRole } from '../lib/auth';
import { OffboardingScreen } from './OffboardingScreen';
import { TasksView } from './TasksScreen';


import React, { useState, useEffect } from "react";
import { View, Text, Pressable, ScrollView, BackHandler } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card } from "../components/ui/Card";

import { SectionHeader } from "../components/ui/SectionHeader";
import { Ui, ViewId } from "../types";
import { BackButton } from "../components/ui/BackButton";
import { HrLeavesScreen } from './HrLeavesScreen';
import { HrDocumentsScreen } from './HrDocumentsScreen';
import { HrInterviewsScreen } from './HrInterviewsScreen';
import { HrAnalyticsScreen } from './HrAnalyticsScreen';
import { RecrutementView, RequestsRhView } from "./RhScreens";

export function RhHubScreen({ ui, onNavigate, sessionProfile, triggerFeedback }: { ui: Ui, onNavigate: (v: ViewId) => void, sessionProfile?: any, triggerFeedback?: (msg?: string) => void }) {
  const { styles, theme } = ui;
  const isRh = isRhRole(sessionProfile?.roleId ?? sessionProfile?.role);
  

// Local Sub-Router state to bypass App.tsx modification restriction
  const [subView, setSubView] = useState<'hub' | 'recrutement' | 'formations' | 'rapports' | 'contract' | 'offboarding' | 'rh_requests' | 'my_tasks' | 'leaves_validation' | 'documents' | 'interviews'>('hub');
  // Handle hardware back button on Android
  useEffect(() => {
    const backAction = () => {
      if (subView !== 'hub') {
        setSubView('hub');
        return true; // Prevent default behavior
      }
      return false; // Let normal back happen
    };
    const backHandler = BackHandler.addEventListener("hardwareBackPress", backAction);
    return () => backHandler.remove();
  }, [subView]);

  const renderSubView = () => {
    if (subView === 'recrutement') return <RecrutementView ui={ui} sessionProfile={sessionProfile} />;
    if (subView === 'formations') {
      return isRh 
        ? <HrTrainingsScreen ui={ui} onNavigate={onNavigate} sessionProfile={sessionProfile} triggerFeedback={triggerFeedback || (() => {})} />
        : <TrainingsScreen ui={ui} sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} />;
    }
    if (subView === 'rapports') return <HrAnalyticsScreen ui={ui} sessionProfile={sessionProfile} />;
    if (subView === 'offboarding') return <OffboardingScreen ui={ui} sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} />;
    if (subView === 'rh_requests') return <RequestsRhView ui={ui} sessionProfile={sessionProfile} triggerFeedback={(m: string) => {}} />;
    if (subView === 'my_tasks') return <TasksView ui={ui} />;
    if (subView === 'leaves_validation') return <HrLeavesScreen ui={ui} />;
    if (subView === 'documents') return <HrDocumentsScreen ui={ui} />;
    if (subView === 'interviews') return <HrInterviewsScreen ui={ui} />;
    return null;
  };

  if (subView !== 'hub') {
    return (
      <>
        <View style={{ paddingHorizontal: 16, paddingTop: 16, paddingBottom: 0 }}>
          <View style={{ marginLeft: -8, alignSelf: 'flex-start' }}>
            <BackButton onPress={() => setSubView('hub')} ui={ui} />
          </View>
        </View>
        {renderSubView()}
      </>
    );
  }

  // Configuration backend-driven
  let strategyActions: any[] = [];
  let operationalActions: any[] = [];

  if (isRh) {
    strategyActions = [
      { id: 'documents', icon: 'file-text', label: 'Gestion Documents', desc: 'Dossiers et attestations', status: 'available', action: () => setSubView('documents') },
      { id: 'leaves_validation', icon: 'calendar', label: 'Validation des Congés', desc: 'Soldes et demandes', status: 'available', action: () => setSubView('leaves_validation') },
      { id: 'interviews', icon: 'mic', label: 'Entretiens Annuels', desc: 'Évaluations et objectifs', status: 'available', action: () => setSubView('interviews') },
      { id: 'offboarding', icon: 'log-out', label: 'Départs', desc: 'Plans d\'offboarding', status: 'available', action: () => onNavigate('manager_offboarding' as ViewId) },
    ];
    operationalActions = [
      { id: 'hr_team', icon: 'users', label: 'Personnel', desc: 'Annuaire et dossiers', status: 'available', action: () => onNavigate('hr_team' as ViewId) },
      { id: 'trainings', icon: 'book', label: 'Formations RH', desc: 'Catalogue et sessions', status: 'available', action: () => setSubView('formations') },
      { id: 'onboarding', icon: 'map', label: 'Intégration', desc: 'Plans d\'onboarding', status: 'available', action: () => onNavigate('manager_onboarding' as ViewId) },
      { id: 'recrutement', icon: 'user-plus', label: 'Recrutement', desc: 'Suivi des candidats', status: 'available', action: () => setSubView('recrutement') },
      { id: 'absences', icon: 'clock', label: 'Absences', desc: 'Suivi et déclarations', status: 'available', action: () => onNavigate('absences' as ViewId) },
      { id: 'announcements', icon: 'message-square', label: 'Communications', desc: 'Annonces globales ou ciblées', status: 'available', action: () => onNavigate('announcements' as ViewId) },
      { id: 'hr_contracts', icon: 'file-text', label: 'Contrats', desc: 'Contrats actifs', status: 'available', action: () => onNavigate('hr_contracts' as ViewId) },
    ];
  } else {
    operationalActions = [
      { id: 'onboarding', icon: 'map', label: 'Mon Intégration', desc: 'Parcours et tâches assignées', status: 'available', action: () => onNavigate('onboarding' as ViewId) },
      { id: 'documents', icon: 'file-text', label: 'Documents RH', desc: 'Attestations, Justificatifs', status: 'available', action: () => onNavigate('documents' as ViewId) },
      { id: 'leave', icon: 'sun', label: 'Congés', desc: 'Soldes et demandes', status: 'available', action: () => onNavigate('leave' as ViewId) },
      { id: 'absences', icon: 'clock', label: 'Absences', desc: 'Déclarer une absence', status: 'available', action: () => onNavigate('absences' as ViewId) },
      { id: 'timesheet', icon: 'check-square', label: 'Pointage', desc: 'Saisie des temps', status: 'available', action: () => onNavigate('timesheet' as ViewId) },
      { id: 'requests', icon: 'tag', label: 'Mes Demandes', desc: 'Support et attestations', status: 'available', action: () => onNavigate('requests' as ViewId) },
      { id: 'offboarding', icon: 'log-out', label: 'Offboarding', desc: 'Gérer mon départ', status: 'available', action: () => setSubView('offboarding') },
      { id: 'my_tasks', icon: 'check-square', label: 'Mes Tâches', desc: 'Tâches assignées', status: 'available', action: () => setSubView('my_tasks') },
    ];
    strategyActions = [
      { id: 'trainings', icon: 'book', label: 'Mes Formations', desc: 'Catalogue et sessions', status: 'available', action: () => setSubView('formations') },
      { id: 'surveys', icon: 'bar-chart-2', label: 'Sondages', desc: 'Enquêtes QVT et feedback', status: 'available', action: () => onNavigate('surveys' as ViewId) },
    ];
  }

  const renderActionGrid = (actions: any[]) => (
    <View style={[styles.actionGrid, { flexWrap: "wrap", justifyContent: "space-between" }]}>
      {actions.map((action, idx) => {
        const isAvailable = action.status === 'available';
        return (
          <Pressable 
            key={action.id} 
            style={[
              styles.card, 
              { 
                width: '48%', 
                marginBottom: 16, 
                padding: 16,
                backgroundColor: isAvailable ? theme.card : theme.background,
                borderColor: isAvailable ? theme.line : theme.line + '50',
                borderWidth: 1,
                opacity: isAvailable ? 1 : 0.6
              }
            ]} 
            onPress={() => isAvailable && action.action()}
            disabled={!isAvailable}
          >
            <View style={[styles.rowBetween, { marginBottom: 12 }]}>
              <View style={{ backgroundColor: isAvailable ? theme.sky + '20' : theme.muted + '20', padding: 10, borderRadius: 10 }}>
                <Feather name={action.icon as any} size={20} color={isAvailable ? theme.sky : theme.muted} />
              </View>
            </View>
            <Text style={[styles.bodyStrong, { fontSize: 14, marginBottom: 2 }]} numberOfLines={1} ellipsizeMode="tail">
              {action.label}
            </Text>
            <Text style={[styles.metaText, { fontSize: 11, color: theme.muted }]} numberOfLines={1} ellipsizeMode="tail">
              {action.desc}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );

  const renderSecondaryActions = (actions: any[]) => (
    <Card ui={ui} style={{ padding: 0, overflow: 'hidden' }}>
      <View style={{ flexDirection: 'column' }}>
        {actions.map((action, idx) => {
          const isAvailable = action.status === 'available';
          return (
            <Pressable 
              key={action.id} 
              style={({ pressed }) => [
                styles.rowStart, 
                { 
                  padding: 16, 
                  borderBottomWidth: idx < actions.length - 1 ? 1 : 0, 
                  borderBottomColor: theme.line,
                  backgroundColor: pressed && isAvailable ? theme.line + '30' : 'transparent',
                  opacity: isAvailable ? 1 : 0.6
                }
              ]} 
              onPress={() => isAvailable && action.action()}
            >
              <View style={{ backgroundColor: isAvailable ? theme.cardElevated || theme.line + '50' : theme.muted + '20', padding: 10, borderRadius: 10, marginRight: 16 }}>
                <Feather name={action.icon as any} size={18} color={isAvailable ? theme.text : theme.muted} />
              </View>
              <View style={{ flex: 1 }}>
                <View style={[styles.rowStart, { marginBottom: 2 }]}>
                  <Text style={[styles.bodyStrong, { fontSize: 15 }]} numberOfLines={1}>{action.label}</Text>
                </View>
                <Text style={[styles.metaText, { fontSize: 12, color: theme.muted }]} numberOfLines={1} ellipsizeMode="tail">{action.desc}</Text>
              </View>
              {isAvailable && <Feather name="chevron-right" size={18} color={theme.muted} style={{ marginLeft: 8 }} />}
            </Pressable>
          );
        })}
      </View>
    </Card>
  );


return (
    <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        <View style={{ marginBottom: 16 }}>
          <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>
            {isRh ? "Opérations RH" : "Hub RH"}
          </Text>
          <Text style={styles.mutedText}>
            {isRh ? "Outils de gestion et de pilotage des ressources humaines" : "Tous vos services collaborateurs au même endroit."}
          </Text>
        </View>

        {isRh && (
          <>
            <SectionHeader icon="briefcase" title="Gestion Opérationnelle" ui={ui} />
            {renderActionGrid(operationalActions)}
            
            <SectionHeader icon="compass" title="Pilotage & Stratégie" ui={ui} />
            {renderSecondaryActions(strategyActions)}
          </>
        )}

        {!isRh && (
          <>
            <SectionHeader icon="book-open" title="Actions Rapides" ui={ui} />
            {renderActionGrid(operationalActions)}
            
            <SectionHeader icon="more-horizontal" title="Services et Rapports" ui={ui} />
            {renderSecondaryActions(strategyActions)}
          </>
        )}
      </View>
    </ScrollView>
  );
}
