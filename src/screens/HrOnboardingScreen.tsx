import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, Pressable, ActivityIndicator, Modal, TextInput, Platform } from "react-native";
import { Feather } from "@expo/vector-icons";
import DateTimePicker from '@react-native-community/datetimepicker';
import { Ui } from "../types";
import { Card } from "../components/ui/Card";
import { PrimaryButton } from "../components/ui/Button";
import { BackButton } from "../components/ui/BackButton";
import { onboardingService } from "../services/onboarding.service";
import api from "../services/api";
import { isRhRole } from "../lib/auth";

export function ManagerOnboardingScreen({ ui, sessionProfile }: { ui: Ui, sessionProfile?: any }) {
  const { styles, theme } = ui;
  const isRh = isRhRole(sessionProfile?.roleId ?? sessionProfile?.role);
  const [activeTab, setActiveTab] = useState<'ongoing' | 'history'>('ongoing');
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [managePlan, setManagePlan] = useState<any>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [taskSubmitting, setTaskSubmitting] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedEmpId, setSelectedEmpId] = useState<number | null>(null);
  const [planType, setPlanType] = useState("30_days");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const plansData = await onboardingService.getAllPlans();
      setPlans(plansData || []);
      if (isRh) {
        try {
          const empRes = await api.get('/api/employees/');
          setEmployees(empRes.data || []);
        } catch (_) {}
      }
    } catch (e) {
      console.error("Error loading onboarding plans", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  useEffect(() => {
    if (startDate && planType) {
      const start = new Date(startDate);
      const days = planType === '7_days' ? 7 : planType === '90_days' ? 90 : 30;
      start.setDate(start.getDate() + days);
      setEndDate(start.toISOString().split('T')[0]);
    }
  }, [startDate, planType]);

  const handleCreatePlan = async () => {
    if (!selectedEmpId || !startDate || !endDate) {
      alert("Veuillez remplir tous les champs obligatoires.");
      return;
    }
    try {
      setSubmitting(true);
      await onboardingService.createPlan({ employee_id: selectedEmpId, plan_type: planType, start_date: startDate, end_date: endDate, status: "in_progress" });
      setShowCreateModal(false);
      setSelectedEmpId(null);
      setStartDate("");
      setEndDate("");
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Erreur de création");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePlan = async (id: number) => {
    try { await onboardingService.deletePlan(id); loadData(); }
    catch (_) { alert("Erreur lors de la suppression"); }
  };

  const handleToggleTask = async (task: any) => {
    try {
      const newStatus = task.status === "done" ? "todo" : "done";
      await onboardingService.updateTaskStatus(task.id, newStatus);
      setManagePlan((prev: any) => ({ ...prev, tasks: prev.tasks.map((t: any) => t.id === task.id ? { ...t, status: newStatus } : t) }));
      loadData();
    } catch (_) {}
  };

  const handleAddTask = async () => {
    if (!newTaskTitle.trim() || !managePlan) return;
    try {
      setTaskSubmitting(true);
      const newTask = await onboardingService.addTask(managePlan.id, { title: newTaskTitle, status: "todo" });
      setManagePlan((prev: any) => ({ ...prev, tasks: [...(prev.tasks || []), newTask] }));
      setNewTaskTitle("");
      loadData();
    } catch (_) { alert("Erreur lors de l'ajout de la tâche"); }
    finally { setTaskSubmitting(false); }
  };

  const onChangeDate = (setter: any, pickerSetter: any) => (event: any, selectedDate?: Date) => {
    if (Platform.OS !== 'ios') pickerSetter(false);
    if (selectedDate && event.type !== 'dismissed') {
      const local = new Date(selectedDate.getTime() - selectedDate.getTimezoneOffset() * 60000);
      setter(local.toISOString().split('T')[0]);
    }
  };

  const filteredPlans = plans.filter(p => activeTab === 'ongoing' ? p.status !== 'completed' : p.status === 'completed');

  const getPlanInitials = (plan: any) => {
    const p = plan.employee_prenom?.[0] || '';
    const n = plan.employee_nom?.[0] || '';
    return (p + n).toUpperCase();
  };

  // ── DETAIL VIEW ─────────────────────────────────────────────────────
  if (managePlan) {
    const totalTasks = managePlan.tasks?.length || 0;
    const doneTasks = managePlan.tasks?.filter((t: any) => t.status === "done").length || 0;
    const progress = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0;

    return (
      <View style={{ flex: 1 }}>
        <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
          {/* Header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 20 }}>
            <View style={{ marginRight: 12 }}>
              <BackButton onPress={() => setManagePlan(null)} ui={ui} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.heroTitle, { fontSize: 20 }]}>Plan d'intégration</Text>
              <Text style={[styles.mutedText, { marginTop: 2 }]}>{managePlan.employee_prenom} {managePlan.employee_nom}</Text>
            </View>
          </View>

          {/* Progress Card */}
          <Card ui={ui} style={{ marginBottom: 16 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
              <View style={{ width: 52, height: 52, borderRadius: 26, backgroundColor: theme.skySoft, alignItems: 'center', justifyContent: 'center', marginRight: 14 }}>
                <Text style={{ fontWeight: 'bold', fontSize: 18, color: theme.sky }}>{getPlanInitials(managePlan)}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.bodyStrong}>{managePlan.employee_prenom} {managePlan.employee_nom}</Text>
                <Text style={styles.mutedText}>{managePlan.plan_type?.replace('_', ' ')} • {managePlan.employee_role}</Text>
              </View>
              <View style={{ backgroundColor: progress === 100 ? theme.emeraldSoft : theme.skySoft, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 }}>
                <Text style={{ color: progress === 100 ? theme.emerald : theme.sky, fontWeight: 'bold', fontSize: 13 }}>{progress}%</Text>
              </View>
            </View>

            {/* Progress Bar */}
            <View style={{ backgroundColor: theme.line, borderRadius: 4, height: 8, marginBottom: 12 }}>
              <View style={{ backgroundColor: progress === 100 ? theme.emerald : theme.sky, borderRadius: 4, height: 8, width: `${progress}%` as any }} />
            </View>

            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={styles.mutedText}>{new Date(managePlan.start_date).toLocaleDateString('fr-FR')}</Text>
              <Text style={[styles.mutedText, { fontWeight: '600' }]}>{doneTasks}/{totalTasks} tâches</Text>
              <Text style={styles.mutedText}>{new Date(managePlan.end_date).toLocaleDateString('fr-FR')}</Text>
            </View>
          </Card>

          {/* Tasks */}
          <Text style={[styles.bodyStrong, { fontSize: 16, marginBottom: 12 }]}>Tâches de l'intégration</Text>
          {managePlan.tasks?.length === 0 && (
            <Card ui={ui}>
              <Text style={[styles.mutedText, { textAlign: 'center', paddingVertical: 20 }]}>Aucune tâche pour le moment.</Text>
            </Card>
          )}
          <View style={{ gap: 10, marginBottom: 16 }}>
            {managePlan.tasks?.map((task: any) => {
              const done = task.status === "done";
              return (
                <Pressable
                  key={task.id}
                  onPress={() => handleToggleTask(task)}
                  style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.card, borderRadius: 12, padding: 16, borderWidth: 1, borderColor: done ? theme.emerald + '40' : theme.line }}
                >
                  <View style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: done ? theme.emerald : 'transparent', borderWidth: done ? 0 : 2, borderColor: theme.muted, alignItems: 'center', justifyContent: 'center', marginRight: 14 }}>
                    {done && <Feather name="check" size={16} color="white" />}
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.bodyStrong, { textDecorationLine: done ? 'line-through' : 'none', color: done ? theme.muted : theme.text }]}>{task.title}</Text>
                    {task.due_date && <Text style={[styles.mutedText, { fontSize: 12, marginTop: 2 }]}>Échéance : {new Date(task.due_date).toLocaleDateString('fr-FR')}</Text>}
                  </View>
                  {done && <Feather name="check-circle" size={18} color={theme.emerald} />}
                </Pressable>
              );
            })}
          </View>

          {/* Add Task */}
          <Card ui={ui}>
            <Text style={[styles.bodyStrong, { marginBottom: 10 }]}>Ajouter une tâche</Text>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <TextInput
                style={{ flex: 1, backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8, fontSize: 14 }}
                placeholder="Titre de la tâche..."
                placeholderTextColor={theme.muted}
                value={newTaskTitle}
                onChangeText={setNewTaskTitle}
              />
              <Pressable onPress={handleAddTask} style={{ backgroundColor: theme.sky, padding: 12, borderRadius: 8, justifyContent: 'center' }}>
                {taskSubmitting ? <ActivityIndicator color="white" size="small" /> : <Feather name="plus" size={20} color="white" />}
              </Pressable>
            </View>
          </Card>
        </ScrollView>
      </View>
    );
  }

  // ── LIST VIEW ────────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1 }}>
      <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>

        {/* Header */}
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <View>
            <Text style={[styles.heroTitle, { fontSize: 22 }]}>Plans d'intégration</Text>
            <Text style={[styles.mutedText, { marginTop: 2 }]}>{filteredPlans.length} plan{filteredPlans.length !== 1 ? 's' : ''} {activeTab === 'ongoing' ? 'en cours' : 'terminés'}</Text>
          </View>
          {isRh && (
            <Pressable onPress={() => setShowCreateModal(true)} style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.sky, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10 }}>
              <Feather name="plus" size={16} color="white" style={{ marginRight: 6 }} />
              <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 13 }}>Nouveau</Text>
            </Pressable>
          )}
        </View>

        {/* Tabs */}
        <View style={{ flexDirection: 'row', backgroundColor: theme.surfaceAlt, borderRadius: 10, padding: 4, marginBottom: 20 }}>
          {(['ongoing', 'history'] as const).map(tab => (
            <Pressable
              key={tab}
              onPress={() => setActiveTab(tab)}
              style={{ flex: 1, paddingVertical: 10, alignItems: 'center', backgroundColor: activeTab === tab ? theme.card : 'transparent', borderRadius: 8 }}
            >
              <Text style={{ fontWeight: activeTab === tab ? '700' : '400', color: activeTab === tab ? theme.sky : theme.muted, fontSize: 14 }}>
                {tab === 'ongoing' ? 'En cours' : 'Historique'}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Content */}
        {loading ? (
          <ActivityIndicator color={theme.sky} style={{ marginVertical: 40 }} />
        ) : filteredPlans.length === 0 ? (
          <View style={{ alignItems: 'center', paddingVertical: 60 }}>
            <View style={{ width: 64, height: 64, borderRadius: 32, backgroundColor: theme.surfaceAlt, alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
              <Feather name="inbox" size={28} color={theme.muted} />
            </View>
            <Text style={[styles.bodyStrong, { textAlign: 'center', marginBottom: 6 }]}>Aucun plan {activeTab === 'ongoing' ? 'en cours' : 'dans l\'historique'}</Text>
            <Text style={[styles.mutedText, { textAlign: 'center' }]}>
              {isRh ? "Créez un plan d'intégration pour un collaborateur." : "Aucun plan d'intégration pour votre équipe."}
            </Text>
          </View>
        ) : (
          <View style={{ gap: 14 }}>
            {filteredPlans.map(plan => {
              const total = plan.tasks?.length || 0;
              const done = plan.tasks?.filter((t: any) => t.status === "done").length || 0;
              const progress = total > 0 ? Math.round((done / total) * 100) : 0;
              const isComplete = plan.status === 'completed' || progress === 100;

              return (
                <Pressable key={plan.id} onPress={() => setManagePlan(plan)}>
                  <Card ui={ui} style={{ padding: 0, overflow: 'hidden' }}>
                    {/* Color strip */}
                    <View style={{ height: 4, backgroundColor: isComplete ? theme.emerald : theme.sky }} />

                    <View style={{ padding: 16 }}>
                      {/* Top row */}
                      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 14 }}>
                        <View style={{ width: 46, height: 46, borderRadius: 23, backgroundColor: isComplete ? theme.emeraldSoft : theme.skySoft, alignItems: 'center', justifyContent: 'center', marginRight: 12 }}>
                          <Text style={{ fontWeight: 'bold', fontSize: 16, color: isComplete ? theme.emerald : theme.sky }}>{getPlanInitials(plan)}</Text>
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.bodyStrong, { fontSize: 15 }]}>{plan.employee_prenom} {plan.employee_nom}</Text>
                          <Text style={[styles.mutedText, { fontSize: 12, marginTop: 2 }]}>{plan.plan_type?.replace('_', ' ')} • {plan.employee_role}</Text>
                        </View>
                        <View style={{ backgroundColor: isComplete ? theme.emeraldSoft : theme.skySoft, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                          <Text style={{ color: isComplete ? theme.emerald : theme.sky, fontWeight: 'bold', fontSize: 12 }}>
                            {isComplete ? 'Terminé' : 'En cours'}
                          </Text>
                        </View>
                      </View>

                      {/* Progress bar */}
                      <View style={{ backgroundColor: theme.line, borderRadius: 4, height: 6, marginBottom: 8 }}>
                        <View style={{ backgroundColor: isComplete ? theme.emerald : theme.sky, borderRadius: 4, height: 6, width: `${progress}%` as any }} />
                      </View>

                      {/* Bottom row */}
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={[styles.mutedText, { fontSize: 12 }]}>
                          {new Date(plan.start_date).toLocaleDateString('fr-FR')} → {new Date(plan.end_date).toLocaleDateString('fr-FR')}
                        </Text>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                          <Text style={[styles.mutedText, { fontSize: 12 }]}>{done}/{total} tâches</Text>
                          {isRh && activeTab === 'ongoing' && (
                            <Pressable
                              onPress={(e) => { e.stopPropagation?.(); handleDeletePlan(plan.id); }}
                              style={{ padding: 6 }}
                            >
                              <Feather name="trash-2" size={15} color={theme.rose} />
                            </Pressable>
                          )}
                          <Feather name="chevron-right" size={16} color={theme.muted} />
                        </View>
                      </View>
                    </View>
                  </Card>
                </Pressable>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* CREATE MODAL */}
      <Modal visible={showCreateModal} animationType="slide" transparent>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.card, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, paddingBottom: 40 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <Text style={[styles.heroTitle, { fontSize: 20 }]}>Nouveau plan d'intégration</Text>
              <Pressable onPress={() => setShowCreateModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>

            <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Collaborateur *</Text>
            <ScrollView style={{ maxHeight: 130, borderColor: theme.line, borderWidth: 1, borderRadius: 10, marginBottom: 16 }}>
              {employees.filter(e => e.user_id != null).map(emp => (
                <Pressable
                  key={emp.id}
                  onPress={() => setSelectedEmpId(emp.user_id)}
                  style={{ flexDirection: 'row', alignItems: 'center', padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line, backgroundColor: selectedEmpId === emp.user_id ? theme.skySoft : 'transparent' }}
                >
                  <View style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: theme.surfaceAlt, alignItems: 'center', justifyContent: 'center', marginRight: 10 }}>
                    <Text style={{ fontSize: 12, fontWeight: 'bold', color: theme.text }}>{emp.user?.prenom?.[0]}{emp.user?.nom?.[0]}</Text>
                  </View>
                  <Text style={{ color: selectedEmpId === emp.user_id ? theme.sky : theme.text, fontWeight: selectedEmpId === emp.user_id ? '600' : '400' }}>
                    {emp.user?.prenom} {emp.user?.nom} — {emp.position?.title || 'Employé'}
                  </Text>
                </Pressable>
              ))}
            </ScrollView>

            <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Type de plan *</Text>
            <View style={{ flexDirection: 'row', gap: 8, marginBottom: 16 }}>
              {[{ v: '7_days', l: '7 jours' }, { v: '30_days', l: '30 jours' }, { v: '90_days', l: '90 jours' }].map(({ v, l }) => (
                <Pressable key={v} onPress={() => setPlanType(v)} style={{ flex: 1, padding: 10, borderRadius: 8, borderWidth: 1.5, borderColor: planType === v ? theme.sky : theme.line, alignItems: 'center', backgroundColor: planType === v ? theme.skySoft : 'transparent' }}>
                  <Text style={{ color: planType === v ? theme.sky : theme.text, fontWeight: planType === v ? '700' : '400', fontSize: 13 }}>{l}</Text>
                </Pressable>
              ))}
            </View>

            <View style={{ flexDirection: 'row', gap: 12, marginBottom: 20 }}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 6 }]}>Date début *</Text>
                <Pressable onPress={() => setShowStartPicker(true)} style={{ borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8, backgroundColor: theme.background }}>
                  <Text style={{ color: startDate ? theme.text : theme.muted, fontSize: 14 }}>{startDate || "jj/mm/aaaa"}</Text>
                </Pressable>
                {showStartPicker && (
                  Platform.OS === 'ios' ? (
                    <Modal transparent animationType="slide">
                      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.4)' }}>
                        <View style={{ backgroundColor: 'white', padding: 20, paddingBottom: 40 }}>
                          <Pressable onPress={() => setShowStartPicker(false)} style={{ alignItems: 'flex-end', marginBottom: 10 }}>
                            <Text style={{ color: theme.sky, fontWeight: 'bold' }}>Terminé</Text>
                          </Pressable>
                          <DateTimePicker themeVariant="light" textColor="#000000" value={startDate ? new Date(startDate) : new Date()} mode="date" display="spinner" onChange={onChangeDate(setStartDate, setShowStartPicker)} />
                        </View>
                      </View>
                    </Modal>
                  ) : <DateTimePicker themeVariant="light" textColor="#000000"  value={startDate ? new Date(startDate) : new Date()} mode="date" display="default" onChange={onChangeDate(setStartDate, setShowStartPicker)} />
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 6 }]}>Date fin *</Text>
                <Pressable onPress={() => setShowEndPicker(true)} style={{ borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8, backgroundColor: theme.background }}>
                  <Text style={{ color: endDate ? theme.text : theme.muted, fontSize: 14 }}>{endDate || "jj/mm/aaaa"}</Text>
                </Pressable>
                {showEndPicker && (
                  Platform.OS === 'ios' ? (
                    <Modal transparent animationType="slide">
                      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.4)' }}>
                        <View style={{ backgroundColor: 'white', padding: 20, paddingBottom: 40 }}>
                          <Pressable onPress={() => setShowEndPicker(false)} style={{ alignItems: 'flex-end', marginBottom: 10 }}>
                            <Text style={{ color: theme.sky, fontWeight: 'bold' }}>Terminé</Text>
                          </Pressable>
                          <DateTimePicker themeVariant="light" textColor="#000000" value={endDate ? new Date(endDate) : new Date()} mode="date" display="spinner" onChange={onChangeDate(setEndDate, setShowEndPicker)} />
                        </View>
                      </View>
                    </Modal>
                  ) : <DateTimePicker themeVariant="light" textColor="#000000"  value={endDate ? new Date(endDate) : new Date()} mode="date" display="default" onChange={onChangeDate(setEndDate, setShowEndPicker)} />
                )}
              </View>
            </View>

            <PrimaryButton label={submitting ? "Création..." : "Créer le plan"} icon="check" onPress={handleCreatePlan} ui={ui} />
          </View>
        </View>
      </Modal>
    </View>
  );
}
