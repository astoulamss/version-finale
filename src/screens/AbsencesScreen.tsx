import React, { useState, useEffect } from "react";
import { View, KeyboardAvoidingView, Platform, Text, Modal, TextInput, ActivityIndicator, Pressable, ScrollView } from "react-native";
import DateTimePicker from "@react-native-community/datetimepicker";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, IconButton } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { absencesService } from "../services/absences.service";
import { Ui, EmployeeProfile } from "../types";


export function AbsencesScreen({ ui, triggerFeedback, sessionProfile }: { ui: Ui; triggerFeedback: (label?: string) => void; sessionProfile: EmployeeProfile }) {
  const { styles, theme } = ui;
  const [modalOpen, setModalOpen] = useState(false);
  const [absences, setAbsences] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAbsence, setSelectedAbsence] = useState<any>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await absencesService.fetchMyAbsences();
      setAbsences(data);
    } catch (e) {
      console.warn("Error fetching absences", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await absencesService.deleteAbsence(id);
      triggerFeedback("Absence annulée");
      fetchData();
    } catch (e) {
      triggerFeedback("Erreur lors de l'annulation");
    }
  };

  const openEdit = (absence: any) => {
    setSelectedAbsence(absence);
    setModalOpen(true);
  };

  const openCreate = () => {
    setSelectedAbsence(null);
    setModalOpen(true);
  };

  return (
    <View style={styles.stack}>
      <AICard ui={ui}>
        <Text style={styles.heroTitle}>Mes Absences</Text>
        <Text style={styles.heroText}>Déclarez vos absences imprévues (maladie, retard, absence injustifiée) à votre équipe RH.</Text>
        <PrimaryButton icon="plus" label="Déclarer une absence" onPress={openCreate} ui={ui} />
      </AICard>

      <SectionHeader icon="clock" title="Absences actives" ui={ui} />
      {loading ? (
        <ActivityIndicator color={theme.sky} />
      ) : absences.length === 0 ? (
        <Text style={styles.mutedText}>Aucune absence en cours.</Text>
      ) : (
        absences.map((absence, index) => (
          <Card key={index} ui={ui}>
            <View style={styles.rowBetween}>
              <View>
                 <Text style={styles.bodyStrong}>{absence.absence_type} - {absence.duration_hours ? (absence.duration_hours / 24).toFixed(1) : "N/A"} jours</Text>
                 <Text style={styles.mutedText}>Du {absence.start_date?.split('T')[0]} au {absence.end_date?.split('T')[0]}</Text>
              </View>
              <StatusBadge label={absence.status === 'pending' ? "En attente" : absence.status} tone={absence.status === 'resolved' || absence.status === 'approved' ? 'success' : 'warning'} ui={ui} />
            </View>
            {absence.status === 'pending' && (
              <View style={[styles.rowStart, { marginTop: 12, borderTopWidth: 1, borderColor: theme.line, paddingTop: 12 }]}>
                <Pressable onPress={() => openEdit(absence)} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16 }}>
                  <Feather name="edit-2" size={14} color={theme.sky} />
                  <Text style={{ marginLeft: 4, color: theme.sky, fontSize: 13, fontWeight: '500' }}>Modifier</Text>
                </Pressable>
                <Pressable onPress={() => handleDelete(absence.id)} style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Feather name="trash-2" size={14} color={theme.rose} />
                  <Text style={{ marginLeft: 4, color: theme.rose, fontSize: 13, fontWeight: '500' }}>Supprimer</Text>
                </Pressable>
              </View>
            )}
          </Card>
        ))
      )}

      <AbsenceRequestModal open={modalOpen} onClose={() => { setModalOpen(false); fetchData(); }} triggerFeedback={triggerFeedback} ui={ui} sessionProfile={sessionProfile} existingAbsence={selectedAbsence} />
    </View>
  );
}

function AbsenceRequestModal({ open, onClose, triggerFeedback, ui, sessionProfile, existingAbsence }: { open: boolean; onClose: () => void; triggerFeedback: (label?: string) => void; ui: Ui; sessionProfile: EmployeeProfile, existingAbsence?: any }) {
  const { styles, theme } = ui;
  const [type, setType] = useState(existingAbsence?.absence_type || "maladie");
  const [start, setStart] = useState(existingAbsence?.start_date ? existingAbsence.start_date.split('T')[0] : "");
  const [end, setEnd] = useState(existingAbsence?.end_date ? existingAbsence.end_date.split('T')[0] : "");
  const [reason, setReason] = useState(existingAbsence?.reason || "");
  const [submitting, setSubmitting] = useState(false);
  const [showPicker, setShowPicker] = useState<"start" | "end" | null>(null);
  const currentPickerDate = showPicker === "start" ? (start ? new Date(start) : new Date()) : (end ? new Date(end) : new Date());

  useEffect(() => {
    if (open) {
      setType(existingAbsence?.absence_type || "maladie");
      setStart(existingAbsence?.start_date ? existingAbsence.start_date.split('T')[0] : "");
      setEnd(existingAbsence?.end_date ? existingAbsence.end_date.split('T')[0] : "");
      setReason(existingAbsence?.reason || "");
    }
  }, [open, existingAbsence]);

  const handleSubmit = async () => {
    if (!start || !end || !reason) { triggerFeedback("Veuillez remplir les champs obligatoires"); return; }
    setSubmitting(true);
    try {
      if (existingAbsence) {
        await absencesService.updateAbsence(existingAbsence.id, {
          absence_type: type,
          start_date: `${start}T00:00:00Z`,
          end_date: `${end}T23:59:59Z`,
          reason: reason
        });
        triggerFeedback("Absence modifiée avec succès");
      } else {
        await absencesService.declareAbsence({
          employee_id: parseInt(sessionProfile.employeeId, 10),
          absence_type: type,
          start_date: `${start}T00:00:00Z`,
          end_date: `${end}T23:59:59Z`,
          reason: reason
        });
        triggerFeedback("Absence déclarée avec succès");
      }
      onClose();
    } catch (e) {
      console.warn(e);
      triggerFeedback("Erreur lors de la déclaration");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal animationType="slide" onRequestClose={onClose} transparent visible={open}>
      <ScrollView automaticallyAdjustKeyboardInsets={true} style={{ flex: 1 }} contentContainerStyle={styles.modalBackdrop} keyboardShouldPersistTaps="handled" bounces={false}>
        <Pressable style={{ flex: 1 }} onPress={onClose} />
        <View style={styles.modalSheet}>
          <View style={styles.rowBetween}>
            <Text style={styles.modalTitle}>{existingAbsence ? "Modifier l'absence" : "Déclarer une absence"}</Text>
            <IconButton icon="x" onPress={onClose} ui={ui} />
          </View>
          <View style={styles.stack}>
            <View style={styles.fieldBlock}>
              <Text style={styles.fieldLabel}>Type d'absence</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 8 }}>
                <View style={styles.horizontalRail}>
                  <Pressable onPress={() => setType('maladie')} style={{ paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: type === 'maladie' ? theme.sky : theme.muted + '20', marginRight: 8 }}>
                    <Text style={{ color: type === 'maladie' ? '#fff' : theme.text, fontSize: 13, fontWeight: '600' }}>Maladie</Text>
                  </Pressable>
                  <Pressable onPress={() => setType('retard')} style={{ paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: type === 'retard' ? theme.sky : theme.muted + '20', marginRight: 8 }}>
                    <Text style={{ color: type === 'retard' ? '#fff' : theme.text, fontSize: 13, fontWeight: '600' }}>Retard</Text>
                  </Pressable>
                  <Pressable onPress={() => setType('injustifie')} style={{ paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: type === 'injustifie' ? theme.sky : theme.muted + '20', marginRight: 8 }}>
                    <Text style={{ color: type === 'injustifie' ? '#fff' : theme.text, fontSize: 13, fontWeight: '600' }}>Injustifiée</Text>
                  </Pressable>
                  <Pressable onPress={() => setType('autre')} style={{ paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: type === 'autre' ? theme.sky : theme.muted + '20' }}>
                    <Text style={{ color: type === 'autre' ? '#fff' : theme.text, fontSize: 13, fontWeight: '600' }}>Autre</Text>
                  </Pressable>
                </View>
              </ScrollView>
            </View>
            <View style={styles.rowBetween}>
               <View style={[styles.fieldBlock, { flex: 1, marginRight: 8 }]}>
                 <Text style={styles.fieldLabel}>Date de début</Text>
                 <Pressable onPress={() => setShowPicker("start")} style={[styles.fieldInput, { justifyContent: "center" }]}>
                   <Text style={{ color: start ? theme.text : theme.muted }}>{start || "Sélectionner"}</Text>
                 </Pressable>
               </View>
               <View style={[styles.fieldBlock, { flex: 1, marginLeft: 8 }]}>
                 <Text style={styles.fieldLabel}>Date de fin (est.)</Text>
                 <Pressable onPress={() => setShowPicker("end")} style={[styles.fieldInput, { justifyContent: "center" }]}>
                   <Text style={{ color: end ? theme.text : theme.muted }}>{end || "Sélectionner"}</Text>
                 </Pressable>
               </View>
            </View>
            
            {showPicker && (
              <View style={{ backgroundColor: theme.background, borderRadius: 12, padding: 12, marginBottom: 16 }}>
                <DateTimePicker themeVariant="light" textColor="#000000" 
                  value={currentPickerDate}
                  mode="date"
                  display={Platform.OS === "ios" ? "inline" : "default"}
                  onChange={(event: any, date?: Date) => {
                    if (Platform.OS === "android") setShowPicker(null);
                    if (date) {
                      const iso = date.toISOString().split("T")[0];
                      if (showPicker === "start") setStart(iso);
                      if (showPicker === "end") setEnd(iso);
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
            <View style={styles.fieldBlock}>
              <Text style={styles.fieldLabel}>Motif détaillé (obligatoire)</Text>
              <TextInput placeholder="Expliquez la raison de l'absence..." value={reason} onChangeText={setReason} placeholderTextColor={theme.muted} style={styles.fieldInput} multiline numberOfLines={3} textAlignVertical="top" />
            </View>
            <PrimaryButton icon="send" label={submitting ? "Envoi..." : existingAbsence ? "Enregistrer les modifications" : "Déclarer l'absence"} onPress={handleSubmit} ui={ui} />
          </View>
        </View>
      </ScrollView>
    </Modal>
  );
}
