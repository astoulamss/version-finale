import React, { useState, useEffect } from "react";
import { View, Text, Pressable, ActivityIndicator } from "react-native";
import { Feather } from "@expo/vector-icons";
import { SecondaryButton } from "../components/ui/Button";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { ProgressBar, StatusIcon } from "../components/Shared";
import { Ui, OnboardingTask } from "../types";
import { onboardingService } from "../services/onboarding.service";


export function OnboardingScreen({
  onSelectTask,
  triggerFeedback,
  ui,
}: {
  onboardingProgress?: number;
  onSelectTask: (task: OnboardingTask) => void;
  completedTasks?: string[];
  triggerFeedback: (label?: string) => void;
  ui: Ui;
}) {
  const { styles, theme } = ui;
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const plans = await onboardingService.fetchMyPlans();
      let allTasks: any[] = [];
      if (plans && plans.length > 0) {
        plans.forEach((plan: any) => {
          if (plan.tasks) {
            allTasks = [...allTasks, ...plan.tasks];
          }
        });
      }
      setTasks(allTasks);
    } catch (e) {
      console.warn("Erreur chargement onboarding:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleTaskPress = (task: any) => {
    // Adapter le format pour le modal existant dans App.tsx
    const adaptedTask: OnboardingTask = {
      id: String(task.id),
      title: task.title,
      description: task.description || "Aucune description fournie.",
      deadline: task.due_date || "Non définie",
      status: task.status === "done" ? "done" : "todo",
      resources: [],
      contacts: [],
      documents: []
    };
    onSelectTask(adaptedTask);
  };

  const completedCount = tasks.filter(t => t.status === "done").length;
  const totalCount = tasks.length;
  const progress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <View style={styles.stack}>
      <AICard ui={ui}>
        <Text style={styles.heroTitle}>Onboarding J1 - J30</Text>
        <Text style={styles.heroText}>Suivez votre parcours d'intégration généré par l'API.</Text>
        <View style={styles.rowBetween}>
          <Text style={styles.progressValue}>{progress}%</Text>
          <StatusBadge label={progress === 100 ? "Terminé" : "En cours"} tone={progress === 100 ? "success" : "info"} ui={ui} />
        </View>
        <ProgressBar value={progress} ui={ui} />
      </AICard>

      {loading ? (
        <ActivityIndicator color={theme.sky} style={{ marginVertical: 32 }} />
      ) : (
        <Card ui={ui}>
          <View style={styles.rowBetween}>
            <View>
              <Text style={styles.cardTitle}>Mes tâches à accomplir</Text>
              <Text style={styles.mutedText}>{completedCount} sur {totalCount} terminées</Text>
            </View>
          </View>
          
          <View style={[styles.taskList, { marginTop: 16 }]}>
            {tasks.length === 0 ? (
              <Text style={styles.mutedText}>Aucune tâche d'intégration n'a été trouvée pour votre profil.</Text>
            ) : (
              tasks.map((task) => (
                <Pressable key={task.id} onPress={() => handleTaskPress(task)} style={styles.taskRow}>
                  <StatusIcon status={task.status === "done" ? "done" : "todo"} ui={ui} />
                  <View style={styles.flex1}>
                    <Text style={[styles.bodyStrong, task.status === "done" && { textDecorationLine: 'line-through', opacity: 0.6 }]}>
                      {task.title}
                    </Text>
                    <Text style={styles.mutedText}>Deadline: {task.due_date || "N/A"}</Text>
                  </View>
                  <Feather name="chevron-right" size={18} color={theme.muted} />
                </Pressable>
              ))
            )}
          </View>
        </Card>
      )}

      <Card tone="success" ui={ui}>
        <View style={styles.rowStart}>
          <View style={styles.successMedal}>
            <Feather name="award" size={22} color="#ffffff" />
          </View>
          <View style={styles.flex1}>
            <Text style={styles.cardTitle}>Ecran succes J30</Text>
            <Text style={styles.bodyText}>Vous pouvez générer une synthèse de votre progression.</Text>
          </View>
        </View>
        <SecondaryButton icon="download" label="Générer mon rapport" onPress={() => triggerFeedback("Rapport d'intégration demandé")} ui={ui} />
      </Card>
    </View>
  );
}
