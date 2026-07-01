

import React, { useState, useEffect } from "react";
import { View, Text, TextInput, ScrollView, Pressable, ActivityIndicator, Modal } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { Chip, StatusBadge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { ProgressBar } from "../components/Shared";
import { Ui, EmployeeProfile, FeatherName, ViewId } from "../types";
import { isRhRole } from "../lib/auth";
import { fetchTeamMembers } from "../services/dashboard.service";
import { managerService } from "../services/manager.service";
import { leavesService } from "../services/leaves.service";
import DateTimePicker from '@react-native-community/datetimepicker';

export function ManagerTeamScreen({ sessionProfile, ui, onNavigate, onSelectEmployee }: { sessionProfile: EmployeeProfile; ui: Ui; onNavigate: (view: ViewId) => void; onSelectEmployee: (id: number) => void }) {
  const { styles, theme } = ui;
  const roleId = sessionProfile.roleId ?? sessionProfile.role;
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("Tous");
  const filters = ["Tous", "À risque", "En congé"];

  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const isRh = isRhRole(roleId);
    const { fetchTeamAbsences } = require("../services/dashboard.service");
    Promise.all([
      fetchTeamMembers(),
      require("../services/ml.service").mlService.fetchTurnoverPredictions().catch(() => null),
      fetchTeamAbsences(isRh).catch(() => [])
    ])
      .then(([membersData, mlData, absencesData]) => {
        const predictionsMap = new Map();
        if (mlData && mlData.predictions) {
          mlData.predictions.forEach((p: any) => predictionsMap.set(p.employee_id, p));
        }

        const absencesCountMap = new Map();
        if (absencesData) {
          absencesData.forEach((leave: any) => {
            if (leave.status === "approved" || leave.status === "pending") {
              const empId = leave.employee_id;
              absencesCountMap.set(empId, (absencesCountMap.get(empId) || 0) + 1);
            }
          });
        }

        const mapped = membersData?.map((emp: any) => {
          const pred = predictionsMap.get(emp.id);
          let engagement = "En attente d'IA";
          if (pred) {
            engagement = pred.risk_level === "High" ? "Critique" : pred.risk_level === "Medium" ? "Moyen" : "Stable";
          }
          return {
            id: emp.id,
            name: emp.user ? `${emp.user.prenom} ${emp.user.nom}` : "Employé",
            role: emp.position?.title || "Non renseigné",
            department: emp.department?.name || "Non renseigné",
            status: emp.status === "active" ? "En poste" : emp.status === "on_leave" ? "En congé" : "Inactif",
            engagement: engagement,
            absences: absencesCountMap.get(emp.id) || 0,
            avatarInitials: emp.user ? `${emp.user.prenom[0] || ""}${emp.user.nom[0] || ""}` : "U",
            email: emp.user?.email || ""
          };
        });
        setTeamMembers(mapped);
      })
      .catch(err => console.log("Erreur chargement équipe", err))
      .finally(() => setLoading(false));
  }, [roleId]);

  const filteredMembers = teamMembers?.filter((member) => {
    const matchesFilter = filter === "Tous" || member.status === filter;
    const text = `${member.name} ${member.role} ${member.department}`.toLowerCase();
    return matchesFilter && text.includes(search.toLowerCase());
  });

  return (
    <View style={styles.stack}>
      <SectionHeader icon="users" title={isRhRole(roleId) ? "Collaborateurs RH" : "Mon équipe"} ui={ui} />
      {loading && <Text style={[styles.bodyText, { textAlign: "center", marginVertical: 20 }]}>Chargement de l'équipe...</Text>}
      <Card ui={ui}>
        <View style={styles.rowBetween}>
          <View style={styles.flex1}>
            <Text style={styles.cardTitle}>{isRhRole(roleId) ? "Base RH mobile" : "Équipe suivie"}</Text>
            <Text style={styles.mutedText}>{filteredMembers.length} collaborateurs visibles</Text>
          </View>
          <StatusBadge label={isRhRole(roleId) ? "RH" : "Manager"} tone="info" ui={ui} />
        </View>
        <View style={styles.fieldBlock}>
          <TextInput
            placeholder="Rechercher par nom, poste, département…"
            placeholderTextColor={theme.muted}
            style={styles.fieldInput}
            value={search}
            onChangeText={setSearch}
          />
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.chipWrap}>
            {filters?.map((item) => (
              <Chip key={item} active={item === filter} label={item} onPress={() => setFilter(item)} ui={ui} />
            ))}
          </View>
        </ScrollView>
      </Card>
      <Card ui={ui} style={{ padding: 0, overflow: 'hidden', marginTop: 16 }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={{ minWidth: 650 }}>
            {/* Table Header */}
            <View style={{ flexDirection: 'row', padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line, backgroundColor: theme.surfaceAlt }}>
              <Text style={{ flex: 2, color: theme.muted, fontWeight: 'bold', fontSize: 13 }}>Employé</Text>
              <Text style={{ flex: 2, color: theme.muted, fontWeight: 'bold', fontSize: 13 }}>Poste</Text>
              <Text style={{ flex: 3, color: theme.muted, fontWeight: 'bold', fontSize: 13 }}>Email</Text>
              <Text style={{ flex: 1, color: theme.muted, fontWeight: 'bold', fontSize: 13, textAlign: 'right' }}>Statut</Text>
            </View>
            
            {/* Table Rows */}
            {filteredMembers?.length === 0 ? (
              <View style={{ padding: 24, alignItems: 'center' }}>
                <Text style={{ color: theme.muted }}>Aucun employé trouvé.</Text>
              </View>
            ) : (
              filteredMembers?.map((member, index) => (
                <Pressable 
                  key={member.id} 
                  onPress={() => onSelectEmployee(member.id)}
                  style={({ pressed }) => [
                    {
                      flexDirection: 'row', 
                      padding: 16, 
                      borderBottomWidth: index === filteredMembers.length - 1 ? 0 : 1, 
                      borderBottomColor: theme.line,
                      alignItems: 'center',
                      backgroundColor: pressed ? theme.surfaceAlt : 'transparent'
                    }
                  ]}
                >
                  <Text style={{ flex: 2, color: theme.text, fontWeight: 'bold', fontSize: 14 }}>{member.name}</Text>
                  <Text style={{ flex: 2, color: theme.muted, fontSize: 14 }}>{member.role}</Text>
                  <Text style={{ flex: 3, color: theme.muted, fontSize: 14 }}>{member.email || "Non renseigné"}</Text>
                  <View style={{ flex: 1, alignItems: 'flex-end' }}>
                    <StatusBadge label={member.status} tone={member.status === "Alerte active" ? "critical" : member.status === "Onboarding" ? "warning" : member.status === "Inactif" ? "neutral" : "success"} ui={ui} />
                  </View>
                </Pressable>
              ))
            )}
          </View>
        </ScrollView>
      </Card>

    </View>
  );
}

export function ManagerTasksScreen({ sessionProfile, ui }: { sessionProfile: EmployeeProfile; ui: Ui }) {
  const { styles, theme } = ui;
  const roleId = sessionProfile.roleId ?? sessionProfile.role;
  const isRh = isRhRole(roleId);

  const [tasks, setTasks] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const [tab, setTab] = useState<'Toutes les tâches' | 'Non terminées' | 'Deadlines dépassées'>('Toutes les tâches');
  const [memberFilter, setMemberFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formTask, setFormTask] = useState<any>({ title: '', description: '', assigned_to: '', priority: 'medium', status: 'todo', due_date: '' });
  const [submitting, setSubmitting] = useState(false);
  const [showAssignDropdown, setShowAssignDropdown] = useState(false);
  const [showPriorityDropdown, setShowPriorityDropdown] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  const [showMemberFilterDropdown, setShowMemberFilterDropdown] = useState(false);
  const [showStatusFilterDropdown, setShowStatusFilterDropdown] = useState(false);

  const priorityOptions = [
    { value: 'low', label: 'Basse', color: theme.emerald },
    { value: 'medium', label: 'Moyenne', color: '#4F46E5' },
    { value: 'high', label: 'Haute', color: '#F97316' },
    { value: 'urgent', label: 'Urgente', color: theme.rose }
  ];

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, membersData] = await Promise.all([
        managerService.fetchTasksStats(),
        fetchTeamMembers()
      ]);
      setStats(statsData);
      setTeamMembers(membersData || []);
      
      await loadTasksList();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTasksList = async () => {
    try {
      setLoading(true);
      
      let overdue = tab === 'Deadlines dépassées' ? true : undefined;
      let statusParams = statusFilter;
      
      const tasksData = await managerService.fetchTasks(
        statusFilter === 'all' ? undefined : statusFilter,
        memberFilter === 'all' ? undefined : parseInt(memberFilter),
        overdue
      );
      
      let filtered = tasksData;
      if (tab === 'Non terminées') {
        filtered = filtered.filter((t: any) => t.status !== 'done' && t.status !== 'cancelled');
      }
      
      setTasks(filtered || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [isRh]);

  useEffect(() => {
    loadTasksList();
  }, [tab, memberFilter, statusFilter]);

  const handleCreateTask = async () => {
    if (!formTask.title || !formTask.assigned_to) {
      alert("Veuillez remplir le titre et sélectionner un membre.");
      return;
    }
    try {
      setSubmitting(true);
      await managerService.createTask(formTask);
      setIsModalOpen(false);
      setFormTask({ title: '', description: '', assigned_to: '', priority: 'medium', status: 'todo', due_date: '' });
      loadData();
    } catch (err: any) {
      alert("Erreur lors de la création.");
    } finally {
      setSubmitting(false);
    }
  };

  const updateTaskStatus = async (taskId: number, newStatus: string) => {
    try {
      await managerService.updateTask(taskId, { status: newStatus });
      loadTasksList();
      managerService.fetchTasksStats().then(setStats);
    } catch (e) {
      console.error("Error updating status", e);
    }
  };
  
  const deleteTask = async (taskId: number) => {
    try {
      await managerService.deleteTask(taskId);
      loadTasksList();
      managerService.fetchTasksStats().then(setStats);
    } catch (e) {
      console.error("Error deleting task", e);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch(priority) {
      case 'urgent': return { label: 'URGENTE', tone: 'critical' };
      case 'high': return { label: 'HAUTE', tone: 'warning' };
      case 'low': return { label: 'BASSE', tone: 'info' };
      default: return { label: 'MOYENNE', tone: 'info' };
    }
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'done': return { label: 'Terminée', tone: 'success' };
      case 'in_progress': return { label: 'En cours', tone: 'info' };
      case 'todo': return { label: 'À faire', tone: 'neutral' };
      case 'cancelled': return { label: 'Annulée', tone: 'critical' };
      default: return { label: status, tone: 'neutral' };
    }
  };

  return (
    <View style={styles.stack}>
      {/* KPI Cards */}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 16, marginBottom: 8 }}>
        <Card ui={ui} style={{ flex: 1, minWidth: 150, padding: 16 }}>
          <View style={[styles.rowBetween, { alignItems: 'flex-start' }]}>
            <Text style={[styles.bodyStrong, { color: theme.muted, fontSize: 13 }]}>TOTAL TÂCHES</Text>
            <Feather name="check-square" size={18} color={theme.sky} />
          </View>
          <Text style={[styles.heroTitle, { marginTop: 8, color: theme.sky }]}>{stats?.total || 0}</Text>
        </Card>
        <Card ui={ui} style={{ flex: 1, minWidth: 150, padding: 16 }}>
          <View style={[styles.rowBetween, { alignItems: 'flex-start' }]}>
            <Text style={[styles.bodyStrong, { color: theme.muted, fontSize: 13 }]}>NON TERMINÉES</Text>
            <Feather name="clock" size={18} color={theme.amber} />
          </View>
          <Text style={[styles.heroTitle, { marginTop: 8, color: theme.amber }]}>{stats?.not_done || 0}</Text>
        </Card>
        <Card ui={ui} style={{ flex: 1, minWidth: 150, padding: 16 }}>
          <View style={[styles.rowBetween, { alignItems: 'flex-start' }]}>
            <Text style={[styles.bodyStrong, { color: theme.muted, fontSize: 13 }]}>DEADLINES DÉPASSÉES</Text>
            <Feather name="alert-triangle" size={18} color={theme.rose} />
          </View>
          <Text style={[styles.heroTitle, { marginTop: 8, color: theme.rose }]}>{stats?.overdue || 0}</Text>
        </Card>
        <Card ui={ui} style={{ flex: 1, minWidth: 150, padding: 16 }}>
          <View style={[styles.rowBetween, { alignItems: 'flex-start' }]}>
            <Text style={[styles.bodyStrong, { color: theme.muted, fontSize: 13 }]}>TERMINÉES</Text>
            <Feather name="check" size={18} color={theme.emerald} />
          </View>
          <Text style={[styles.heroTitle, { marginTop: 8, color: theme.emerald }]}>{stats?.done || 0}</Text>
        </Card>
      </View>

      {/* Tabs */}
      <View style={{ borderBottomWidth: 1, borderBottomColor: theme.line, marginBottom: 16 }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 24, paddingRight: 20 }}>
          {(['Toutes les tâches', 'Non terminées', 'Deadlines dépassées'] as const).map((t) => (
            <Pressable key={t} onPress={() => setTab(t)} style={{ paddingVertical: 12, borderBottomWidth: 2, borderBottomColor: tab === t ? theme.sky : 'transparent' }}>
              <View style={styles.rowStart}>
                {t === 'Toutes les tâches' && <Feather name="check-square" size={16} color={tab === t ? theme.sky : theme.muted} style={{ marginRight: 6 }} />}
                {t === 'Non terminées' && <Feather name="clock" size={16} color={tab === t ? theme.sky : theme.muted} style={{ marginRight: 6 }} />}
                {t === 'Deadlines dépassées' && <Feather name="alert-triangle" size={16} color={tab === t ? theme.sky : theme.muted} style={{ marginRight: 6 }} />}
                <Text style={{ color: tab === t ? theme.sky : theme.muted, fontWeight: 'bold' }}>{t}</Text>
                {t === 'Non terminées' && stats?.not_done > 0 && (
                  <View style={{ backgroundColor: theme.amberSoft, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 12, marginLeft: 8 }}>
                    <Text style={{ color: theme.amber, fontSize: 12, fontWeight: 'bold' }}>{stats.not_done}</Text>
                  </View>
                )}
                {t === 'Deadlines dépassées' && stats?.overdue > 0 && (
                  <View style={{ backgroundColor: theme.roseSoft, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 12, marginLeft: 8 }}>
                    <Text style={{ color: theme.rose, fontSize: 12, fontWeight: 'bold' }}>{stats.overdue}</Text>
                  </View>
                )}
              </View>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      {/* Filters and Action */}
      <View style={[styles.rowBetween, { flexWrap: 'wrap', gap: 12, marginBottom: 16, zIndex: 100 }]}>
        <View style={[styles.rowStart, { zIndex: 100 }]}>
          <Feather name="filter" size={18} color={theme.muted} style={{ marginRight: 12 }} />
          
          {/* Filtre Membres */}
          <View style={{ position: 'relative', zIndex: 110, marginRight: 8 }}>
            <Pressable
              onPress={() => { setShowMemberFilterDropdown(!showMemberFilterDropdown); setShowStatusFilterDropdown(false); }}
              style={{ borderWidth: 1, borderColor: theme.line, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: theme.card }}
            >
              <Text style={{ color: theme.text, fontSize: 14 }}>
                {memberFilter === 'all' 
                  ? 'Tous les membres' 
                  : (teamMembers.find(m => (m.user?.id || m.id) === parseInt(memberFilter))?.user?.prenom || teamMembers.find(m => (m.user?.id || m.id) === parseInt(memberFilter))?.name || 'Sélectionné')} ▾
              </Text>
            </Pressable>
            {showMemberFilterDropdown && (
              <ScrollView style={{ position: 'absolute', top: 35, left: 0, minWidth: 150, maxHeight: 200, backgroundColor: theme.card, borderRadius: 6, borderWidth: 1, borderColor: theme.line, elevation: 5, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, zIndex: 120 }}>
                <Pressable
                  onPress={() => { setMemberFilter('all'); setShowMemberFilterDropdown(false); }}
              style={{ padding: 10, borderBottomWidth: 1, borderBottomColor: theme.line, backgroundColor: memberFilter === 'all' ? theme.skySoft : 'transparent' }}
                >
                  <Text style={{ color: memberFilter === 'all' ? theme.sky : theme.text, fontWeight: memberFilter === 'all' ? 'bold' : 'normal' }}>Tous les membres</Text>
                </Pressable>
                {teamMembers.map(emp => {
                  const empId = emp.user?.id || emp.id;
                  const empName = emp.user ? `${emp.user.prenom} ${emp.user.nom}` : emp.name;
                  const isSelected = memberFilter === empId.toString();
                  return (
                    <Pressable
                      key={empId}
                      onPress={() => { setMemberFilter(empId.toString()); setShowMemberFilterDropdown(false); }}
              style={{ padding: 10, borderBottomWidth: 1, borderBottomColor: theme.line, backgroundColor: isSelected ? theme.skySoft : 'transparent' }}
                    >
                      <Text style={{ color: isSelected ? theme.sky : theme.text, fontWeight: isSelected ? 'bold' : 'normal' }}>{empName}</Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            )}
          </View>

          {/* Filtre Statut */}
          <View style={{ position: 'relative', zIndex: 100 }}>
            <Pressable
              onPress={() => { setShowStatusFilterDropdown(!showStatusFilterDropdown); setShowMemberFilterDropdown(false); }}
              style={{ borderWidth: 1, borderColor: theme.line, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: theme.card }}
            >
              <Text style={{ color: theme.text, fontSize: 14 }}>
                {statusFilter === 'all' ? 'Tous les statuts' : 
                 statusFilter === 'todo' ? 'À faire' : 
                 statusFilter === 'in_progress' ? 'En cours' : 
                 statusFilter === 'done' ? 'Terminée' : 
                 statusFilter === 'cancelled' ? 'Annulée' : 'Tous les statuts'} ▾
              </Text>
            </Pressable>
            {showStatusFilterDropdown && (
              <View style={{ position: 'absolute', top: 35, left: 0, minWidth: 150, backgroundColor: theme.card, borderRadius: 6, borderWidth: 1, borderColor: theme.line, elevation: 5, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, zIndex: 110 }}>
                {[
                  { value: 'all', label: 'Tous les statuts' },
                  { value: 'todo', label: 'À faire' },
                  { value: 'in_progress', label: 'En cours' },
                  { value: 'done', label: 'Terminée' },
                  { value: 'cancelled', label: 'Annulée' }
                ].map(opt => (
                  <Pressable
                    key={opt.value}
                    onPress={() => { setStatusFilter(opt.value); setShowStatusFilterDropdown(false); }}
              style={{ padding: 10, borderBottomWidth: 1, borderBottomColor: theme.line, backgroundColor: statusFilter === opt.value ? theme.skySoft : 'transparent' }}
                  >
                    <Text style={{ color: statusFilter === opt.value ? theme.sky : theme.text, fontWeight: statusFilter === opt.value ? 'bold' : 'normal' }}>{opt.label}</Text>
                  </Pressable>
                ))}
              </View>
            )}
          </View>
        </View>
        <PrimaryButton icon="plus" label="Nouvelle tâche" onPress={() => setIsModalOpen(true)} ui={ui} />
      </View>

      {/* Task List */}
      {loading ? (
        <ActivityIndicator color={theme.sky} style={{ marginVertical: 40 }} />
      ) : tasks.length === 0 ? (
        <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 40 }}>
          <Text style={styles.mutedText}>Aucune tâche trouvée pour ce filtre.</Text>
        </Card>
      ) : (
        <View style={styles.stack}>
          {tasks.map(task => {
            const priorityBadge = getPriorityBadge(task.priority);
            const statusBadge = getStatusBadge(task.status);
            
            return (
              <Card key={task.id} ui={ui} style={{ padding: 0, overflow: 'hidden' }}>
                <View style={{ padding: 20 }}>
                  <View style={styles.rowBetween}>
                    <Text style={[styles.heroTitle, { fontSize: 18, marginBottom: 8 }]}>{task.title}</Text>
                    <View style={styles.rowStart}>
                      <Pressable style={{ padding: 8 }}>
                        <Feather name="edit-2" size={16} color={theme.muted} />
                      </Pressable>
                      <Pressable style={{ padding: 8 }} onPress={() => deleteTask(task.id)}>
                        <Feather name="trash-2" size={16} color={theme.muted} />
                      </Pressable>
                    </View>
                  </View>

                  <View style={[styles.rowStart, { marginBottom: 16 }]}>
                    <StatusBadge label={priorityBadge.label} tone={priorityBadge.tone as any} ui={ui} />
                    <View style={{ width: 8 }} />
                    <StatusBadge label={statusBadge.label} tone={statusBadge.tone as any} ui={ui} />
                  </View>

                  <Text style={[styles.bodyText, { marginBottom: 16 }]}>{task.description}</Text>

                  <View style={[styles.rowBetween, { borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 16 }]}>
                    <View style={styles.rowStart}>
                      <Feather name="user" size={14} color={theme.muted} style={{ marginRight: 6 }} />
                      <Text style={[styles.mutedText, { marginRight: 16 }]}>{task.assignee_prenom} {task.assignee_nom}</Text>
                      <Feather name="calendar" size={14} color={theme.muted} style={{ marginRight: 6 }} />
                      <Text style={styles.mutedText}>{task.due_date || 'Non définie'}</Text>
                    </View>
                    
                    {task.status !== 'done' && (
                      <PrimaryButton 
                        label="Marquer terminée" 
                        icon="check" 
                        onPress={() => updateTaskStatus(task.id, 'done')} 
                        ui={ui} 
                      />
                    )}
                  </View>
                </View>
              </Card>
            );
          })}
        </View>
      )}

      {/* Modal Nouvelle Tâche */}
      <Modal visible={isModalOpen} transparent animationType="fade">
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: 20 }}>
          <View style={{ backgroundColor: theme.card, padding: 24, borderRadius: 16, width: '100%', maxWidth: 450 }}>
            {/* Header */}
            <View style={[styles.rowBetween, { marginBottom: 24 }]}>
              <View style={styles.rowStart}>
                <Feather name="plus" size={20} color={theme.text} style={{ marginRight: 8 }} />
                <Text style={{ fontSize: 20, fontWeight: 'bold', color: theme.text }}>Nouvelle tâche</Text>
              </View>
              <Pressable onPress={() => setIsModalOpen(false)}>
                <Feather name="x" size={20} color={theme.text} />
              </Pressable>
            </View>

            {/* Titre */}
            <View style={{ marginBottom: 16 }}>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Titre de la tâche *</Text>
              <TextInput
                placeholder="Ex: Préparer le rapport mensuel"
                placeholderTextColor={theme.muted}
                style={[styles.fieldInput, { backgroundColor: 'transparent', borderRadius: 8, borderWidth: 1, borderColor: theme.line, paddingVertical: 12, paddingHorizontal: 12 }]}
                value={formTask.title}
                onChangeText={(text) => setFormTask({...formTask, title: text})}
              />
            </View>

            {/* Description */}
            <View style={{ marginBottom: 16 }}>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Description (optionnel)</Text>
              <TextInput
                placeholder="Détails de la tâche..."
                placeholderTextColor={theme.muted}
                style={[styles.fieldInput, { backgroundColor: 'transparent', borderRadius: 8, borderWidth: 1, borderColor: theme.line, height: 100, textAlignVertical: 'top', paddingVertical: 12, paddingHorizontal: 12 }]}
                multiline
                value={formTask.description}
                onChangeText={(text) => setFormTask({...formTask, description: text})}
              />
            </View>

            {/* Assigné à / Deadline */}
            <View style={{ flexDirection: 'row', gap: 16, marginBottom: 16, zIndex: 20 }}>
              <View style={{ flex: 1, zIndex: 30 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Assigné à *</Text>
                <Pressable onPress={() => setShowAssignDropdown(!showAssignDropdown)}
                  style={[styles.rowBetween, styles.fieldInput, { backgroundColor: 'transparent', borderRadius: 8, borderWidth: 1, borderColor: theme.line, paddingHorizontal: 12, paddingVertical: 12 }]}>
                  <Text style={{ color: formTask.assigned_to ? theme.text : theme.muted }}>
                    {formTask.assigned_to 
                      ? (teamMembers.find(m => (m.user?.id || m.id) === formTask.assigned_to)?.user?.prenom || teamMembers.find(m => (m.user?.id || m.id) === formTask.assigned_to)?.name || "Sélectionné") 
                      : "-- Choisir un membre --"}
                  </Text>
                  <Feather name={showAssignDropdown ? "chevron-up" : "chevron-down"} size={16} color={theme.text} />
                </Pressable>
                {showAssignDropdown && (
                  <ScrollView style={{ position: 'absolute', top: 76, left: 0, right: 0, maxHeight: 150, backgroundColor: '#ffffff', borderRadius: 8, elevation: 5, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, zIndex: 50 }}>
                    {teamMembers.map(emp => {
                      const empName = emp.user ? `${emp.user.prenom} ${emp.user.nom}` : emp.name;
                      const empId = emp.user?.id || emp.id;
                      const isSelected = formTask.assigned_to === empId;
                      return (
                        <Pressable 
                          key={emp.id} 
                          onPress={() => { setFormTask({...formTask, assigned_to: empId}); setShowAssignDropdown(false); }}
                          style={{ padding: 12, backgroundColor: isSelected ? theme.skySoft : 'transparent', borderBottomWidth: 1, borderBottomColor: theme.line }}
                        >
                          <Text style={{ color: isSelected ? theme.sky : theme.text, fontWeight: isSelected ? 'bold' : 'normal' }}>
                            {empName}
                          </Text>
                        </Pressable>
                      );
                    })}
                  </ScrollView>
                )}
              </View>

              <View style={{ flex: 1 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Deadline</Text>
                <Pressable onPress={() => setShowDatePicker(true)} style={[styles.rowBetween, styles.fieldInput, { backgroundColor: 'transparent', borderRadius: 8, borderWidth: 1, borderColor: theme.line, paddingHorizontal: 12, paddingVertical: 12 }]}>
                  <Text style={{ color: formTask.due_date ? theme.text : theme.muted }}>
                    {formTask.due_date ? new Date(formTask.due_date).toLocaleDateString() : "jj/mm/aaaa"}
                  </Text>
                  <Feather name="calendar" size={16} color={theme.text} />
                </Pressable>
                {showDatePicker && (
                  <DateTimePicker themeVariant="light" textColor="#000000" 
                    value={formTask.due_date ? new Date(formTask.due_date) : new Date()}
                    mode="date"
                    display="default"
                    onChange={(event, selectedDate) => {
                      setShowDatePicker(false);
                      if (selectedDate) {
                        const dateString = selectedDate.toISOString().split('T')[0];
                        setFormTask({...formTask, due_date: dateString});
                      }
                    }}
                  />
                )}
              </View>
            </View>

            {/* Priorité */}
            <View style={{ marginBottom: 24, width: '50%', paddingRight: 8, zIndex: 10 }}>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Priorité</Text>
              <Pressable onPress={() => setShowPriorityDropdown(!showPriorityDropdown)}
                  style={[styles.rowBetween, styles.fieldInput, { backgroundColor: 'transparent', borderRadius: 8, borderWidth: 1, borderColor: theme.line, paddingHorizontal: 12, paddingVertical: 12 }]}>
                <View style={styles.rowStart}>
                  <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: priorityOptions.find(p => p.value === formTask.priority)?.color || '#4F46E5', marginRight: 8 }} />
                  <Text style={{ color: theme.text }}>{priorityOptions.find(p => p.value === formTask.priority)?.label || 'Moyenne'}</Text>
                </View>
                <Feather name={showPriorityDropdown ? "chevron-up" : "chevron-down"} size={16} color={theme.text} />
              </Pressable>
              {showPriorityDropdown && (
                <View style={{ position: 'absolute', top: 76, left: 0, right: 8, backgroundColor: '#ffffff', borderRadius: 8, elevation: 5, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, zIndex: 50 }}>
                  {priorityOptions.map(opt => (
                    <Pressable 
                      key={opt.value} 
                      onPress={() => { setFormTask({...formTask, priority: opt.value as any}); setShowPriorityDropdown(false); }}
                      style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line, flexDirection: 'row', alignItems: 'center' }}
                    >
                      <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: opt.color, marginRight: 8 }} />
                      <Text style={{ color: formTask.priority === opt.value ? theme.sky : theme.text, fontWeight: formTask.priority === opt.value ? 'bold' : 'normal' }}>
                        {opt.label}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>

            {/* Boutons */}
            <View style={[styles.rowStart, { justifyContent: 'flex-end', gap: 12 }]}>
              <Pressable 
                onPress={() => setIsModalOpen(false)}
                style={{ paddingVertical: 12, paddingHorizontal: 20, backgroundColor: '#E5E7EB', borderRadius: 8 }}
              >
                <Text style={{ fontWeight: 'bold', color: '#1F2937' }}>Annuler</Text>
              </Pressable>
              
              <Pressable 
                onPress={handleCreateTask}
                disabled={submitting || !formTask.title || !formTask.assigned_to}
                style={{ paddingVertical: 12, paddingHorizontal: 20, backgroundColor: '#4F46E5', borderRadius: 8, opacity: (submitting || !formTask.title || !formTask.assigned_to) ? 0.5 : 1 }}
              >
                <Text style={{ fontWeight: 'bold', color: '#ffffff' }}>{submitting ? "Création..." : "Créer la tâche"}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

export let globalOffboardingTab: 'En cours' | 'Historique' = 'En cours';
export function setGlobalOffboardingTab(tab: 'En cours' | 'Historique') {
  globalOffboardingTab = tab;
}

export function ManagerOffboardingScreen({ ui, sessionProfile }: { ui: Ui, sessionProfile?: any }) {
  const { styles, theme } = ui;
  const [activeTab, setActiveTab] = useState<'En cours' | 'Historique'>(globalOffboardingTab);
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [employees, setEmployees] = useState<any[]>([]);
  const [formEmployeeId, setFormEmployeeId] = useState("");
  const [formDate, setFormDate] = useState("");
  const [formReason, setFormReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    loadPlans();
    loadEmployees();
  }, []);

  // Update activeTab when globalOffboardingTab changes externally
  React.useEffect(() => {
    setActiveTab(globalOffboardingTab);
  }, [globalOffboardingTab]);

  const handleTabChange = (tab: 'En cours' | 'Historique') => {
    setActiveTab(tab);
    setGlobalOffboardingTab(tab);
  };

  async function loadPlans() {
    try {
      setLoading(true);
      const data = await managerService.fetchOffboardingPlans();
      if (data) setPlans(data);
    } catch (err: any) {
      setError(err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }

  async function loadEmployees() {
    try {
      const data = await fetchTeamMembers();
      if (data) setEmployees(data);
    } catch (err) {
      console.error(err);
    }
  }

  const toggleTask = async (planId: string, taskId: string, currentStatus: string) => {
    try {
      await managerService.toggleTask(taskId, currentStatus);
      loadPlans();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreate = async () => {
    if (!formEmployeeId || !formDate || !formReason) {
      alert("Veuillez remplir tous les champs obligatoires (Collaborateur, Date, Motif).");
      return;
    }
    try {
      setSubmitting(true);
      await managerService.createOffboardingPlan(parseInt(formEmployeeId), formDate, formReason);
      setIsModalOpen(false);
      setFormEmployeeId("");
      setFormDate("");
      setFormReason("");
      loadPlans();
    } catch (err: any) {
      let errorMsg = err.message;
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join('\n');
        } else {
          errorMsg = err.response.data.detail;
        }
      }
      alert("Erreur lors de la création :\n" + errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredPlans = plans.filter(p => activeTab === 'En cours' ? p.status !== 'completed' : p.status === 'completed');
  const getInitials = (plan: any) => ((plan.employee_prenom?.[0] || '') + (plan.employee_nom?.[0] || '')).toUpperCase();

  return (
    <View style={styles.stack}>
      <Card ui={ui} style={{ padding: 16 }}>
        <View style={[styles.rowBetween, { flexWrap: 'wrap', gap: 12 }]}>
          <View style={styles.rowStart}>
            <Feather name="log-out" size={24} color={theme.text} style={{ marginRight: 12 }} />
            <Text style={[styles.heroTitle, { fontSize: 20 }]}>Suivi des Plans de Sortie (Offboarding)</Text>
          </View>
          
          <View style={styles.rowStart}>
            <View style={{ flexDirection: 'row', backgroundColor: theme.surfaceAlt, borderRadius: 8, padding: 4, marginRight: 16 }}>
              <Pressable 
                onPress={() => handleTabChange('En cours')}
                style={{ paddingVertical: 6, paddingHorizontal: 12, backgroundColor: activeTab === 'En cours' ? theme.sky : 'transparent', borderRadius: 6 }}
              >
                <Text style={{ color: activeTab === 'En cours' ? '#fff' : theme.muted, fontWeight: activeTab === 'En cours' ? 'bold' : 'normal', fontSize: 13 }}>En cours</Text>
              </Pressable>
              <Pressable 
                onPress={() => handleTabChange('Historique')}
                style={{ paddingVertical: 6, paddingHorizontal: 12, backgroundColor: activeTab === 'Historique' ? theme.sky : 'transparent', borderRadius: 6 }}
              >
                <Text style={{ color: activeTab === 'Historique' ? '#fff' : theme.muted, fontWeight: activeTab === 'Historique' ? 'bold' : 'normal', fontSize: 13 }}>Historique</Text>
              </Pressable>
            </View>
            
            <Pressable 
              onPress={() => setIsModalOpen(true)}
              style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#6366f1', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 8 }}
            >
              <Feather name="plus-circle" size={16} color="#fff" style={{ marginRight: 8 }} />
              <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 14 }}>Créer un plan de sortie</Text>
            </Pressable>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator color={theme.sky} style={{ marginVertical: 40 }} />
        ) : error ? (
          <Text style={[styles.bodyStrong, { color: theme.rose, textAlign: 'center', marginVertical: 40 }]}>Erreur: {error}</Text>
        ) : filteredPlans.length === 0 ? (
          <View style={{ paddingVertical: 60, alignItems: 'center' }}>
            <Text style={[styles.mutedText, { fontSize: 15 }]}>Aucun plan de sortie {activeTab === 'En cours' ? 'en cours' : "dans l'historique"} pour le moment.</Text>
          </View>
        ) : (
          <View style={{ marginTop: 24 }}>
            {filteredPlans.map(plan => {
              const tasks = plan.tasks || [];
              const completedCount = tasks.filter((t: any) => t.status === "completed").length;
              const progress = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;
              
              return (
                <View key={plan.id} style={{ marginBottom: 24 }}>
                  <AICard ui={ui}>
                    <View style={styles.rowBetween}>
                      <View style={styles.flex1}>
                        <Text style={styles.heroTitle}>Départ prévu : {plan.departure_date}</Text>
                        <Text style={styles.heroText}>Employé : {plan.employee_prenom} {plan.employee_nom}</Text>
                        <Text style={[styles.mutedText, { marginTop: 4 }]}>Motif : {plan.departure_reason || 'Non précisé'}</Text>
                      </View>
                      <StatusBadge label={plan.status} tone={plan.status === "completed" ? "success" : "warning"} ui={ui} />
                    </View>
                    <View style={[styles.rowBetween, { marginTop: 12, marginBottom: 4 }]}>
                      <Text style={styles.metaText}>Progression de la checklist</Text>
                      <Text style={styles.bodyStrong}>{progress}%</Text>
                    </View>
                    <ProgressBar value={progress} ui={ui} />
                  </AICard>

                  <Text style={[styles.bodyStrong, { marginTop: 16, marginBottom: 8 }]}>Checklist Manager</Text>
                  {tasks.length === 0 && <Text style={styles.mutedText}>Aucune tâche assignée.</Text>}
                  {tasks.map((task: any) => {
                    const isCompleted = task.status === "completed";
                    return (
                      <Pressable key={task.id} onPress={() => toggleTask(plan.id, task.id, task.status)} style={[styles.documentRow, isCompleted && { opacity: 0.6 }]}>
                        <View style={[styles.actionIcon, { backgroundColor: isCompleted ? theme.emeraldSoft : theme.surfaceAlt }]}>
                          <Feather name={isCompleted ? "check" : "circle"} size={18} color={isCompleted ? theme.emerald : theme.muted} />
                        </View>
                        <View style={styles.flex1}>
                          <Text style={[styles.bodyStrong, isCompleted && { textDecorationLine: "line-through", color: theme.muted }]}>{task.title}</Text>
                          <Text style={styles.mutedText}>{task.description}</Text>
                        </View>
                      </Pressable>
                    );
                  })}
                </View>
              );
            })}
          </View>
        )}
      </Card>

      <Modal visible={isModalOpen} transparent animationType="fade">
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: 20 }}>
          <View style={{ backgroundColor: theme.card, padding: 24, borderRadius: 16, width: '100%', maxWidth: 500 }}>
            <View style={[styles.rowBetween, { marginBottom: 20 }]}>
              <Text style={styles.heroTitle}>Nouveau Plan de Sortie</Text>
              <Pressable onPress={() => setIsModalOpen(false)}>
                <Feather name="x" size={24} color={theme.muted} />
              </Pressable>
            </View>

            <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Collaborateur sur le départ *</Text>
            <View style={[styles.fieldBlock, { zIndex: 10 }]}>
              <ScrollView style={{ maxHeight: 120, borderWidth: 1, borderColor: theme.line, borderRadius: 8, marginBottom: 16 }}>
                {employees.map(emp => {
                  const empName = emp.user ? `${emp.user.prenom} ${emp.user.nom}` : emp.name;
                  const empId = (emp.user_id || emp.id).toString();
                  const isSelected = formEmployeeId === empId;
                  return (
                    <Pressable 
                      key={emp.id} 
                      onPress={() => setFormEmployeeId(empId)}
                      style={{ padding: 12, backgroundColor: isSelected ? theme.skySoft : 'transparent', borderBottomWidth: 1, borderBottomColor: theme.line }}
                    >
                      <Text style={{ color: isSelected ? theme.sky : theme.text, fontWeight: isSelected ? 'bold' : 'normal' }}>
                        {empName}
                      </Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>

            <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Date de départ prévue *</Text>
            <View style={styles.fieldBlock}>
              <TextInput
                placeholder="YYYY-MM-DD"
                placeholderTextColor={theme.muted}
                style={styles.fieldInput}
                value={formDate}
                onChangeText={setFormDate}
              />
            </View>

            <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Motif du départ *</Text>
            <View style={styles.fieldBlock}>
              <TextInput
                placeholder="Ex: Fin de contrat, Démission, Retraite..."
                placeholderTextColor={theme.muted}
                style={styles.fieldInput}
                value={formReason}
                onChangeText={setFormReason}
              />
            </View>

            <View style={[styles.rowBetween, { marginTop: 12 }]}>
              <View style={{ flex: 1, marginRight: 8 }}>
                <SecondaryButton label="Annuler" icon="x" onPress={() => setIsModalOpen(false)} ui={ui} />
              </View>
              <View style={{ flex: 1, marginLeft: 8 }}>
                <PrimaryButton 
                  label={submitting ? "Création..." : "Créer le plan"} 
                  icon="check"
                  onPress={handleCreate} 
                  ui={ui} 
                  disabled={submitting || !formEmployeeId || !formDate || !formReason} 
                />
              </View>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
export function ManagerEmployeeDetailScreen({ employeeId, ui, sessionProfile }: { employeeId: number; ui: any;  sessionProfile?: any }) {
  const [detail, setDetail] = React.useState<any>(null);
  const [actionLoading, setActionLoading] = React.useState(false);
  const [rhMessage, setRhMessage] = React.useState("");
  
  const isRh = sessionProfile?.roleId === "rh" || sessionProfile?.role === "rh";

  React.useEffect(() => {
    const fetchDetail = async () => {
      try {
        const { fetchEmployeeDetail } = require("../services/manager.service");
        const data = await fetchEmployeeDetail(employeeId);
        setDetail(data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchDetail();
  }, [employeeId]);

  const handleCreateContract = async () => {
    setActionLoading(true);
    setRhMessage("");
    try {
      const { createContract } = require("../services/rh.service");
      await createContract({
        user_id: employeeId,
        contract_type: "CDI",
        start_date: new Date().toISOString().split("T")[0],
        position: detail.position || "Employé",
        salary: "35000€"
      });
      setRhMessage("Contrat CDI créé avec succès !");
    } catch (e: any) {
      setRhMessage("Erreur création contrat: " + e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUploadDocument = async () => {
    setActionLoading(true);
    setRhMessage("");
    try {
      const { uploadDocument } = require("../services/rh.service");
      await uploadDocument({
        title: "Fiche de paie",
        document_type: "Fiche de paie",
        file_path: `/documents/payslip_${employeeId}_${Date.now()}.pdf`
      });
      setRhMessage("Document uploadé avec succès !");
    } catch (e: any) {
      setRhMessage("Erreur upload document: " + e.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (!detail) return <View style={[ui.styles.stack, {flex: 1, justifyContent: "center"}]}><ActivityIndicator color={ui.theme.sky} size="large" /></View>;

  return (
    <ScrollView style={ui.styles.stack}>

      <Card ui={ui}>
        <View style={{flexDirection: "row", alignItems: "center", marginBottom: 16}}>
          <View style={[ui.styles.profileAvatar, {width: 64, height: 64, borderRadius: 32}]}>
            <Text style={{fontSize: 24, color: ui.theme.text}}>{detail.prenom?.slice(0, 1)}{detail.nom?.slice(0, 1)}</Text>
          </View>
          <View style={{marginLeft: 16}}>
            <Text style={ui.styles.heroTitle}>{detail.prenom} {detail.nom}</Text>
            <Text style={ui.styles.mutedText}>{detail.position} · {detail.department}</Text>
          </View>
        </View>
        <View style={ui.styles.infoGrid}>
          <Card ui={ui} style={{flex: 1}}>
            <Text style={ui.styles.bodyStrong}>Score Engagement</Text>
            <Text style={ui.styles.progressValue}>{detail.engagement_score != null ? `${detail.engagement_score}%` : "N/A"}</Text>
          </Card>
          <Card ui={ui} style={{flex: 1}}>
            <Text style={ui.styles.bodyStrong}>Risque Départ</Text>
            <Text style={ui.styles.progressValue}>{detail.turnover_risk != null ? `${detail.turnover_risk}%` : "N/A"}</Text>
          </Card>
        </View>
        
        {isRh && (
          <View style={{marginTop: 24, paddingTop: 16, borderTopWidth: 1, borderTopColor: ui.theme.line}}>
            <SectionHeader icon="settings" title="Actions Administratives (RH)" ui={ui} />
            
            {rhMessage ? <Text style={[ui.styles.metaText, {color: ui.theme.sky, marginBottom: 8}]}>{rhMessage}</Text> : null}
            
            <View style={{flexDirection: "row", gap: 8, marginTop: 8}}>
              <View style={{flex: 1}}>
                <PrimaryButton 
                  label={actionLoading ? "En cours..." : "Nouveau Contrat (CDI)"} 
                  icon="file-text" 
                  onPress={handleCreateContract} 
                  ui={ui} 
                  disabled={actionLoading}
                />
              </View>
              <View style={{flex: 1}}>
                <SecondaryButton 
                  label={actionLoading ? "En cours..." : "Ajouter Fiche de paie"} 
                  icon="upload" 
                  onPress={handleUploadDocument} 
                  ui={ui} 
                  disabled={actionLoading}
                />
              </View>
            </View>
          </View>
        )}

        <View style={{marginTop: 16}}>
          <Text style={ui.styles.bodyStrong}>Historique Récent</Text>
          <Text style={ui.styles.bodyText}>{detail.leaves_count} absences récentes.</Text>
        </View>
      </Card>
    </ScrollView>
  );
}

export { ManagerOnboardingScreen } from './HrOnboardingScreen';

export const ManagerHubScreen: React.FC<{
  sessionProfile: any;
  ui: any;
  onNavigate: (view: ViewId) => void;
}> = ({ sessionProfile, ui, onNavigate }) => {
  const { theme, styles } = ui;

  const handleTaskNavigation = () => {
    onNavigate("alerts");
  };

  return (
    <View style={styles.container}>
      <View style={{ marginBottom: 32 }}>
        <Text style={{ fontSize: 14, color: theme.sky, fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Tableau de bord</Text>
        <Text style={styles.heroTitle}>Manager Hub</Text>
        <Text style={styles.bodyText}>Bienvenue dans votre espace manager. Accdez rapidement  vos outils et indicateurs cls.</Text>
      </View>

      <View style={{ gap: 16 }}>
        {/* Active Cards */}
        <Pressable onPress={handleTaskNavigation} style={({ pressed }) => [{ opacity: pressed ? 0.9 : 1, transform: [{ scale: pressed ? 0.98 : 1 }] }]}>
          <View style={{ padding: 24, backgroundColor: theme.skySoft, borderWidth: 1, borderColor: theme.sky + '40', borderRadius: 16 }}>
            <View style={[styles.rowStart, { marginBottom: 12 }]}>
              <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: '#ffffff', alignItems: 'center', justifyContent: 'center', marginRight: 16 }}>
                <Feather name="check-square" size={24} color={theme.sky} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.heroTitle, { fontSize: 20 }]}>Gestion des tches</Text>
                <Text style={[styles.mutedText, { marginTop: 4 }]}>Assignez et suivez les tches de votre quipe.</Text>
              </View>
              <Feather name="chevron-right" size={24} color={theme.sky} />
            </View>
          </View>
        </Pressable>

        <View style={{ gap: 16, marginBottom: 40 }}>
        <Text style={[styles.bodyStrong, { marginTop: 24, marginBottom: 8 }]}>Vos cartes</Text>
        
        <View style={{ flexDirection: 'row', gap: 16, flexWrap: 'wrap' }}>
          <Pressable 
            onPress={() => onNavigate('manager_leaves')}
            style={{ flex: 1, minWidth: 150, padding: 20, backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 16 }}>
            <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: theme.surfaceAlt, alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
              <Feather name="calendar" size={20} color={theme.sky} />
            </View>
            <Text style={[styles.bodyStrong, { marginBottom: 4 }]}>Gestion des Congés</Text>
            <Text style={{ fontSize: 12, color: theme.muted }}>Validation et historique.</Text>
          </Pressable>
          
          <Pressable 
            onPress={() => onNavigate('manager_absences')}
            style={{ flex: 1, minWidth: 150, padding: 20, backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 16 }}>
            <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: theme.surfaceAlt, alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
              <Feather name="clock" size={20} color={theme.sky} />
            </View>
            <Text style={[styles.bodyStrong, { marginBottom: 4 }]}>Gestion des Absences</Text>
            <Text style={{ fontSize: 12, color: theme.muted }}>Déclarations et suivi.</Text>
          </Pressable>

          <Pressable 
            onPress={() => onNavigate('manager_onboarding')}
            style={{ flex: 1, minWidth: 150, padding: 20, backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 16 }}>
            <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: theme.surfaceAlt, alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
              <Feather name="map" size={20} color={theme.sky} />
            </View>
            <Text style={[styles.bodyStrong, { marginBottom: 4 }]}>Plans d'intégration</Text>
            <Text style={{ fontSize: 12, color: theme.muted }}>Suivi de l'onboarding.</Text>
          </Pressable>

          <Pressable
            onPress={() => onNavigate('manager_offboarding')}
            style={{ flex: 1, minWidth: 150, padding: 20, backgroundColor: theme.card, borderWidth: 1, borderColor: '#6366f1' + '40', borderRadius: 16 }}>
            <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: '#6366f115', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
              <Feather name="log-out" size={20} color="#6366f1" />
            </View>
            <Text style={[styles.bodyStrong, { marginBottom: 4 }]}>Offboarding</Text>
            <Text style={{ fontSize: 12, color: theme.muted }}>Suivi des départs.</Text>
          </Pressable>
        </View>
        </View>

        <View style={{ padding: 20, opacity: 0.6, borderStyle: 'dashed', borderWidth: 1, borderColor: theme.line, marginTop: 16, borderRadius: 16 }}>
          <View style={styles.rowStart}>
            <Feather name="bar-chart-2" size={24} color={theme.muted} style={{ marginRight: 16 }} />
            <View style={{ flex: 1 }}>
              <Text style={[styles.bodyStrong, { marginBottom: 4 }]}>Performance quipe</Text>
              <Text style={{ fontSize: 12, color: theme.muted }}>Indicateurs et KPIs de productivit.</Text>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
};

