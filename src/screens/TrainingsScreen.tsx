import React, { useState, useEffect } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton } from "../components/ui/Button";
import { Ui } from "../types";
import { employeeService } from "../services/employee.service";


export function TrainingsScreen({ ui, sessionProfile, triggerFeedback }: { ui: Ui, sessionProfile?: any, triggerFeedback?: any }) {
  const { styles, theme } = ui;
  const [activeTab, setActiveTab] = useState<'catalog' | 'my_trainings'>('catalog');
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  
  const [catalog, setCatalog] = useState<any[]>([]);
  const [enrollments, setEnrollments] = useState<any[]>([]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [catData, enrData] = await Promise.all([
        employeeService.fetchFormations(),
        employeeService.fetchMyEnrollments()
      ]);
      setCatalog(catData || []);
      setEnrollments(enrData || []);
    } catch (e) {
      console.error("Erreur chargement formations:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const isEnrolled = (formationId: number) => {
    return enrollments.some(e => e.formation_id === formationId);
  };

  const handleEnroll = async (id: number) => {
    try {
      setActionLoadingId(id);
      await employeeService.enrollInFormation(id);
      await fetchData(); // Refresh data
    } catch (e: any) {
      console.warn("Erreur d'inscription:", e);
      alert(e.response?.data?.detail || "Erreur lors de l'inscription.");
    } finally {
      setActionLoadingId(null);
    }
  };
  
  const handleUnenroll = async (id: number) => {
    try {
      setActionLoadingId(id);
      await employeeService.unenrollFromFormation(id);
      await fetchData(); // Refresh data
    } catch (e: any) {
      console.warn("Erreur de désinscription:", e);
      alert(e.response?.data?.detail || "Erreur lors de la désinscription.");
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
          <View>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Développement des Compétences</Text>
            <Text style={styles.mutedText}>Gérez vos formations et votre parcours</Text>
          </View>
        </View>

        <View style={{ flexDirection: 'row', marginBottom: 16, backgroundColor: theme.line, borderRadius: 8, padding: 4 }}>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'catalog' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('catalog')}
          >
            <Text style={{ fontWeight: activeTab === 'catalog' ? '600' : '400', color: theme.text }}>Catalogue</Text>
          </Pressable>
          <Pressable 
            style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'my_trainings' ? theme.surfaceAlt : 'transparent', borderRadius: 6 }}
            onPress={() => setActiveTab('my_trainings')}
          >
            <Text style={{ fontWeight: activeTab === 'my_trainings' ? '600' : '400', color: theme.text }}>Mes Formations</Text>
          </Pressable>
        </View>

        {loading ? (
          <ActivityIndicator color={theme.sky} style={{ marginVertical: 32 }} />
        ) : activeTab === 'catalog' ? (
          <>
            <SectionHeader icon="book-open" title="Catalogue des formations" ui={ui} />
            
            {catalog.length === 0 ? (
               <Text style={styles.mutedText}>Aucune formation disponible pour votre département.</Text>
            ) : (
              catalog.map(item => {
                const enrolled = isEnrolled(item.id);
                return (
                  <Card key={item.id} ui={ui} style={{ marginBottom: 12 }}>
                    <View style={styles.rowBetween}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.bodyStrong}>{item.title}</Text>
                        <Text style={styles.metaText}>{item.start_date} au {item.end_date}</Text>
                      </View>
                      <StatusBadge 
                        label={enrolled ? 'Inscrit' : 'Disponible'} 
                        tone={enrolled ? 'success' : 'info'} 
                        ui={ui} 
                      />
                    </View>
                    <Text style={[styles.bodyText, { marginTop: 8, fontSize: 13 }]}>{item.description}</Text>
                    <View style={{ marginTop: 12 }}>
                      {enrolled ? (
                         <PrimaryButton 
                           label={actionLoadingId === item.id ? "Désinscription..." : "Se désinscrire"} 
                           icon="x" 
                           onPress={() => handleUnenroll(item.id)} 
                           disabled={actionLoadingId === item.id}
                           ui={{ ...ui, theme: { ...ui.theme, sky: ui.theme.rose } }} 
                         />
                      ) : (
                         <PrimaryButton 
                           label={actionLoadingId === item.id ? "Inscription en cours..." : "S'inscrire"} 
                           icon="check" 
                           onPress={() => handleEnroll(item.id)} 
                           disabled={actionLoadingId === item.id}
                           ui={ui} 
                         />
                      )}
                    </View>
                  </Card>
                );
              })
            )}
          </>
        ) : (
          <>
            <SectionHeader icon="award" title="Mes Inscriptions" ui={ui} />
            
            {enrollments.length === 0 ? (
               <Text style={styles.mutedText}>Vous n'êtes inscrit à aucune formation.</Text>
            ) : (
              enrollments.map(item => (
                <Card key={item.id} ui={ui} style={{ marginBottom: 12 }}>
                  <View style={styles.rowBetween}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.bodyStrong}>{item.formation_title}</Text>
                      <Text style={styles.metaText}>{item.formation_start_date} au {item.formation_end_date}</Text>
                    </View>
                    <StatusBadge 
                      label="Confirmé"
                      tone="success"
                      ui={ui} 
                    />
                  </View>
                  {item.formation_description && (
                     <Text style={[styles.bodyText, { marginTop: 8, fontSize: 13 }]}>{item.formation_description}</Text>
                  )}
                  <View style={{ marginTop: 12 }}>
                     <PrimaryButton 
                       label={actionLoadingId === item.formation_id ? "Désinscription..." : "Se désinscrire"} 
                       icon="x" 
                       onPress={() => handleUnenroll(item.formation_id)} 
                       disabled={actionLoadingId === item.formation_id}
                       ui={{ ...ui, theme: { ...ui.theme, sky: ui.theme.rose } }} 
                     />
                  </View>
                </Card>
              ))
            )}
          </>
        )}
      </View>
    </ScrollView>
  );
}
