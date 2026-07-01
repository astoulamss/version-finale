import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, Pressable, ActivityIndicator, Alert, TextInput } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Ui } from "../types";
import { leavesService } from "../services/leaves.service";
import { managerService } from "../services/manager.service";
import { BackButton } from "../components/ui/BackButton";

export const ManagerLeavesScreen: React.FC<{
  sessionProfile: any;
  ui: any;
  onNavigate?: (v: any) => void;
}> = ({ sessionProfile, ui, onNavigate }) => {
  const { theme, styles } = ui;

  const [activeTab, setActiveTab] = useState<"pending" | "history" | "team">("pending");
  const [loading, setLoading] = useState(true);
  const [teamLeaves, setTeamLeaves] = useState<any[]>([]);
  const [leaveHistory, setLeaveHistory] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [leaves, history] = await Promise.all([
        leavesService.fetchTeamLeaves().catch(() => []),
        managerService.fetchLeaveHistory().catch(() => [])
      ]);
      setTeamLeaves(leaves);
      setLeaveHistory(history);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpdateStatus = async (id: number, status: string) => {
    try {
      await leavesService.updateLeaveStatus(id, status);
      fetchData();
    } catch (err: any) {
      Alert.alert("Erreur", err.response?.data?.detail || "Action impossible");
    }
  };

  const pendingLeaves = teamLeaves.filter(l => l.status === "pending");
  const historyLeaves = teamLeaves.filter(l => l.status !== "pending");

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved": return "#10B981";
      case "rejected": return "#EF4444";
      case "pending": return "#F59E0B";
      case "cancelled": return theme.muted;
      default: return theme.muted;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "approved": return "Approuvé";
      case "rejected": return "Refusé";
      case "pending": return "En attente";
      case "cancelled": return "Annulé";
      default: return status;
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.background }}>
      <View style={{ padding: 20, flexDirection: 'row', alignItems: 'center' }}>
        <View style={{ marginRight: 16 }}>
          <BackButton onPress={() => onNavigate && onNavigate("manager_hub")} ui={ui} />
        </View>
        <View>
          <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text }}>Gestion des Congés</Text>
          <Text style={{ color: theme.muted, fontSize: 14 }}>Gérez les absences de votre équipe</Text>
        </View>
      </View>

      <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
        <View style={{ flexDirection: 'row', backgroundColor: theme.card, borderRadius: 8, padding: 4, borderWidth: 1, borderColor: theme.line }}>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'pending' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('pending')}
          >
            <Text style={{ fontWeight: activeTab === 'pending' ? '600' : '400', color: theme.text }}>
              En attente {pendingLeaves.length > 0 && `(${pendingLeaves.length})`}
            </Text>
          </Pressable>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'history' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('history')}
          >
            <Text style={{ fontWeight: activeTab === 'history' ? '600' : '400', color: theme.text }}>Journal</Text>
          </Pressable>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'team' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('team')}
          >
            <Text style={{ fontWeight: activeTab === 'team' ? '600' : '400', color: theme.text }}>Équipe</Text>
          </Pressable>
        </View>
      </View>

      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={theme.sky} />
        </View>
      ) : (
        <ScrollView style={{ flex: 1, paddingHorizontal: 20 }} showsVerticalScrollIndicator={false}>
          {activeTab === "pending" && (
            <View>
              {pendingLeaves.length === 0 ? (
                <View style={{ padding: 40, alignItems: 'center', opacity: 0.6 }}>
                  <Feather name="check-circle" size={48} color={theme.muted} style={{ marginBottom: 16 }} />
                  <Text style={{ color: theme.text, fontSize: 16, fontWeight: '600' }}>Tout est à jour</Text>
                  <Text style={{ color: theme.muted, textAlign: 'center', marginTop: 8 }}>Aucune demande de congé en attente.</Text>
                </View>
              ) : (
                pendingLeaves.map(leave => (
                  <View key={leave.id} style={{ backgroundColor: theme.card, borderRadius: 16, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: theme.line }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 }}>
                      <View>
                        <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>
                          {leave.employee?.prenom} {leave.employee?.nom}
                        </Text>
                        <Text style={{ color: theme.sky, fontWeight: '600', fontSize: 14, marginTop: 4 }}>
                          {leave.leave_type_name || "Congé"}
                        </Text>
                      </View>
                      <View style={{ backgroundColor: getStatusColor(leave.status) + '20', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, alignSelf: 'flex-start' }}>
                        <Text style={{ color: getStatusColor(leave.status), fontWeight: 'bold', fontSize: 12 }}>{getStatusLabel(leave.status)}</Text>
                      </View>
                    </View>
                    
                    <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                      <Feather name="calendar" size={16} color={theme.muted} style={{ marginRight: 8 }} />
                      <Text style={{ color: theme.text }}>Du {leave.start_date} au {leave.end_date}</Text>
                    </View>
                    {leave.reason && (
                      <View style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 16 }}>
                        <Feather name="align-left" size={16} color={theme.muted} style={{ marginRight: 8, marginTop: 2 }} />
                        <Text style={{ color: theme.muted, flex: 1 }}>{leave.reason}</Text>
                      </View>
                    )}

                    <View style={{ flexDirection: 'row', gap: 12, marginTop: 12 }}>
                      <Pressable 
                        onPress={() => handleUpdateStatus(leave.id, "approved")}
                        style={{ flex: 1, backgroundColor: '#10B981', paddingVertical: 12, borderRadius: 8, alignItems: 'center' }}>
                        <Text style={{ color: 'white', fontWeight: 'bold' }}>Approuver</Text>
                      </Pressable>
                      <Pressable 
                        onPress={() => handleUpdateStatus(leave.id, "rejected")}
                        style={{ flex: 1, backgroundColor: 'transparent', borderWidth: 1, borderColor: '#EF4444', paddingVertical: 12, borderRadius: 8, alignItems: 'center' }}>
                        <Text style={{ color: '#EF4444', fontWeight: 'bold' }}>Refuser</Text>
                      </Pressable>
                    </View>
                  </View>
                ))
              )}
            </View>
          )}

          {activeTab === "team" && (
            <View>
              {historyLeaves.length === 0 ? (
                <Text style={{ color: theme.muted, textAlign: 'center', marginTop: 40 }}>Aucun historique de congé pour l'équipe.</Text>
              ) : (
                historyLeaves.map(leave => (
                  <View key={leave.id} style={{ backgroundColor: theme.card, borderRadius: 12, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: theme.line }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ fontSize: 16, fontWeight: 'bold', color: theme.text }}>
                        {leave.employee?.prenom} {leave.employee?.nom}
                      </Text>
                      <Text style={{ color: getStatusColor(leave.status), fontWeight: 'bold', fontSize: 12 }}>{getStatusLabel(leave.status)}</Text>
                    </View>
                    <Text style={{ color: theme.muted, fontSize: 13, marginBottom: 4 }}>{leave.leave_type_name || "Congé"}</Text>
                    <Text style={{ color: theme.text, fontSize: 14 }}>Du {leave.start_date} au {leave.end_date}</Text>
                  </View>
                ))
              )}
            </View>
          )}

          {activeTab === "history" && (
            <View>
              {leaveHistory.length === 0 ? (
                <Text style={{ color: theme.muted, textAlign: 'center', marginTop: 40 }}>Aucun journal d'audit disponible.</Text>
              ) : (
                leaveHistory.map((log, index) => (
                  <View key={log.id || index} style={{ flexDirection: 'row', marginBottom: 20 }}>
                    <View style={{ width: 40, alignItems: 'center' }}>
                      <View style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: theme.sky + '20', justifyContent: 'center', alignItems: 'center' }}>
                        <Feather name="activity" size={16} color={theme.sky} />
                      </View>
                      {index !== leaveHistory.length - 1 && (
                        <View style={{ width: 2, flex: 1, backgroundColor: theme.line, marginTop: 4 }} />
                      )}
                    </View>
                    <View style={{ flex: 1, marginLeft: 12, backgroundColor: theme.card, padding: 16, borderRadius: 12, borderWidth: 1, borderColor: theme.line }}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                        <Text style={{ fontWeight: 'bold', color: theme.text, fontSize: 14 }}>
                          {log.action.toUpperCase()}
                        </Text>
                        <Text style={{ color: theme.muted, fontSize: 12 }}>
                          {new Date(log.created_at).toLocaleDateString()} {new Date(log.created_at).toLocaleTimeString().substring(0, 5)}
                        </Text>
                      </View>
                      <Text style={{ color: theme.text, fontSize: 13, marginBottom: 8 }}>
                        {log.details}
                      </Text>
                      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <Feather name="user" size={12} color={theme.muted} style={{ marginRight: 6 }} />
                        <Text style={{ color: theme.muted, fontSize: 12 }}>
                          Par {log.performer_prenom} {log.performer_nom}
                        </Text>
                      </View>
                    </View>
                  </View>
                ))
              )}
            </View>
          )}
          
          <View style={{ height: 40 }} />
        </ScrollView>
      )}
    </View>
  );
};
