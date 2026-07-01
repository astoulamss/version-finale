

import React, { useState, useEffect } from "react";
import { View, KeyboardAvoidingView, Platform, Text, Modal, TextInput, ActivityIndicator, Alert, Pressable, ScrollView } from "react-native";
import DateTimePicker from "@react-native-community/datetimepicker";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton, IconButton } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { DocumentRow } from "../components/Shared";
import { employeeService } from "../services/employee.service";
import { leavesService } from "../services/leaves.service";
import { fetchMyLeaveBalances, fetchMyDocuments } from "../services/dashboard.service";
import { surveysService } from "../services/surveys.service";
import { downloadAndOpenDocument } from "../utils/document.utils";
import { Ui, ViewId, EmployeeProfile } from "../types";
export function LeaveScreen({ ui, triggerFeedback, sessionProfile }: { ui: Ui; triggerFeedback: (label?: string) => void; sessionProfile: EmployeeProfile }) {
  const { styles, theme } = ui;
  const [leaveModalOpen, setLeaveModalOpen] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState<any>(null);
  const [leaves, setLeaves] = useState<any[]>([]);
  const [balances, setBalances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [leavesData, balancesData] = await Promise.all([
        leavesService.fetchMyLeaves(),
        fetchMyLeaveBalances(),
      ]);
      setLeaves(leavesData);
      setBalances(balancesData);
    } catch (e) {
      console.warn(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalRemaining = balances.reduce((sum, bal) => sum + (Number(bal.remaining_days) || 0), 0);

  const handleDelete = async (leaveId: number) => {
    try {
      await leavesService.deleteLeave(leaveId);
      triggerFeedback("Demande annulée avec succès");
      fetchData();
    } catch (e) {
      triggerFeedback("Erreur lors de l'annulation");
    }
  };

  return (
    <View style={styles.stack}>
      <AICard ui={ui}>
        <Text style={styles.heroTitle}>{'Mes Congés'}</Text>
        <Text style={[styles.heroText, { marginBottom: 16 }]}>Les demandes sont validées par {sessionProfile.manager || 'votre manager'}.</Text>
        
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          {loading ? (
             <ActivityIndicator color={theme.sky} style={{ margin: 16 }} />
          ) : balances.length > 0 ? balances.map((bal, idx) => (
            <View key={idx} style={{ backgroundColor: theme.surfaceAlt, padding: 8, borderRadius: 8, minWidth: '48%', flex: 1 }}>
              <Text style={[styles.bodyStrong, { fontSize: 13 }]} numberOfLines={1}>{bal.leave_type_name || "Congé"}</Text>
              <Text style={{ fontSize: 16, fontWeight: 'bold', color: theme.sky, marginTop: 4 }}>
                {Number(bal.remaining_days)} <Text style={{ fontSize: 12, fontWeight: 'normal', color: theme.muted }}>jours</Text>
              </Text>
            </View>
          )) : (
            <Text style={styles.mutedText}>Aucun solde disponible</Text>
          )}
        </View>

        <PrimaryButton icon='plus' label='Nouvelle demande' onPress={() => { setSelectedLeave(null); setLeaveModalOpen(true); }} ui={ui} />
      </AICard>
      <SectionHeader icon='calendar' title='Historique' ui={ui} />
      {loading ? (
        <ActivityIndicator color={theme.sky} />
      ) : leaves.length === 0 ? (
        <Text style={styles.mutedText}>{'Aucune demande de congé'}</Text>
      ) : (
        leaves?.map((leave, index) => (
          <Card key={index} ui={ui}>
            <View style={styles.rowBetween}>
              <View>
                <Text style={styles.bodyStrong}>{leave.leave_type_name || leave.leave_type} - {leave.duration || 'N/A'} jours</Text>
                <Text style={styles.mutedText}>Du {leave.start_date} au {leave.end_date}</Text>
              </View>
              <StatusBadge label={leave.status === 'pending' ? 'En attente' : leave.status === 'approved' ? 'Accepté' : leave.status === 'rejected' ? 'Refusé' : leave.status} tone={leave.status === 'approved' ? 'success' : leave.status === 'rejected' ? 'critical' : 'warning'} ui={ui} />
            </View>
            {leave.status === 'pending' && (
              <View style={[styles.rowStart, { marginTop: 12, borderTopWidth: 1, borderColor: theme.line, paddingTop: 12 }]}>
                <Pressable onPress={() => { setSelectedLeave(leave); setLeaveModalOpen(true); }} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16 }}>
                  <Feather name='edit-2' size={14} color={theme.sky} />
                  <Text style={{ marginLeft: 4, color: theme.sky, fontSize: 13, fontWeight: '500' }}>Modifier</Text>
                </Pressable>
                <Pressable onPress={() => handleDelete(leave.id)} style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Feather name='trash-2' size={14} color={theme.rose} />
                  <Text style={{ marginLeft: 4, color: theme.rose, fontSize: 13, fontWeight: '500' }}>Annuler</Text>
                </Pressable>
              </View>
            )}
          </Card>
        ))
      )}
      <LeaveRequestModal initialData={selectedLeave} open={leaveModalOpen} onClose={() => { setLeaveModalOpen(false); setSelectedLeave(null); fetchData(); }} triggerFeedback={triggerFeedback} ui={ui} />
    </View>
  );
}

export function LeaveRequestModal({ open, onClose, triggerFeedback, ui, initialData }: { open: boolean; onClose: () => void; triggerFeedback: (label?: string) => void; ui: Ui; initialData?: any }) {
  const { styles, theme } = ui;
  const [typeId, setTypeId] = useState<number | null>(null);
  const [leaveTypes, setLeaveTypes] = useState<any[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  React.useEffect(() => {
    if (open) {
      setErrorMsg(null);
      leavesService.fetchLeaveTypes().then(data => {
        setLeaveTypes(data);
        if (data && data.length > 0 && !typeId && !initialData) {
          setTypeId(data[0].id);
        }
      }).catch(e => {
        console.warn("Erreur fetch types:", e);
        setErrorMsg("Impossible de charger les types de congés");
      });
    }
  }, [open]);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showPicker, setShowPicker] = useState<"start" | "end" | null>(null);
  const currentPickerDate = showPicker === "start" ? (start ? new Date(start) : new Date()) : (end ? new Date(end) : new Date());

  React.useEffect(() => {
    if (open) {
      if (initialData?.leave_type_id) {
        setTypeId(initialData.leave_type_id);
      }
      setStart(initialData?.start_date || '');
      setEnd(initialData?.end_date || '');
      setReason(initialData?.reason || '');
    }
  }, [open, initialData]);

  const handleSubmit = async () => {
    if (!typeId || !start || !end) { triggerFeedback('Veuillez remplir tous les champs obligatoires'); return; }
    setSubmitting(true);
    try {
      if (initialData && initialData.id) {
        await leavesService.editLeave(initialData.id, {
          leave_type_id: typeId,
          start_date: start,
          end_date: end,
          reason: reason
        });
        triggerFeedback('Demande modifiée avec succès');
      } else {
        await leavesService.submitLeave({
          leave_type_id: typeId,
          start_date: start,
          end_date: end,
          reason: reason
        });
        triggerFeedback('Demande envoyée pour validation');
      }
      onClose();
    } catch (e) {
      console.warn(e);
      triggerFeedback('Erreur lors de la requête');
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
            <Text style={styles.modalTitle}>{initialData ? 'Modifier la demande' : "Demande de congés"}</Text>
            <IconButton icon="x" onPress={onClose} ui={ui} />
          </View>
          <View style={styles.stack}>
            <View style={styles.fieldBlock}>
              <Text style={styles.fieldLabel}>Type de congé</Text>
              {errorMsg && <Text style={{color: theme.rose, fontSize: 12, marginBottom: 8}}>{errorMsg}</Text>}
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 8 }}>
                <View style={styles.horizontalRail}>
                  {leaveTypes.length > 0 ? leaveTypes.map((lt, idx) => (
                    <Pressable key={idx} onPress={() => setTypeId(lt.id)} style={{ paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: typeId === lt.id ? theme.sky : theme.muted + '20', marginRight: 8 }}>
                      <Text style={{ color: typeId === lt.id ? '#fff' : theme.text, fontSize: 13, fontWeight: '600' }}>{lt.name}</Text>
                    </Pressable>
                  )) : <ActivityIndicator color={theme.sky} style={{ marginHorizontal: 20 }} />}
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
                <Text style={styles.fieldLabel}>Date de fin</Text>
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
              <Text style={styles.fieldLabel}>Commentaire (optionnel)</Text>
              <TextInput placeholder="Motif ou information supplémentaire..." value={reason} onChangeText={setReason} placeholderTextColor={theme.muted} style={styles.fieldInput} multiline numberOfLines={3} textAlignVertical="top" />
            </View>
            <PrimaryButton
              icon="send"
              label={submitting ? "Envoi..." : "Soumettre la demande"}
              onPress={handleSubmit}
              ui={ui}
            />
          </View>
        </View>
      </ScrollView>
    </Modal>
  );
}

export function PayrollScreen({ ui, triggerFeedback, sessionProfile }: { ui: Ui; triggerFeedback: (label?: string) => void; sessionProfile: EmployeeProfile }) {
  const { styles, theme } = ui;
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMyDocuments()
      .then(data => setDocuments(data))
      .catch(console.warn)
      .finally(() => setLoading(false));
  }, []);

  // Filter or fall back
  const displayDocs = documents.map((doc) => ({
    id: String(doc.id),
    title: doc.title || doc.document_type?.name || "Document RH",
    category: doc.document_type?.name || "Paie",
    date: new Date(doc.created_at).toLocaleDateString(),
    status: "downloadable" as const,
    owner: "RH"
  }));

  const handleDownload = (docId: string, title?: string) => {
    downloadAndOpenDocument(docId, title, triggerFeedback);
  };

  return (
    <View style={styles.stack}>
      <AICard ui={ui}>
        <Text style={styles.heroTitle}>Ma Paie</Text>
        <Text style={styles.heroText}>Votre prochain bulletin sera généré et mis à disposition le 28 du mois en cours.</Text>
        <PrimaryButton 
          icon="download" 
          label="Télécharger le dernier bulletin" 
          onPress={() => displayDocs[0] ? handleDownload(displayDocs[0].id, displayDocs[0].title) : triggerFeedback('Aucun bulletin disponible')} 
          ui={ui} 
        />
      </AICard>
      <SectionHeader icon="folder" title="Archives" ui={ui} />
      {loading ? (
        <ActivityIndicator color={theme.sky} />
      ) : displayDocs.length === 0 ? (
        <Text style={styles.mutedText}>Aucun bulletin de paie disponible.</Text>
      ) : (
        displayDocs.map((doc) => (
          <DocumentRow key={doc.id} document={doc} onPress={() => handleDownload(doc.id, doc.title)} ui={ui} />
        ))
      )}
    </View>
  );
}

export function RequestsScreen({ ui, triggerFeedback }: { ui: Ui; triggerFeedback: (label?: string) => void }) {
  const { styles, theme } = ui;
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchTickets = async () => {
    try {
      const data = await employeeService.fetchTickets();
      setTickets(data);
    } catch (e) {
      console.warn(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  return (
    <View style={styles.stack}>
      <AICard ui={ui}>
        <Text style={styles.heroTitle}>Mes Demandes RH</Text>
        <Text style={styles.heroText}>Besoin d'une attestation ou d'un renseignement ? Faites une demande ici.</Text>
        <PrimaryButton icon="plus" label="Créer une demande" onPress={() => setModalOpen(true)} ui={ui} />
      </AICard>
      <SectionHeader icon="clock" title="En attente" ui={ui} />
      {loading ? (
        <ActivityIndicator color={theme.sky} />
      ) : tickets.length === 0 ? (
        <Text style={styles.mutedText}>Vous n'avez aucune demande en cours.</Text>
      ) : (
        tickets?.map((t) => (
          <DocumentRow
            key={t.id}
            document={{
              id: String(t.id),
              title: t.subject,
              category: "Demande RH",
              date: new Date(t.created_at).toLocaleDateString(),
              status: t.status === 'open' ? 'pending' : t.status === 'resolved' ? 'approved' : 'correction',
              owner: t.assignee ? `${t.assignee.prenom} ${t.assignee.nom}` : "RH"
            }}
            onPress={() => triggerFeedback(`Demande: ${t.subject}`)}
            ui={ui}
          />
        ))
      )}
      <TicketRequestModal open={modalOpen} onClose={() => { setModalOpen(false); fetchTickets(); }} triggerFeedback={triggerFeedback} ui={ui} />
    </View>
  );
}

export function TicketRequestModal({ open, onClose, triggerFeedback, ui }: { open: boolean; onClose: () => void; triggerFeedback: (label?: string) => void; ui: Ui }) {
  const { styles, theme } = ui;
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!subject || !description) { triggerFeedback("Veuillez remplir tous les champs obligatoires"); return; }
    setSubmitting(true);
    try {
      await employeeService.createTicket({
        subject,
        description
      });
      triggerFeedback("Demande créée avec succès");
      setSubject("");
      setDescription("");
      onClose();
    } catch (e) {
      console.warn(e);
      triggerFeedback("Erreur lors de la création de la demande");
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
            <Text style={styles.modalTitle}>Nouvelle Demande</Text>
            <IconButton icon="x" onPress={onClose} ui={ui} />
          </View>
          <View style={styles.stack}>
            <View style={styles.fieldBlock}>
              <Text style={styles.fieldLabel}>Type de demande</Text>
              <TextInput placeholder="Sujet de votre demande..." value={subject} onChangeText={setSubject} placeholderTextColor={theme.muted} style={styles.fieldInput} />
            </View>
            <View style={styles.fieldBlock}>
              <Text style={styles.fieldLabel}>Détails de la demande</Text>
              <TextInput placeholder="Décrivez votre demande en détail..." value={description} onChangeText={setDescription} placeholderTextColor={theme.muted} style={styles.fieldInput} multiline numberOfLines={4} textAlignVertical="top" />
            </View>
            <PrimaryButton
              icon="send"
              label={submitting ? "Envoi..." : "Envoyer la demande"}
              onPress={handleSubmit}
              ui={ui}
            />
          </View>
        </View>
      </ScrollView>
    </Modal>
  );
}

export function MobilityScreen({ ui, triggerFeedback }: { ui: Ui, triggerFeedback: (label?: string) => void }) {
  const { styles, theme } = ui;
  return (
    <View style={styles.stack}>
      <AICard ui={ui}>
        <Text style={styles.heroTitle}>Mobilité interne</Text>
        <Text style={styles.heroText}>La mise en relation IA avec des opportunités internes n'est pas encore disponible dans cette version.</Text>
      </AICard>
      <SectionHeader icon="briefcase" title="Opportunités" ui={ui} />
      <Card ui={ui}>
        <Text style={styles.mutedText}>Aucune opportunité pour le moment.</Text>
      </Card>
    </View>
  );
}

export function TicketsScreen({ ui, triggerFeedback }: { ui: Ui, triggerFeedback: (label?: string) => void }) {
  const { styles, theme } = ui;
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    employeeService.fetchTickets().then(data => setTickets(data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <View style={styles.stack}>
      <SectionHeader icon="tag" title="Mes Tickets RH & IT" ui={ui} />
      {loading && <Text style={styles.bodyText}>Chargement des tickets...</Text>}
      {!loading && tickets.length === 0 && (
        <Card ui={ui}><Text style={styles.mutedText}>Aucun ticket pour le moment.</Text></Card>
      )}
      {tickets?.map((t) => (
        <Card key={t.id} ui={ui}>
          <View style={styles.rowBetween}>
            <Text style={styles.cardTitle}>{t.subject}</Text>
            <StatusBadge label={t.status} tone={t.status === 'open' ? 'warning' : t.status === 'resolved' || t.status === 'closed' ? 'success' : 'info'} ui={ui} />
          </View>
          <Text style={styles.bodyText}>{t.description}</Text>
        </Card>
      ))}
    </View>
  );
}


export function SurveyResponseModal({ open, survey, onClose, onSubmit, ui }: { open: boolean; survey: any; onClose: () => void; onSubmit: () => void; ui: Ui }) {
  const { styles, theme } = ui;
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && survey) {
      setAnswers({});
    }
  }, [open, survey]);

  if (!open || !survey) return null;

  const handleAnswerChange = (questionId: number, val: any) => {
    setAnswers(prev => ({ ...prev, [questionId]: val }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const payload = Object.keys(answers).map(qId => {
        const qIdNum = parseInt(qId, 10);
        const qDef = survey.questions?.find((q: any) => q.id === qIdNum);
        const val = answers[qIdNum];
        let score = undefined;
        let answerStr = undefined;
        if (qDef?.question_type === 'rating') {
          score = val;
        } else if (qDef?.question_type === 'yes_no') {
          answerStr = val ? 'Oui' : 'Non';
        } else {
          answerStr = String(val);
        }
        return { question_id: qIdNum, answer: answerStr, score };
      });
      
      await surveysService.submitSurveyResponse(survey.id, payload);
      onSubmit();
    } catch (e) {
      console.warn("Error submitting survey", e);
      // Let the parent handle or just show error.
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
            <Text style={styles.modalTitle}>{survey.title}</Text>
            <IconButton icon="x" onPress={onClose} ui={ui} />
          </View>
          <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} style={{ marginTop: 16 }}>
            <Text style={[styles.bodyText, { marginBottom: 24 }]}>{survey.description}</Text>

            {(survey.questions || []).map((q: any, index: number) => (
              <View key={q.id} style={{ marginBottom: 24 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 12 }]}>{index + 1}. {q.question}</Text>
                
                {q.question_type === 'yes_no' && (
                  <View style={[styles.rowStart, { backgroundColor: theme.cardElevated, borderRadius: 8, padding: 4 }]}>
                    <Pressable onPress={() => handleAnswerChange(q.id, true)} style={{ flex: 1, paddingVertical: 12, alignItems: 'center', backgroundColor: answers[q.id] === true ? theme.sky : 'transparent', borderRadius: 6 }}>
                      <Text style={{ color: answers[q.id] === true ? '#fff' : theme.text, fontWeight: '600' }}>Oui</Text>
                    </Pressable>
                    <Pressable onPress={() => handleAnswerChange(q.id, false)} style={{ flex: 1, paddingVertical: 12, alignItems: 'center', backgroundColor: answers[q.id] === false ? theme.rose : 'transparent', borderRadius: 6 }}>
                      <Text style={{ color: answers[q.id] === false ? '#fff' : theme.text, fontWeight: '600' }}>Non</Text>
                    </Pressable>
                  </View>
                )}

                {q.question_type === 'rating' && (
                  <View style={styles.rowBetween}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Pressable key={star} onPress={() => handleAnswerChange(q.id, star)} style={{ padding: 8 }}>
                        <Feather name="star" size={32} color={star <= (answers[q.id] || 0) ? theme.amber : theme.line} fill={star <= (answers[q.id] || 0) ? theme.amber : 'transparent'} />
                      </Pressable>
                    ))}
                  </View>
                )}

                {(q.question_type === 'free_text' || q.question_type === 'single_choice' || q.question_type === 'multiple_choice') && (
                  <TextInput
                    style={{ borderWidth: 1, borderColor: theme.line, borderRadius: 8, padding: 12, color: theme.text, height: 100 }}
                    value={answers[q.id] || ""}
                    onChangeText={(val) => handleAnswerChange(q.id, val)}
                    multiline
                    textAlignVertical="top"
                    placeholder="Votre réponse..."
                    placeholderTextColor={theme.muted}
                  />
                )}
              </View>
            ))}

            <View style={{ marginTop: 8 }}>
              <PrimaryButton icon="send" label={submitting ? "Envoi en cours..." : "Envoyer mes réponses"} onPress={handleSubmit} ui={ui} />
            </View>
          </ScrollView>
        </View>
      </ScrollView>
    </Modal>
  );
}

export function SurveysScreen({ ui, triggerFeedback }: { ui: Ui, triggerFeedback: (label?: string) => void }) {
  const { styles, theme } = ui;
  const [surveys, setSurveys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedSurvey, setSelectedSurvey] = useState<any>(null);

  const fetchSurveys = async () => {
    try {
      setLoading(true);
      const data = await surveysService.fetchMySurveys();
      setSurveys(data);
    } catch (e) {
      console.warn("Erreur chargement sondages:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSurveys();
  }, []);

  const handleOpenSurvey = (survey: any) => {
    setSelectedSurvey(survey);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    setModalOpen(false);
    triggerFeedback("Merci ! Vos réponses ont bien été enregistrées.");
    setSelectedSurvey(null);
    fetchSurveys();
  };

  return (
    <View style={styles.stack}>
      <SurveyResponseModal open={modalOpen} survey={selectedSurvey} onClose={() => setModalOpen(false)} onSubmit={handleSubmit} ui={ui} />

      <SectionHeader icon="clipboard" title="Sondages Internes" ui={ui} />
      {loading ? (
        <ActivityIndicator color={theme.sky} style={{ marginVertical: 20 }} />
      ) : surveys.length === 0 ? (
        <Card ui={ui}>
          <Text style={styles.mutedText}>Aucun sondage disponible pour le moment.</Text>
        </Card>
      ) : surveys.map((s) => (
        <Card key={s.id} ui={ui}>
          <View style={styles.rowBetween}>
            <Text style={styles.cardTitle}>{s.title}</Text>
            <StatusBadge label={s.has_responded ? 'Terminé' : 'Nouveau'} tone={s.has_responded ? 'success' : 'info'} ui={ui} />
          </View>
          <Text style={[styles.bodyText, { marginTop: 8 }]}>{s.description}</Text>
          <View style={{ marginTop: 16 }}>
            <PrimaryButton
              icon={s.has_responded ? 'check' : 'edit-2'}
              label={s.has_responded ? 'Réponses envoyées' : 'Répondre'}
              onPress={() => !s.has_responded && handleOpenSurvey(s)}
              ui={ui}
            />
          </View>
        </Card>
      ))}
    </View>
  );
}


export function TimesheetScreen({ ui, triggerFeedback }: { ui: Ui, triggerFeedback: (label?: string) => void }) {
  const { styles, theme } = ui;
  const [history, setHistory] = useState<any[]>([]);
  const [todayStatus, setTodayStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchTimesheetData = async () => {
    try {
      setLoading(true);
      const [today, mine] = await Promise.all([
        employeeService.fetchTodayTimesheet(),
        employeeService.fetchMyTimesheets()
      ]);
      setTodayStatus(today);
      setHistory(mine || []);
    } catch (e: any) {
      console.error(e);
      triggerFeedback("Erreur de connexion au serveur");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchTimesheetData();
  }, []);

  const handlePointer = async () => {
    if (actionLoading) return;
    setActionLoading(true);
    try {
      if (!todayStatus || !todayStatus.clock_in) {
        await employeeService.clockIn();
        triggerFeedback("Arrivée enregistrée avec succès");
      } else if (todayStatus && !todayStatus.clock_out) {
        await employeeService.clockOut();
        triggerFeedback("Départ enregistré avec succès");
      }
      await fetchTimesheetData();
    } catch (e: any) {
      const errorMsg = e.response?.data?.detail || "Erreur lors du pointage";
      triggerFeedback(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  const getButtonState = () => {
    if (loading) return { label: "Chargement...", icon: "loader", color: theme.muted, disabled: true };
    if (!todayStatus || !todayStatus.clock_in) {
      return { label: "Signaler mon Arrivée", icon: "play", color: theme.sky, disabled: false };
    }
    if (todayStatus && !todayStatus.clock_out) {
      return { label: "Signaler mon Départ", icon: "square", color: theme.rose, disabled: false };
    }
    return { label: "Journée terminée", icon: "check", color: theme.emerald, disabled: true };
  };

  const btnState = getButtonState();

  const formatTime = (isoString?: string) => {
    if (!isoString) return "--:--";
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <View style={styles.stack}>
      <Card ui={ui}>
        <View style={{ alignItems: "center", paddingVertical: 12 }}>
          <View style={{ backgroundColor: theme.sky + "15", padding: 16, borderRadius: 50, marginBottom: 16 }}>
            <Feather name="clock" size={32} color={theme.sky} />
          </View>
          <Text style={[styles.heroTitle, { fontSize: 22, textAlign: "center", marginBottom: 8 }]}>Chronomètre de Travail</Text>
          <Text style={[styles.mutedText, { textAlign: "center", marginBottom: 16, lineHeight: 20 }]}>
            Le système enregistre automatiquement l'heure exacte.{"\n"}Aucune modification manuelle n'est possible.
          </Text>
          <View style={{ backgroundColor: theme.sky + "15", paddingHorizontal: 16, paddingVertical: 8, borderRadius: 12 }}>
            <Text style={{ color: theme.sky, fontWeight: "600", fontSize: 13 }}>Horaires obligatoires : 08h00 - 16h00 (8 heures)</Text>
          </View>
        </View>

        <Pressable
          onPress={handlePointer}
          disabled={actionLoading || btnState.disabled}
          style={{
            backgroundColor: btnState.disabled ? theme.muted + "40" : btnState.color,
            paddingVertical: 16,
            borderRadius: 12,
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            marginTop: 8,
            opacity: actionLoading ? 0.7 : 1
          }}
        >
          {actionLoading ? (
            <ActivityIndicator color="#fff" style={{ marginRight: 8 }} />
          ) : (
            <Feather name={btnState.icon as any} size={20} color={btnState.disabled ? theme.text + "50" : "#fff"} style={{ marginRight: 8 }} />
          )}
          <Text style={{ color: btnState.disabled ? theme.text + "50" : "#fff", fontWeight: "700", fontSize: 16 }}>
            {actionLoading ? "Enregistrement..." : btnState.label}
          </Text>
        </Pressable>
      </Card>

      <SectionHeader icon="list" title="Historique de mes pointages" ui={ui} />

      {loading ? (
        <ActivityIndicator color={theme.sky} style={{ marginTop: 24 }} />
      ) : history.length === 0 ? (
        <Card ui={ui} style={{ alignItems: "center", paddingVertical: 32 }}>
          <Feather name="inbox" size={32} color={theme.muted} style={{ marginBottom: 12 }} />
          <Text style={styles.mutedText}>Aucun pointage enregistré.</Text>
        </Card>
      ) : (
        history.map((ts) => (
          <Card key={ts.id} ui={ui} style={{ padding: 16 }}>
            <View style={styles.rowBetween}>
              <View>
                <Text style={styles.bodyStrong}>{new Date(ts.date).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}</Text>
                <View style={[styles.rowStart, { marginTop: 4 }]}>
                  <Text style={[styles.mutedText, { fontSize: 13 }]}>{formatTime(ts.clock_in)} - {formatTime(ts.clock_out)}</Text>
                </View>
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Text style={[styles.bodyStrong, { color: ts.hours_worked >= 8 ? theme.emerald : theme.text }]}>
                  {ts.hours_worked ? `${ts.hours_worked}h` : "En cours"}
                </Text>
                <View style={{ marginTop: 4 }}>
                  <StatusBadge label={ts.status} tone={ts.status === "PENDING" ? "warning" : "success"} ui={ui} />
                </View>
              </View>
            </View>
          </Card>
        ))
      )}
    </View>
  );
}

/* =========================================================================================
   Ã‰CRANS ADMINISTRATEUR (PÃ©rimÃ¨tre Technique et SÃ©curitaire Exclusif)
========================================================================================= */


