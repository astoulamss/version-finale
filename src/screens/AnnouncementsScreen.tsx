import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, TextInput, Pressable, ActivityIndicator } from "react-native";
import { Feather } from "@expo/vector-icons";
import { EmployeeProfile, Ui, ViewId } from "../types";
import { Card } from "../components/ui/Card";
import { SectionHeader } from "../components/ui/SectionHeader";
import { BackButton } from "../components/ui/BackButton";

import { announcementService, AnnouncementResponse, RecipientsListResponse } from "../services/announcements.service";

interface Props {
  sessionProfile: EmployeeProfile;
  triggerFeedback: (msg?: string) => void;
  ui: Ui;
  onNavigate: (view: ViewId) => void;
}

export const AnnouncementsScreen: React.FC<Props> = ({ sessionProfile, triggerFeedback, ui, onNavigate }) => {
  const { theme, styles } = ui;
  
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [recipientsData, setRecipientsData] = useState<RecipientsListResponse | null>(null);
  const [history, setHistory] = useState<AnnouncementResponse[]>([]);
  
  // Form state
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [recipientType, setRecipientType] = useState<'GLOBAL' | 'DEPARTMENT' | 'EMPLOYEE'>('GLOBAL');
  const [recipientId, setRecipientId] = useState<number | undefined>(undefined);
  const [selectedRecipientName, setSelectedRecipientName] = useState("Tous les collaborateurs (Global)");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [recipients, hist] = await Promise.all([
        announcementService.getRecipients(),
        announcementService.getHistory()
      ]);
      setRecipientsData(recipients);
      setHistory(hist);
    } catch (error) {
      console.error("Failed to load announcements data", error);
      triggerFeedback("Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!title.trim() || !content.trim()) {
      triggerFeedback("Veuillez remplir le titre et le message");
      return;
    }
    
    if (recipientType !== 'GLOBAL' && !recipientId) {
      triggerFeedback("Veuillez sélectionner un destinataire spécifique");
      return;
    }

    try {
      setSending(true);
      await announcementService.sendAnnouncement({
        title,
        content,
        recipient_type: recipientType,
        recipient_id: recipientId
      });
      triggerFeedback("Annonce envoyée avec succès");
      setTitle("");
      setContent("");
      loadData();
    } catch (error) {
      console.error("Failed to send announcement", error);
      triggerFeedback("Erreur lors de l'envoi");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.background }}>
        <ActivityIndicator size="large" color={theme.sky} />
      </View>
    );
  }

  const selectRecipient = (type: 'GLOBAL' | 'DEPARTMENT' | 'EMPLOYEE', id: number | undefined, name: string) => {
    setRecipientType(type);
    setRecipientId(id);
    setSelectedRecipientName(name);
    setDropdownOpen(false);
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        
        <View style={styles.rowStart}>
          <View style={{ marginLeft: -8, marginRight: 8 }}>
            <BackButton onPress={() => onNavigate('operations')} ui={ui} />
          </View>
          <View>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Communications</Text>
            <Text style={styles.mutedText}>Envoyez des annonces et consultez l'historique.</Text>
          </View>
        </View>

        <Card ui={ui} style={{ marginTop: 24, backgroundColor: theme.sky + '10', borderColor: theme.sky + '30' }}>
          <View style={styles.stack}>
            <View style={{ zIndex: 10 }}>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Destinataire(s)</Text>
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
                <Text style={{ color: theme.text }}>{selectedRecipientName}</Text>
                <Feather name={dropdownOpen ? "chevron-up" : "chevron-down"} size={20} color={theme.text} />
              </Pressable>

              {dropdownOpen && recipientsData && (
                <View style={{
                  backgroundColor: theme.background,
                  borderColor: theme.line,
                  borderWidth: 1,
                  borderTopWidth: 0,
                  borderBottomLeftRadius: 8,
                  borderBottomRightRadius: 8,
                  maxHeight: 250,
                  marginTop: -4,
                }}>
                  <ScrollView nestedScrollEnabled={true}>
                    <Pressable
                      onPress={() => selectRecipient('GLOBAL', undefined, "Tous les collaborateurs (Global)")}
                      style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}
                    >
                      <Text style={{ color: theme.text, fontWeight: 'bold' }}>Tous les collaborateurs (Global)</Text>
                    </Pressable>

                    {recipientsData.departments.length > 0 && (
                      <View style={{ backgroundColor: theme.line + '50', padding: 8 }}>
                        <Text style={{ color: theme.muted, fontSize: 12, fontWeight: 'bold' }}>DÉPARTEMENTS</Text>
                      </View>
                    )}
                    {recipientsData.departments.map(d => (
                      <Pressable
                        key={`dept-${d.id}`}
                        onPress={() => selectRecipient('DEPARTMENT', d.id, `Dép: ${d.name}`)}
                        style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}
                      >
                        <Text style={{ color: theme.text }}>{d.name}</Text>
                      </Pressable>
                    ))}

                    {recipientsData.employees.length > 0 && (
                      <View style={{ backgroundColor: theme.line + '50', padding: 8 }}>
                        <Text style={{ color: theme.muted, fontSize: 12, fontWeight: 'bold' }}>EMPLOYÉS</Text>
                      </View>
                    )}
                    {recipientsData.employees.map(e => (
                      <Pressable
                        key={`emp-${e.id}`}
                        onPress={() => selectRecipient('EMPLOYEE', e.id, e.name)}
                        style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}
                      >
                        <Text style={{ color: theme.text }}>{e.name}</Text>
                      </Pressable>
                    ))}
                  </ScrollView>
                </View>
              )}
            </View>

            <View>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Titre de l'annonce</Text>
              <TextInput
                style={[{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }]}
                placeholder="Ex: Fermeture exceptionnelle des bureaux..."
                placeholderTextColor={theme.muted}
                value={title}
                onChangeText={setTitle}
              />
            </View>

            <View>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Message</Text>
              <TextInput
                style={[{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8, height: 100, textAlignVertical: 'top' }]}
                placeholder="Détails de l'annonce..."
                placeholderTextColor={theme.muted}
                value={content}
                onChangeText={setContent}
                multiline
              />
            </View>

            <Pressable
              style={[
                styles.primaryButton,
                { opacity: sending ? 0.7 : 1, alignSelf: 'flex-end', marginTop: 8 }
              ]}
              onPress={handleSend}
              disabled={sending}
            >
              <View style={styles.rowStart}>
                {sending ? (
                  <ActivityIndicator color={theme.textInverse} style={{ marginRight: 8 }} />
                ) : (
                  <Feather name="send" size={18} color={theme.textInverse} style={{ marginRight: 8 }} />
                )}
                <Text style={styles.primaryButtonText}>
                  {recipientType === 'GLOBAL' ? "Diffuser à tous" : "Envoyer"}
                </Text>
              </View>
            </Pressable>
          </View>
        </Card>

        <SectionHeader icon="clock" title="Historique des Messages Envoyés" ui={ui} />
        
        {history.length === 0 ? (
          <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 40 }}>
            <Feather name="message-square" size={48} color={theme.muted} style={{ marginBottom: 16, opacity: 0.5 }} />
            <Text style={styles.mutedText}>Aucun message envoyé pour le moment.</Text>
          </Card>
        ) : (
          <View style={styles.stack}>
            {history.map(ann => (
              <Card key={ann.id} ui={ui} style={{ padding: 16 }}>
                <View style={[styles.rowBetween, { marginBottom: 8 }]}>
                  <Text style={[styles.bodyStrong, { fontSize: 16 }]} numberOfLines={1}>{ann.title}</Text>
                  <View style={{ backgroundColor: theme.sky + '20', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 }}>
                    <Text style={{ color: theme.sky, fontSize: 12, fontWeight: 'bold' }}>{ann.status}</Text>
                  </View>
                </View>
                <Text style={[styles.metaText, { marginBottom: 8, color: theme.sky }]} numberOfLines={1}>
                  Destinataire : {ann.recipient_name}
                </Text>
                <Text style={[styles.bodyText, { color: theme.text, opacity: 0.8 }]} numberOfLines={3}>
                  {ann.content}
                </Text>
                <View style={[styles.rowBetween, { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: theme.line }]}>
                  <Text style={styles.metaText}>
                    Envoyé par {ann.sender_name}
                  </Text>
                  <Text style={styles.metaText}>
                    {new Date(ann.created_at).toLocaleDateString()} à {new Date(ann.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Text>
                </View>
              </Card>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
};
