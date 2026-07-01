import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, Pressable, ActivityIndicator, TextInput, Platform, Modal } from "react-native";
import { Feather } from "@expo/vector-icons";
import DateTimePicker from '@react-native-community/datetimepicker';
import { EmployeeProfile, Ui, ViewId } from "../types";
import { Card } from "../components/ui/Card";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { trainingsService, Formation } from "../services/trainings.service";
import { BackButton } from "../components/ui/BackButton";
import api from "../services/api";

interface Props {
  sessionProfile: EmployeeProfile;
  triggerFeedback: (msg?: string) => void;
  ui: Ui;
  onNavigate: (view: ViewId) => void;
}

export const HrTrainingsScreen: React.FC<Props> = ({ sessionProfile, triggerFeedback, ui, onNavigate }) => {
  const { theme, styles } = ui;
  
  const [loading, setLoading] = useState(true);
  const [formations, setFormations] = useState<Formation[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [departmentId, setDepartmentId] = useState<number | null>(null);

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [selectedDeptName, setSelectedDeptName] = useState("Tous les départements (Optionnel)");

  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);

  const onChangeStart = (event: any, selectedDate?: Date) => {
    if (Platform.OS === 'android') {
      setShowStartPicker(false);
    }
    if (selectedDate) {
      setStartDate(selectedDate.toISOString().split('T')[0]);
    }
  };

  const onChangeEnd = (event: any, selectedDate?: Date) => {
    if (Platform.OS === 'android') {
      setShowEndPicker(false);
    }
    if (selectedDate) {
      setEndDate(selectedDate.toISOString().split('T')[0]);
    }
  };

  // Participants modal
  const [showParticipants, setShowParticipants] = useState<number | null>(null);
  const [participants, setParticipants] = useState<any[]>([]);
  const [loadingParticipants, setLoadingParticipants] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [formationsData, deptsData] = await Promise.all([
        trainingsService.getAllFormationsRH(),
        api.get('/api/employees/departments').then(res => res.data).catch(() => [])
      ]);
      setFormations(formationsData);
      setDepartments(deptsData);
    } catch (error) {
      console.error("Failed to load formations", error);
      triggerFeedback("Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrUpdate = async () => {
    if (!title || !startDate || !endDate) {
      triggerFeedback("Titre et dates sont obligatoires");
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        title,
        description,
        start_date: startDate,
        end_date: endDate,
        target_department_id: departmentId
      };

      if (editingId) {
        await trainingsService.updateFormation(editingId, payload);
        triggerFeedback("Formation modifiée");
      } else {
        await trainingsService.createFormation(payload);
        triggerFeedback("Formation créée");
      }
      setShowForm(false);
      resetForm();
      loadData();
    } catch (error: any) {
      console.error("Save error", error);
      triggerFeedback(error.response?.data?.detail || "Erreur lors de l'enregistrement");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (f: Formation) => {
    setEditingId(f.id);
    setTitle(f.title);
    setDescription(f.description || "");
    setStartDate(f.start_date);
    setEndDate(f.end_date);
    setDepartmentId(f.target_department_id);
    if (f.target_department_id) {
      const d = departments.find(d => d.id === f.target_department_id);
      setSelectedDeptName(d ? d.name : "Département inconnu");
    } else {
      setSelectedDeptName("Tous les départements (Optionnel)");
    }
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await trainingsService.deleteFormation(id);
      triggerFeedback("Formation supprimée");
      loadData();
    } catch (error) {
      console.error("Delete error", error);
      triggerFeedback("Erreur lors de la suppression");
    }
  };

  const loadParticipants = async (id: number) => {
    try {
      setShowParticipants(id);
      setLoadingParticipants(true);
      const data = await trainingsService.getParticipants(id);
      setParticipants(data);
    } catch (e) {
      triggerFeedback("Erreur de chargement des participants");
    } finally {
      setLoadingParticipants(false);
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setTitle("");
    setDescription("");
    setStartDate("");
    setEndDate("");
    setDepartmentId(null);
    setSelectedDeptName("Tous les départements (Optionnel)");
    setDropdownOpen(false);
  };

  const getDeptName = (deptId: number | null) => {
    if (!deptId) return "Tous";
    const d = departments.find(d => d.id === deptId);
    return d ? d.name : "N/A";
  };

  // Separation logic
  const today = new Date().toISOString().split('T')[0];
  const activeFormations = formations.filter(f => f.end_date >= today).sort((a, b) => a.start_date.localeCompare(b.start_date));
  const historyFormations = formations.filter(f => f.end_date < today).sort((a, b) => b.end_date.localeCompare(a.end_date));

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.background }}>
        <ActivityIndicator size="large" color={theme.sky} />
      </View>
    );
  }

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        
        <View style={styles.rowStart}>
          <View style={{ marginLeft: -8, marginRight: 8 }}>
            <BackButton onPress={() => onNavigate('operations')} ui={ui} />
          </View>
          <View>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Gestion Formations</Text>
            <Text style={styles.mutedText}>Catalogue et suivi des inscriptions</Text>
          </View>
        </View>

        {!showForm ? (
          <View style={{ marginBottom: 16 }}>
            <PrimaryButton 
              label="Nouvelle Formation" 
              icon="plus" 
              onPress={() => setShowForm(true)} 
              ui={ui} 
            />
          </View>
        ) : (
          <Card ui={ui} style={{ marginBottom: 24 }}>
            <View style={[styles.rowBetween, { marginBottom: 16 }]}>
              <Text style={[styles.heroTitle, { fontSize: 18 }]}>
                {editingId ? "Modifier la Formation" : "Créer une Formation"}
              </Text>
              <Pressable onPress={() => { setShowForm(false); resetForm(); }}>
                <Feather name="x" size={24} color={theme.muted} />
              </Pressable>
            </View>

            <View style={styles.stack}>
              <View>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Titre de la formation *</Text>
                <TextInput
                  style={{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                  placeholder="Ex: Formation React Native"
                  placeholderTextColor={theme.muted}
                  value={title}
                  onChangeText={setTitle}
                />
              </View>

              <View>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Description</Text>
                <TextInput
                  style={{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8, minHeight: 80, textAlignVertical: 'top' }}
                  placeholder="Objectifs et contenu..."
                  placeholderTextColor={theme.muted}
                  value={description}
                  onChangeText={setDescription}
                  multiline
                />
              </View>

              <View style={{ zIndex: 10 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Cible (Département)</Text>
                <Pressable
                  onPress={() => setDropdownOpen(!dropdownOpen)}
                  style={{
                    flexDirection: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: theme.background,
                    borderColor: theme.line,
                    borderWidth: 1,
                    padding: 12,
                    borderRadius: 8,
                  }}
                >
                  <Text style={{ color: theme.text }}>{selectedDeptName}</Text>
                  <Feather name={dropdownOpen ? "chevron-up" : "chevron-down"} size={20} color={theme.text} />
                </Pressable>

                {dropdownOpen && (
                  <View style={{
                    backgroundColor: theme.background,
                    borderColor: theme.line,
                    borderWidth: 1,
                    borderTopWidth: 0,
                    borderBottomLeftRadius: 8,
                    borderBottomRightRadius: 8,
                    maxHeight: 200,
                    marginTop: -4,
                  }}>
                    <ScrollView nestedScrollEnabled={true}>
                      <Pressable
                        onPress={() => {
                          setDepartmentId(null);
                          setSelectedDeptName("Tous les départements (Optionnel)");
                          setDropdownOpen(false);
                        }}
                        style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}
                      >
                        <Text style={{ color: theme.text }}>Tous les départements (Optionnel)</Text>
                      </Pressable>
                      {departments.map(d => (
                        <Pressable
                          key={d.id}
                          onPress={() => {
                            setDepartmentId(d.id);
                            setSelectedDeptName(d.name);
                            setDropdownOpen(false);
                          }}
                          style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}
                        >
                          <Text style={{ color: theme.text }}>{d.name}</Text>
                        </Pressable>
                      ))}
                    </ScrollView>
                  </View>
                )}
              </View>

              <View style={styles.rowBetween}>
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Date de début *</Text>
                  <Pressable 
                    style={{ backgroundColor: theme.background, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                    onPress={() => setShowStartPicker(true)}
                  >
                    <Text style={{ color: startDate ? theme.text : theme.muted }}>{startDate || "Sélectionner une date"}</Text>
                  </Pressable>
                  {showStartPicker && (
                    Platform.OS === 'ios' ? (
                      <Modal transparent animationType="slide">
                        <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                          <View style={{ backgroundColor: 'white', padding: 20, paddingBottom: 40 }}>
                            <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 10 }}>
                              <Pressable onPress={() => setShowStartPicker(false)}>
                                <Text style={{ color: theme.sky, fontWeight: 'bold', fontSize: 16 }}>Terminé</Text>
                              </Pressable>
                            </View>
                            <DateTimePicker themeVariant="light" textColor="#000000" 
                              value={startDate ? new Date(startDate) : new Date()}
                              mode="date"
                              display="spinner"
                              onChange={onChangeStart}
                            />
                          </View>
                        </View>
                      </Modal>
                    ) : (
                      <DateTimePicker themeVariant="light" textColor="#000000" 
                        value={startDate ? new Date(startDate) : new Date()}
                        mode="date"
                        display="default"
                        onChange={onChangeStart}
                      />
                    )
                  )}
                </View>
                <View style={{ flex: 1, marginLeft: 8 }}>
                  <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Date de fin *</Text>
                  <Pressable 
                    style={{ backgroundColor: theme.background, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                    onPress={() => setShowEndPicker(true)}
                  >
                    <Text style={{ color: endDate ? theme.text : theme.muted }}>{endDate || "Sélectionner une date"}</Text>
                  </Pressable>
                  {showEndPicker && (
                    Platform.OS === 'ios' ? (
                      <Modal transparent animationType="slide">
                        <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                          <View style={{ backgroundColor: 'white', padding: 20, paddingBottom: 40 }}>
                            <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 10 }}>
                              <Pressable onPress={() => setShowEndPicker(false)}>
                                <Text style={{ color: theme.sky, fontWeight: 'bold', fontSize: 16 }}>Terminé</Text>
                              </Pressable>
                            </View>
                            <DateTimePicker themeVariant="light" textColor="#000000" 
                              value={endDate ? new Date(endDate) : new Date()}
                              mode="date"
                              display="spinner"
                              onChange={onChangeEnd}
                            />
                          </View>
                        </View>
                      </Modal>
                    ) : (
                      <DateTimePicker themeVariant="light" textColor="#000000" 
                        value={endDate ? new Date(endDate) : new Date()}
                        mode="date"
                        display="default"
                        onChange={onChangeEnd}
                      />
                    )
                  )}
                </View>
              </View>

              <View style={{ marginTop: 16 }}>
                <PrimaryButton 
                  label={submitting ? "Enregistrement..." : (editingId ? "Enregistrer" : "Créer la formation")} 
                  icon="check" 
                  onPress={handleCreateOrUpdate} 
                  ui={ui} 
                />
              </View>
            </View>
          </Card>
        )}

        {/* SECTION: Formations en cours ou à venir */}
        <SectionHeader icon="book" title={`Formations en cours ou à venir (${activeFormations.length})`} ui={ui} />
        
        {activeFormations.length === 0 ? (
          <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 40, marginBottom: 24 }}>
            <Feather name="book-open" size={48} color={theme.muted} style={{ marginBottom: 16, opacity: 0.5 }} />
            <Text style={styles.mutedText}>Aucune formation active.</Text>
          </Card>
        ) : (
          <View style={[styles.stack, { marginBottom: 24 }]}>
            {activeFormations.map(f => (
              <Card key={f.id} ui={ui} style={{ padding: 16 }}>
                <Text style={[styles.bodyStrong, { fontSize: 16, marginBottom: 4 }]} numberOfLines={1}>{f.title}</Text>
                {f.description ? <Text style={[styles.bodyText, { marginBottom: 12 }]} numberOfLines={2}>{f.description}</Text> : null}
                
                <Text style={[styles.bodyStrong, { color: theme.sky, marginBottom: 6 }]}>
                  Cible: {getDeptName(f.target_department_id)}
                </Text>
                
                <Text style={[styles.mutedText, { marginBottom: 16 }]}>
                  Du {f.start_date} au {f.end_date}
                </Text>
                
                <View style={[styles.rowStart, { borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 12 }]}>
                  <Pressable 
                    onPress={() => loadParticipants(f.id)}
                    style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16, backgroundColor: theme.surfaceAlt, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 }}
                  >
                    <Feather name="users" size={14} color={theme.text} style={{ marginRight: 6 }} />
                    <Text style={{ color: theme.text, fontSize: 13, fontWeight: '600' }}>Participants</Text>
                  </Pressable>

                  <Pressable 
                    onPress={() => handleEdit(f)}
                    style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16, backgroundColor: theme.surfaceAlt, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 }}
                  >
                    <Feather name="edit-2" size={14} color={theme.text} style={{ marginRight: 6 }} />
                    <Text style={{ color: theme.text, fontSize: 13, fontWeight: '600' }}>Modifier</Text>
                  </Pressable>
                  
                  <Pressable 
                    onPress={() => handleDelete(f.id)}
                    style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#FEF2F2', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 }}
                  >
                    <Feather name="trash-2" size={14} color={theme.amber} style={{ marginRight: 6 }} />
                  </Pressable>
                </View>
              </Card>
            ))}
          </View>
        )}

        {/* SECTION: Historique des Formations */}
        <SectionHeader icon="archive" title={`Historique des Formations (${historyFormations.length})`} ui={ui} />
        
        {historyFormations.length === 0 ? (
          <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 40 }}>
            <Feather name="archive" size={48} color={theme.muted} style={{ marginBottom: 16, opacity: 0.5 }} />
            <Text style={styles.mutedText}>Aucun historique disponible.</Text>
          </Card>
        ) : (
          <Card ui={ui} style={{ padding: 0, overflow: 'hidden' }}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View>
                {/* Table Header */}
                <View style={{ flexDirection: 'row', borderBottomWidth: 1, borderBottomColor: theme.line, padding: 16, backgroundColor: theme.surfaceAlt }}>
                  <Text style={[styles.bodyStrong, { width: 200 }]}>Titre de la formation</Text>
                  <Text style={[styles.bodyStrong, { width: 150 }]}>Cible</Text>
                  <Text style={[styles.bodyStrong, { width: 200 }]}>Dates</Text>
                  <Text style={[styles.bodyStrong, { width: 250 }]}>Description</Text>
                  <Text style={[styles.bodyStrong, { width: 140 }]}>Actions</Text>
                </View>

                {/* Table Rows */}
                {historyFormations.map((f, index) => (
                  <View key={f.id} style={{ 
                    flexDirection: 'row', 
                    borderBottomWidth: index === historyFormations.length - 1 ? 0 : 1, 
                    borderBottomColor: theme.line, 
                    padding: 16,
                    alignItems: 'center'
                  }}>
                    <Text style={[styles.bodyStrong, { width: 200 }]} numberOfLines={2}>{f.title}</Text>
                    <Text style={[styles.bodyText, { color: theme.sky, width: 150 }]} numberOfLines={1}>{getDeptName(f.target_department_id)}</Text>
                    <Text style={[styles.bodyText, { width: 200 }]} numberOfLines={1}>Du {f.start_date} au {f.end_date}</Text>
                    <Text style={[styles.mutedText, { width: 250 }]} numberOfLines={2}>{f.description || "N/A"}</Text>
                    <View style={{ width: 140 }}>
                      <Pressable 
                        onPress={() => loadParticipants(f.id)}
                        style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surfaceAlt, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, alignSelf: 'flex-start' }}
                      >
                        <Feather name="users" size={14} color={theme.text} style={{ marginRight: 6 }} />
                        <Text style={{ color: theme.text, fontSize: 13, fontWeight: '600' }}>Voir Participants</Text>
                      </Pressable>
                    </View>
                  </View>
                ))}
              </View>
            </ScrollView>
          </Card>
        )}
        
      </View>

      {/* Participants Modal/Overlay */}
      {showParticipants !== null && (
        <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <View style={{ backgroundColor: theme.card, borderRadius: 16, width: '90%', maxHeight: '80%', padding: 20 }}>
            <View style={[styles.rowBetween, { marginBottom: 16 }]}>
              <Text style={[styles.heroTitle, { fontSize: 18 }]}>Participants ({participants.length})</Text>
              <Pressable onPress={() => setShowParticipants(null)}>
                <Feather name="x" size={24} color={theme.muted} />
              </Pressable>
            </View>

            {loadingParticipants ? (
              <ActivityIndicator color={theme.sky} style={{ marginVertical: 40 }} />
            ) : participants.length === 0 ? (
              <Text style={[styles.mutedText, { textAlign: 'center', marginVertical: 40 }]}>Aucun participant inscrit.</Text>
            ) : (
              <ScrollView showsVerticalScrollIndicator={false}>
                {participants.map(p => (
                  <View key={p.id} style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                    <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: theme.skySoft, justifyContent: 'center', alignItems: 'center', marginRight: 12 }}>
                      <Text style={{ color: theme.sky, fontWeight: 'bold' }}>{p.prenom?.[0]}{p.nom?.[0]}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.bodyStrong}>{p.prenom} {p.nom}</Text>
                      <Text style={styles.metaText}>{p.department ? p.department : "Sans département"}</Text>
                    </View>
                    <Text style={[styles.metaText, { fontSize: 10 }]}>Inscrit le {new Date(p.enrolled_at).toLocaleDateString()}</Text>
                  </View>
                ))}
              </ScrollView>
            )}
            
            <View style={{ marginTop: 16 }}>
              <PrimaryButton label="Fermer" icon="check" onPress={() => setShowParticipants(null)} ui={ui} />
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
};
