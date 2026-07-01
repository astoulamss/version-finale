import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, ActivityIndicator, Pressable } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { Ui } from "../types";
import { offboardingService } from "../services/offboarding.service";

export function OffboardingScreen({ ui, sessionProfile, triggerFeedback }: { ui: Ui, sessionProfile?: any, triggerFeedback?: any }) {
  const { styles, theme } = ui;
  const [plan, setPlan] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const data = await offboardingService.fetchMyPlans();
      if (data && data.length > 0) {
        setPlan(data[0]);
        setTasks(data[0].tasks || []);
      }
    } catch (e) {
      console.warn("Erreur chargement offboarding", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlans();
  }, []);

  const handleToggleTask = async (task: any) => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    try {
      await offboardingService.updateTaskStatus(task.id, newStatus);
      loadPlans();
    } catch (e) {
      console.warn("Update error", e);
    }
  };

  return (
    <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>

          <View>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Départ (Offboarding)</Text>
            <Text style={styles.mutedText}>Préparation de votre fin de contrat</Text>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator color={theme.sky} style={{ marginVertical: 32 }} />
        ) : !plan ? (
          <Card ui={ui}>
            <Text style={[styles.bodyText, { textAlign: 'center' }]}>Aucune procédure de départ n'a été trouvée pour votre profil.</Text>
          </Card>
        ) : (
          <>
            <AICard ui={ui}>
              <View style={styles.rowBetween}>
                <Text style={styles.cardTitle}>Statut de votre départ</Text>
                <StatusBadge label={plan.status === 'completed' ? "Terminé" : "En cours"} tone={plan.status === 'completed' ? "success" : "warning"} ui={ui} />
              </View>
              <Text style={[styles.bodyText, { marginTop: 8 }]}>
                Votre date de départ prévue est le <Text style={styles.bodyStrong}>{plan.departure_date || "Non définie"}</Text>.                  Merci de compléter les étapes ci-dessous pour assurer une transition fluide.</Text>
            </AICard>

            <SectionHeader icon="check-square" title="Checklist de départ" ui={ui} />
            
            {tasks.map((task: any) => (
              <Card key={task.id} ui={ui} style={{ marginBottom: 12 }}>
                <View style={styles.rowStart}>
                  <View style={{ 
                    backgroundColor: task.status === 'completed' ? theme.emerald + '20' : 
                                    task.status === 'in_progress' ? theme.amber + '20' : 
                                    theme.muted + '20', 
                    padding: 10, 
                    borderRadius: 8, 
                    marginRight: 12 
                  }}>
                    <Feather 
                      name={task.status === 'completed' ? 'check-circle' : task.status === 'in_progress' ? 'clock' : 'circle'} 
                      size={20} 
                      color={task.status === 'completed' ? theme.emerald : task.status === 'in_progress' ? theme.amber : theme.muted} 
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.bodyStrong}>{task.title}</Text>
                    <Text style={styles.metaText}>{task.date}</Text>
                  </View>
                </View>
                
                {task.status !== 'completed' && (
                  <View style={{ marginTop: 12, borderTopWidth: 1, borderColor: theme.line, paddingTop: 12 }}>
                    <SecondaryButton label={task.status === 'in_progress' ? "Continuer" : "Commencer"} icon="arrow-right" onPress={() => handleToggleTask(task)} ui={ui} />
                  </View>
                )}
              </Card>
            ))}

            {tasks.length === 0 && (
              <Text style={styles.mutedText}>Aucune tâche assignée.</Text>
            )}

            <SectionHeader icon="info" title="Informations utiles" ui={ui} />
            <Card ui={ui}>
              <Text style={styles.bodyText}>Vos accès seront coupés le dernier jour de votre contrat à 18h00.                  Pensez à télécharger vos fiches de paie et documents personnels avant cette date.</Text>
              <View style={{ marginTop: 16 }}>
                <PrimaryButton label="Aller aux documents" icon="file-text" onPress={() => {}} ui={ui} />
              </View>
            </Card>
          </>
        )}
      </View>
    </ScrollView>
  );
}
