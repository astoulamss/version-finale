import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, ActivityIndicator, Pressable, Modal } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge, Chip } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton, IconButton } from "../components/ui/Button";
import { Ui } from "../types";
import { myTasksService } from "../services/myTasks.service";

export function TasksView({ ui }: { ui: Ui }) {
  const { styles, theme } = ui;
  const [tasks, setTasks] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'in_progress' | 'overdue' | 'done'>('all');
  const [selectedTask, setSelectedTask] = useState<any>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, tasksData] = await Promise.all([
        myTasksService.fetchMyTasksStats(),
        filter === 'all' ? myTasksService.fetchMyTasks() :
        filter === 'in_progress' ? myTasksService.fetchMyTasks('in_progress') :
        filter === 'done' ? myTasksService.fetchMyTasks('done') :
        myTasksService.fetchMyTasks(undefined, true) // overdue
      ]);
      setStats(statsData);
      setTasks(tasksData);
    } catch (e) {
      console.warn("Erreur chargement tâches:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  const updateStatus = async (taskId: number, newStatus: string) => {
    try {
      await myTasksService.updateTaskStatus(taskId, newStatus);
      if (selectedTask && selectedTask.id === taskId) {
        setSelectedTask({ ...selectedTask, status: newStatus });
      }
      loadData();
    } catch (e) {
      console.warn("Erreur maj statut:", e);
    }
  };

  const filters = [
    { id: 'all', label: 'Toutes les tâches' },
    { id: 'in_progress', label: 'En cours' },
    { id: 'overdue', label: 'En retard' },
    { id: 'done', label: 'Terminées' }
  ];

  const getPriorityTone = (priority: string) => {
    switch(priority) {
      case 'urgent': return 'critical';
      case 'high': return 'warning';
      case 'low': return 'info';
      default: return 'info';
    }
  };

  const getStatusTone = (status: string) => {
    switch(status) {
      case 'done': return 'success';
      case 'in_progress': return 'warning';
      case 'todo': return 'info';
      case 'cancelled': return 'critical';
      default: return 'info';
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
        <View style={styles.stack}>
          <View style={{ marginBottom: 16 }}>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Mes Tâches</Text>
            <Text style={styles.mutedText}>Gérez vos tâches assignées</Text>
          </View>

          {/* KPI Dashboard */}
          {stats && (
            <View style={[styles.actionGrid, { flexWrap: "wrap", justifyContent: "space-between" }]}>
              <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
                <Text style={[styles.progressValue, { fontSize: 24 }]}>{stats.total || 0}</Text>
                <Text style={styles.mutedText}>Total Tâches</Text>
              </Card>
              <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
                <Text style={[styles.progressValue, { fontSize: 24, color: theme.amber }]}>{stats.not_done || 0}</Text>
                <Text style={styles.mutedText}>À faire / En cours</Text>
              </Card>
              <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
                <Text style={[styles.progressValue, { fontSize: 24, color: theme.rose }]}>{stats.overdue || 0}</Text>
                <Text style={styles.mutedText}>En retard</Text>
              </Card>
              <Card style={[styles.card, { width: "48%", marginBottom: 8 }]} ui={ui}>
                <Text style={[styles.progressValue, { fontSize: 24, color: theme.emerald }]}>{stats.done || 0}</Text>
                <Text style={styles.mutedText}>Terminées</Text>
              </Card>
            </View>
          )}

          {/* Filters */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginVertical: 16 }}>
            <View style={styles.chipWrap}>
              {filters.map(f => (
                <Chip 
                  key={f.id} 
                  label={f.label} 
                  active={filter === f.id} 
                  onPress={() => setFilter(f.id as any)} 
                  ui={ui} 
                />
              ))}
            </View>
          </ScrollView>

          {/* Task List */}
          {loading ? (
            <ActivityIndicator color={theme.sky} style={{ marginVertical: 32 }} />
          ) : tasks.length === 0 ? (
            <Card ui={ui}>
              <Text style={[styles.bodyText, { textAlign: 'center' }]}>Aucune tâche ne correspond à ce filtre.</Text>
            </Card>
          ) : (
            tasks.map(task => (
              <Pressable key={task.id} onPress={() => setSelectedTask(task)}>
                <Card ui={ui} style={{ marginBottom: 12 }}>
                  <View style={styles.rowBetween}>
                    <Text style={[styles.bodyStrong, { flex: 1, marginRight: 8 }]} numberOfLines={1}>{task.title}</Text>
                    <StatusBadge label={task.status} tone={getStatusTone(task.status) as any} ui={ui} />
                  </View>
                  <View style={[styles.rowStart, { marginTop: 8 }]}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16 }}>
                      <Feather name="alert-circle" size={14} color={theme.muted} style={{ marginRight: 4 }} />
                      <Text style={styles.metaText}>Priorité: {task.priority}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                      <Feather name="calendar" size={14} color={theme.muted} style={{ marginRight: 4 }} />
                      <Text style={styles.metaText}>Échéance: {task.due_date || 'N/A'}</Text>
                    </View>
                  </View>
                  <View style={{ marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: theme.line }}>
                    <Text style={styles.metaText}>Assigné par: {task.creator_prenom} {task.creator_nom}</Text>
                  </View>
                </Card>
              </Pressable>
            ))
          )}
        </View>
      </ScrollView>

      {/* Task Detail Modal */}
      {selectedTask && (
        <Modal animationType="slide" transparent visible={!!selectedTask} onRequestClose={() => setSelectedTask(null)}>
          <View style={styles.modalBackdrop}>
            <View style={styles.modalSheet}>
              <View style={styles.rowBetween}>
                <Text style={styles.modalTitle}>Détail de la tâche</Text>
                <IconButton icon="x" onPress={() => setSelectedTask(null)} ui={ui} />
              </View>
              
              <View style={styles.stack}>
                <Text style={[styles.heroTitle, { fontSize: 20 }]}>{selectedTask.title}</Text>
                
                <View style={[styles.rowBetween, { marginVertical: 8 }]}>
                  <StatusBadge label={selectedTask.status} tone={getStatusTone(selectedTask.status) as any} ui={ui} />
                  <StatusBadge label={`Priorité: ${selectedTask.priority}`} tone={getPriorityTone(selectedTask.priority) as any} ui={ui} />
                </View>

                <View style={styles.fieldBlock}>
                  <Text style={styles.fieldLabel}>Description</Text>
                  <Text style={styles.bodyText}>{selectedTask.description || "Aucune description fournie."}</Text>
                </View>

                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 16, marginBottom: 16 }}>
                  <View>
                    <Text style={styles.fieldLabel}>Date d'échéance</Text>
                    <Text style={styles.bodyStrong}>{selectedTask.due_date || "Non définie"}</Text>
                  </View>
                  <View>
                    <Text style={styles.fieldLabel}>Assigné par</Text>
                    <Text style={styles.bodyStrong}>{selectedTask.creator_prenom} {selectedTask.creator_nom}</Text>
                  </View>
                  <View>
                    <Text style={styles.fieldLabel}>Créée le</Text>
                    <Text style={styles.bodyStrong}>{new Date(selectedTask.created_at).toLocaleDateString()}</Text>
                  </View>
                </View>

                {/* Actions */}
                <View style={{ borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 16 }}>
                  <Text style={styles.fieldLabel}>Mettre à jour le statut</Text>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                    {selectedTask.status !== 'todo' && (
                      <Chip label="À faire" onPress={() => updateStatus(selectedTask.id, 'todo')} ui={ui} />
                    )}
                    {selectedTask.status !== 'in_progress' && (
                      <Chip label="En cours" onPress={() => updateStatus(selectedTask.id, 'in_progress')} ui={ui} />
                    )}
                    {selectedTask.status !== 'done' && (
                      <Chip label="Terminer" active onPress={() => updateStatus(selectedTask.id, 'done')} ui={ui} />
                    )}
                  </View>
                </View>
              </View>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}
