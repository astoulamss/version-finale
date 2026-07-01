import React, { useState, useEffect, useMemo } from "react";

import { View, Text, ScrollView, Pressable, ActivityIndicator, Alert, TextInput, Platform } from "react-native";
import DateTimePicker from "@react-native-community/datetimepicker";
import { Feather } from "@expo/vector-icons";
import { Ui } from "../types";
import { absencesService } from "../services/absences.service";
import { managerService } from "../services/manager.service";
import { BackButton } from "../components/ui/BackButton";

export const ManagerAbsencesScreen: React.FC<{
  sessionProfile: any;
  ui: any;
  onNavigate?: (v: any) => void;
}> = ({ sessionProfile, ui, onNavigate }) => {
  const { theme, styles } = ui;

  const [activeTab, setActiveTab] = useState<"declare" | "register" | "history">("declare");
  const [loading, setLoading] = useState(true);
  
  const [teamAbsences, setTeamAbsences] = useState<any[]>([]);
  const [archivedAbsences, setArchivedAbsences] = useState<any[]>([]);
  const [teamMembers, setTeamMembers] = useState<any[]>([]);

  // Modals for custom dropdowns
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showTypeModal, setShowTypeModal] = useState(false);

  // Form State
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [absenceType, setAbsenceType] = useState<string>("maladie");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [showPicker, setShowPicker] = useState<"start" | "end" | null>(null);
  const currentPickerDate = showPicker === "start" ? (startDate ? new Date(startDate) : new Date()) : (endDate ? new Date(endDate) : new Date());
  const [reason, setReason] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [editingAbsenceId, setEditingAbsenceId] = useState<number | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [absencesActive, absencesArchived, members] = await Promise.all([
        absencesService.fetchTeamAbsences(false).catch(() => []),
        absencesService.fetchTeamAbsences(true).catch(() => []),
        managerService.fetchTeamMembers().catch(() => [])
      ]);
      setTeamAbsences(absencesActive || []);
      setArchivedAbsences(absencesArchived || []);
      
      setTeamMembers(members || []);
      
      if (members && members.length > 0 && !selectedEmployeeId) {
        setSelectedEmployeeId(members[0].user_id);
      }
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDeclareAbsence = async () => {
    if (!selectedEmployeeId || !startDate || !endDate) {
      Alert.alert("Erreur", "Veuillez remplir tous les champs obligatoires.");
      return;
    }

    setSubmitting(true);
    try {
      if (editingAbsenceId) {
        await absencesService.updateAbsence(editingAbsenceId, {
          absence_type: absenceType,
          start_date: startDate + "T00:00:00Z",
          end_date: endDate + "T23:59:59Z",
          reason: reason
        });
        Alert.alert("Succès", "L'absence a été modifiée avec succès.");
      } else {
        await absencesService.declareAbsence({
          employee_id: selectedEmployeeId,
          absence_type: absenceType,
          start_date: startDate + "T00:00:00Z",
          end_date: endDate + "T23:59:59Z",
          reason: reason
        });
        Alert.alert("Succès", "L'absence a été déclarée avec succès.");
      }
      
      setStartDate("");
      setEndDate("");
      setReason("");
      setEditingAbsenceId(null);
      fetchData();
      setActiveTab("register");
    } catch (err: any) {
      Alert.alert("Erreur", err.response?.data?.detail || "Action impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async (id: number, status: string | {is_archived: boolean}) => {
    try {
      if (typeof status === 'string') {
        await absencesService.updateAbsence(id, { status });
      } else {
        await absencesService.updateAbsence(id, status);
      }
      fetchData();
    } catch (err: any) {
      Alert.alert("Erreur", err.response?.data?.detail || "Action impossible");
    }
  };

  const handleEditAbsence = (absence: any) => {
    setEditingAbsenceId(absence.id);
    setSelectedEmployeeId(absence.employee_id);
    setAbsenceType(absence.absence_type);
    setStartDate(absence.start_date.split('T')[0]);
    setEndDate(absence.end_date.split('T')[0]);
    setReason(absence.reason || "");
    setActiveTab("declare");
  };

  const cancelEdit = () => {
    setEditingAbsenceId(null);
    setStartDate("");
    setEndDate("");
    setReason("");
    setActiveTab("register");
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved": return "#6366F1"; // Purple/Indigo as per screenshot
      case "rejected": return "#EF4444";
      case "pending": return "#D97706"; // Amber/Orange
      case "received": return "#3B82F6";
      default: return theme.muted;
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case "approved": return "#EEF2FF";
      case "rejected": return "#FEF2F2";
      case "pending": return "#FFFBEB"; // Light yellow/orange
      case "received": return "#EFF6FF";
      default: return theme.surfaceAlt;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "approved": return "Approuvée";
      case "rejected": return "Rejetée";
      case "pending": return "En Attente";
      case "received": return "Reçue";
      default: return status;
    }
  };

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yy = d.getFullYear();
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    const sec = String(d.getSeconds()).padStart(2, '0');
    return `${dd}/${mm}/${yy} ${hh}:${min}:${sec}`;
  };

  // Grouper les absences pour l'historique
  const groupedHistory = useMemo(() => {
    // Combiner les actives non en attente et les archivées
    const allHistory = [...teamAbsences.filter(a => a.status !== 'pending'), ...archivedAbsences];
    
    const groups: Record<number, { nom: string, prenom: string, absences: any[], totalHours: number }> = {};
    
    allHistory.forEach(abs => {
      if (!groups[abs.employee_id]) {
        groups[abs.employee_id] = {
          nom: abs.nom,
          prenom: abs.prenom,
          absences: [],
          totalHours: 0
        };
      }
      
      let durationHours = 0;
      if (abs.start_date && abs.end_date) {
        durationHours = (new Date(abs.end_date).getTime() - new Date(abs.start_date).getTime()) / (1000 * 60 * 60);
      }
      
      groups[abs.employee_id].absences.push(abs);
      groups[abs.employee_id].totalHours += Math.max(0, durationHours);
    });
    
    return Object.values(groups);
  }, [teamAbsences, archivedAbsences]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background }}>
      <View style={{ padding: 20, flexDirection: 'row', alignItems: 'center' }}>
        <View style={{ marginRight: 16 }}>
          <BackButton onPress={() => onNavigate && onNavigate("manager_hub")} ui={ui} />
        </View>
        <View>
          <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text }}>Gestion des Absences</Text>
          <Text style={{ color: theme.muted, fontSize: 14 }}>Déclarez et suivez les absences de l'équipe</Text>
        </View>
      </View>

      <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
        <View style={{ flexDirection: 'row', backgroundColor: theme.card, borderRadius: 8, padding: 4, borderWidth: 1, borderColor: theme.line }}>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'declare' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('declare')}
          >
            <Text style={{ fontWeight: activeTab === 'declare' ? '600' : '400', color: theme.text }}>Déclarer</Text>
          </Pressable>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'register' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('register')}
          >
            <Text style={{ fontWeight: activeTab === 'register' ? '600' : '400', color: theme.text }}>Registre</Text>
          </Pressable>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'history' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('history')}
          >
            <Text style={{ fontWeight: activeTab === 'history' ? '600' : '400', color: theme.text }}>Historique</Text>
          </Pressable>
        </View>
      </View>

      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={theme.sky} />
        </View>
      ) : (
        <ScrollView style={{ flex: 1, paddingHorizontal: 20 }} showsVerticalScrollIndicator={false}>
          
          {activeTab === "register" && (
            <View>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
                <Feather name="users" size={20} color={theme.sky} style={{ marginRight: 8 }} />
                <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>Registre des Absences Équipe</Text>
              </View>

              {teamAbsences.length === 0 ? (
                <View style={{ padding: 40, alignItems: 'center', opacity: 0.6 }}>
                  <Feather name="check-circle" size={48} color={theme.muted} style={{ marginBottom: 16 }} />
                  <Text style={{ color: theme.text, fontSize: 16, fontWeight: '600' }}>Registre vide</Text>
                  <Text style={{ color: theme.muted, textAlign: 'center', marginTop: 8 }}>Aucune absence en cours pour l'équipe.</Text>
                </View>
              ) : (
                teamAbsences.map(absence => {
                  let durationHours = 0;
                  if (absence.start_date && absence.end_date) {
                    durationHours = Math.max(0, (new Date(absence.end_date).getTime() - new Date(absence.start_date).getTime()) / (1000 * 60 * 60));
                  }

                  return (
                    <View key={absence.id} style={{ backgroundColor: theme.card, borderRadius: 12, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: theme.line }}>
                      
                      {/* En-tête */}
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>
                          {absence.prenom} {absence.nom}
                        </Text>
                        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                          <View style={{ backgroundColor: getStatusBg(absence.status), paddingHorizontal: 12, paddingVertical: 4, borderRadius: 16, borderWidth: 1, borderColor: getStatusColor(absence.status) + '30', marginRight: 12 }}>
                            <Text style={{ color: getStatusColor(absence.status), fontWeight: 'bold', fontSize: 12 }}>
                              {getStatusLabel(absence.status)}
                            </Text>
                          </View>
                          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 14 }}>
                            {Math.round(durationHours)}h
                          </Text>
                        </View>
                      </View>

                      {/* Type */}
                      <Text style={{ color: theme.text, fontSize: 15, marginBottom: 12, textTransform: 'capitalize' }}>
                        {absence.absence_type}
                      </Text>

                      {/* Dates */}
                      <Text style={{ color: theme.muted, fontSize: 14, marginBottom: 4 }}>
                        Du: {formatDate(absence.start_date)}
                      </Text>
                      <Text style={{ color: theme.muted, fontSize: 14, marginBottom: 12 }}>
                        Au: {formatDate(absence.end_date)}
                      </Text>

                      {/* Motif */}
                      {absence.reason && (
                        <View style={{ borderLeftWidth: 3, borderLeftColor: theme.line, paddingLeft: 12, marginBottom: 16 }}>
                          <Text style={{ color: theme.muted, fontSize: 14, fontStyle: 'italic' }}>
                            "{absence.reason}"
                          </Text>
                        </View>
                      )}

                      {/* Ligne séparatrice */}
                      <View style={{ height: 1, backgroundColor: theme.line, marginBottom: 16, marginTop: 4 }} />

                      {/* Actions */}
                      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'flex-start' }}>
                        <Pressable 
                          onPress={() => handleEditAbsence(absence)}
                          style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surfaceAlt, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 }}>
                          <Feather name="edit" size={14} color={theme.text} style={{ marginRight: 6 }} />
                          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 13 }}>Modifier</Text>
                        </Pressable>
                        
                        <Pressable 
                          onPress={() => handleUpdateStatus(absence.id, { is_archived: true })}
                          style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surfaceAlt, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 }}>
                          <Feather name="archive" size={14} color={theme.text} style={{ marginRight: 6 }} />
                          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 13 }}>Archiver</Text>
                        </Pressable>

                        {absence.status !== 'received' && (
                          <Pressable 
                            onPress={() => handleUpdateStatus(absence.id, 'received')}
                            style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#EFF6FF', borderWidth: 1, borderColor: '#BFDBFE', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 }}>
                            <Feather name="check-circle" size={14} color="#3B82F6" style={{ marginRight: 6 }} />
                            <Text style={{ color: '#3B82F6', fontWeight: '600', fontSize: 13 }}>Reçu</Text>
                          </Pressable>
                        )}

                        <Pressable 
                          onPress={() => handleUpdateStatus(absence.id, 'rejected')}
                          style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#FEF2F2', borderWidth: 1, borderColor: '#FECACA', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 }}>
                          <Feather name="x-circle" size={14} color="#EF4444" style={{ marginRight: 6 }} />
                          <Text style={{ color: '#EF4444', fontWeight: '600', fontSize: 13 }}>Rejeter</Text>
                        </Pressable>

                        <Pressable 
                          onPress={() => handleUpdateStatus(absence.id, 'approved')}
                          style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#6366F1', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, marginLeft: 'auto' }}>
                          <Feather name="check-circle" size={14} color="white" style={{ marginRight: 6 }} />
                          <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 13 }}>Approuver</Text>
                        </Pressable>
                      </View>

                    </View>
                  );
                })
              )}
            </View>
          )}

          {activeTab === "history" && (
            <View>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
                <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>Historique des Absences</Text>
              </View>

              {groupedHistory.length === 0 ? (
                <View style={{ padding: 40, alignItems: 'center', opacity: 0.6 }}>
                  <Feather name="calendar" size={48} color={theme.muted} style={{ marginBottom: 16 }} />
                  <Text style={{ color: theme.text, fontSize: 16, fontWeight: '600' }}>Historique vide</Text>
                  <Text style={{ color: theme.muted, textAlign: 'center', marginTop: 8 }}>Aucun historique d'absence disponible.</Text>
                </View>
              ) : (
                groupedHistory.map(group => (
                  <View key={group.absences[0].employee_id} style={{ backgroundColor: theme.card, borderRadius: 12, marginBottom: 16, borderWidth: 1, borderColor: theme.line, overflow: 'hidden' }}>
                    
                    {/* Header Employé */}
                    <View style={{ backgroundColor: theme.surfaceAlt, padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: theme.line }}>
                      <Text style={{ fontSize: 16, fontWeight: 'bold', color: theme.text }}>
                        {group.prenom} {group.nom}
                      </Text>
                      <Text style={{ fontSize: 14, fontWeight: 'bold', color: theme.text }}>
                        Total : {Math.round(group.totalHours)}h
                      </Text>
                    </View>

                    {/* Liste des absences */}
                    <View style={{ padding: 16 }}>
                      {group.absences.map((abs, idx) => {
                        let durationHours = 0;
                        if (abs.start_date && abs.end_date) {
                          durationHours = Math.max(0, (new Date(abs.end_date).getTime() - new Date(abs.start_date).getTime()) / (1000 * 60 * 60));
                        }

                        return (
                          <View key={abs.id} style={{ 
                            flexDirection: 'row', 
                            justifyContent: 'space-between', 
                            paddingVertical: 12,
                            borderBottomWidth: idx === group.absences.length - 1 ? 0 : 1,
                            borderBottomColor: theme.line
                          }}>
                            <View>
                              <Text style={{ color: theme.muted, fontSize: 14, marginBottom: 8, textTransform: 'capitalize' }}>
                                Arrêt {abs.absence_type}
                              </Text>
                              <Text style={{ color: theme.muted, fontSize: 13, marginBottom: 4 }}>
                                Du: {formatDate(abs.start_date)}
                              </Text>
                              <Text style={{ color: theme.muted, fontSize: 13 }}>
                                Au: {formatDate(abs.end_date)}
                              </Text>
                            </View>
                            
                            <View style={{ alignItems: 'flex-end' }}>
                              <View style={{ backgroundColor: getStatusBg(abs.status), paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, borderWidth: 1, borderColor: getStatusColor(abs.status) + '30', marginBottom: 8 }}>
                                <Text style={{ color: getStatusColor(abs.status), fontWeight: '600', fontSize: 11 }}>
                                  {getStatusLabel(abs.status)}
                                </Text>
                              </View>
                              <Text style={{ color: theme.text, fontWeight: '600', fontSize: 14 }}>
                                {Math.round(durationHours)}h
                              </Text>
                            </View>
                          </View>
                        );
                      })}
                    </View>

                  </View>
                ))
              )}
            </View>
          )}

          {activeTab === "declare" && (
            <View style={{ backgroundColor: theme.card, borderRadius: 12, padding: 24, marginBottom: 16, borderWidth: 1, borderColor: theme.line }}>
              
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 24 }}>
                <Feather name="plus-circle" size={24} color={theme.sky} style={{ marginRight: 12 }} />
                <Text style={{ fontSize: 20, fontWeight: 'bold', color: theme.text }}>
                  {editingAbsenceId ? "Modifier l'absence (Équipe)" : "Déclarer une absence (Équipe)"}
                </Text>
                {editingAbsenceId && (
                  <Pressable onPress={cancelEdit} style={{ marginLeft: 'auto' }}>
                    <Text style={{ color: theme.sky, fontWeight: '600' }}>Annuler</Text>
                  </Pressable>
                )}
              </View>

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, fontSize: 14 }}>Membre de l'équipe *</Text>
              <Pressable 
                onPress={() => setShowEmployeeModal(true)}
                style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: theme.surfaceAlt, borderWidth: 1, borderColor: theme.line, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 14, marginBottom: 20 }}>
                <Text style={{ color: selectedEmployeeId ? theme.text : theme.muted, fontSize: 15 }}>
                  {selectedEmployeeId 
                    ? (() => {
                        const emp = teamMembers.find(m => m.user_id === selectedEmployeeId); 
                        if (!emp) return "";
                        const prenom = emp.user?.prenom || emp.prenom || "";
                        const nom = emp.user?.nom || emp.nom || "";
                        return `${prenom} ${nom}`.trim();
                      })()
                    : "-- Sélectionner un collaborateur --"}
                </Text>
                <Feather name="chevron-down" size={18} color={theme.text} />
              </Pressable>

              <View style={{ flexDirection: 'row', gap: 16, marginBottom: showPicker ? 8 : 20 }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, fontSize: 14 }}>Début *</Text>
                  <Pressable onPress={() => setShowPicker("start")} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: theme.surfaceAlt, borderWidth: 1, borderColor: theme.line, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 14 }}>
                    <Text style={{ color: startDate ? theme.text : theme.muted, fontSize: 15 }}>
                      {startDate ? formatDate(startDate + "T00:00:00Z").substring(0, 10) : "jj/mm/aaaa"}
                    </Text>
                    <Feather name="calendar" size={18} color={theme.text} />
                  </Pressable>
                </View>

                <View style={{ flex: 1 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, fontSize: 14 }}>Fin *</Text>
                  <Pressable onPress={() => setShowPicker("end")} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: theme.surfaceAlt, borderWidth: 1, borderColor: theme.line, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 14 }}>
                    <Text style={{ color: endDate ? theme.text : theme.muted, fontSize: 15 }}>
                      {endDate ? formatDate(endDate + "T00:00:00Z").substring(0, 10) : "jj/mm/aaaa"}
                    </Text>
                    <Feather name="calendar" size={18} color={theme.text} />
                  </Pressable>
                </View>
              </View>

              {showPicker && (
                <View style={{ backgroundColor: theme.background, borderRadius: 12, padding: 12, marginBottom: 20 }}>
                  <DateTimePicker
                    value={currentPickerDate}
                    mode="date"
                    display={Platform.OS === "ios" ? "inline" : "default"}
                    onChange={(event: any, date?: Date) => {
                      if (Platform.OS === "android") setShowPicker(null);
                      if (date) {
                        const iso = date.toISOString().split("T")[0];
                        if (showPicker === "start") setStartDate(iso);
                        if (showPicker === "end") setEndDate(iso);
                      }
                    }}
                  />
                  {Platform.OS === "ios" && (
                    <Pressable onPress={() => setShowPicker(null)} style={{ marginTop: 12, padding: 12, backgroundColor: theme.sky, borderRadius: 8, alignItems: "center" }}>
                      <Text style={{ color: "#fff", fontWeight: "600" }}>Confirmer la date</Text>
                    </Pressable>
                  )}
                </View>
              )}

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, fontSize: 14 }}>Type d'absence *</Text>
              <Pressable 
                onPress={() => setShowTypeModal(true)}
                style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: theme.surfaceAlt, borderWidth: 1, borderColor: theme.line, borderRadius: 8, paddingHorizontal: 16, paddingVertical: 14, marginBottom: 20 }}>
                <Text style={{ color: theme.text, fontSize: 15, textTransform: 'capitalize' }}>
                  {absenceType === 'maladie' ? 'Arrêt Maladie' : absenceType}
                </Text>
                <Feather name="chevron-down" size={18} color={theme.text} />
              </Pressable>

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, fontSize: 14 }}>Motif (Optionnel)</Text>
              <TextInput
                style={{ backgroundColor: theme.surfaceAlt, borderWidth: 1, borderColor: theme.line, color: theme.text, paddingHorizontal: 16, paddingVertical: 14, borderRadius: 8, marginBottom: 32, height: 100, textAlignVertical: 'top', fontSize: 15 }}
                placeholder="Raison ou précisions..."
                placeholderTextColor={theme.muted}
                multiline
                value={reason}
                onChangeText={setReason}
              />

              <Pressable 
                disabled={submitting}
                onPress={handleDeclareAbsence}
                style={{ backgroundColor: '#6366F1', paddingVertical: 16, borderRadius: 8, alignItems: 'center' }}>
                {submitting ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>
                    {editingAbsenceId ? "Enregistrer les modifications" : "Déclarer l'absence"}
                  </Text>
                )}
              </Pressable>
              
            </View>
          )}

          <View style={{ height: 40 }} />
        </ScrollView>
      )}

      {/* Custom Dropdown Modals */}
      {showEmployeeModal && (
        <View style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.card, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, maxHeight: '60%' }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>Sélectionner un collaborateur</Text>
              <Pressable onPress={() => setShowEmployeeModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>
            <ScrollView showsVerticalScrollIndicator={false}>
              {teamMembers.map(member => {
                const prenom = member.user?.prenom || member.prenom || "";
                const nom = member.user?.nom || member.nom || "";
                return (
                  <Pressable 
                    key={member.user_id}
                    onPress={() => {}}
              style={{ paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: theme.line, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text style={{ color: theme.text, fontSize: 16 }}>{prenom} {nom}</Text>
                    {selectedEmployeeId === member.user_id && <Feather name="check" size={20} color={theme.sky} />}
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        </View>
      )}

      {showTypeModal && (
        <View style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.card, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>Type d'absence</Text>
              <Pressable onPress={() => setShowTypeModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>
            {[{id: 'maladie', label: 'Arrêt Maladie'}, {id: 'retard', label: 'Retard'}, {id: 'injustifie', label: 'Injustifiée'}, {id: 'autre', label: 'Autre'}].map(type => (
              <Pressable 
                key={type.id}
                onPress={() => {}}
              style={{ paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: theme.line, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ color: theme.text, fontSize: 16 }}>{type.label}</Text>
                {absenceType === type.id && <Feather name="check" size={20} color={theme.sky} />}
              </Pressable>
            ))}
          </View>
        </View>
      )}

    </View>
  );
};
