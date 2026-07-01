

import React, { useState, useEffect } from "react";
import { View, Text, ScrollView, ActivityIndicator, TextInput, Pressable } from "react-native";
import * as DocumentPicker from 'expo-document-picker';
import { Feather } from "@expo/vector-icons";
import { Card } from "../components/ui/Card";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Ui, DocumentResponse } from "../types";
import { fetchMyDocuments } from "../services/dashboard.service";
import { uploadRealDocument } from "../services/rh.service";
import { downloadAndOpenDocument } from "../utils/document.utils";

const DOCUMENT_TYPES = [
  "RIB",
  "Certificat médical",
  "RIB / IBAN",
  "Pièce d'identité",
  "Passeport",
  "Diplôme",
  "Autre"
];

// Valeur par défaut pour forcer l'utilisateur à choisir
const DEFAULT_TYPE = "Sélectionner un type";

export function DocumentsScreen({ ui, triggerFeedback, onNavigate }: { ui: Ui; triggerFeedback?: (msg: string) => void; onNavigate?: (view: any) => void }) {
  const { styles, theme } = ui;
  
  // Section 1: Quick actions Hub
  const quickActions = [
    { id: "assistant", icon: "message-square", label: "Assistant IA" },
    { id: "leave", icon: "calendar", label: "Congés" },
    { id: "absences", icon: "frown", label: "Absences" },
    { id: "contract", icon: "file-text", label: "Contrats" },
    { id: "surveys", icon: "clipboard", label: "Sondages" },
    { id: "employee_trainings", icon: "award", label: "Formations" },
    { id: "requests", icon: "tag", label: "Mes Demandes" },
    { id: "onboarding", icon: "play-circle", label: "Onboarding" },
    { id: "employee_offboarding", icon: "log-out", label: "Offboarding" },
  ];

  // Section 2: Upload State
  const [title, setTitle] = useState("");
  const [selectedType, setSelectedType] = useState(DEFAULT_TYPE);
  const [fileSelected, setFileSelected] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Section 3: List State
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadDocs = async () => {
    try {
      setIsLoading(true);
      const docs = await fetchMyDocuments();
      setDocuments(docs ? [...docs].reverse() : []);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const [fileUri, setFileUri] = useState<string | null>(null);
  const [fileType, setFileType] = useState<string>("application/pdf");

  const handleFileSelect = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/jpeg', 'image/png'],
        copyToCacheDirectory: true,
      });

      if (result.canceled === false && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setFileSelected(asset.name);
        setFileUri(asset.uri);
        setFileType(asset.mimeType || 'application/pdf');
      }
    } catch (error) {
      console.error("Erreur lors de la sélection du document", error);
    }
  };

  const handleSubmit = async () => {
    if (!title.trim() || selectedType === DEFAULT_TYPE || !fileSelected) {
      setUploadError("Veuillez remplir tous les champs obligatoires et sélectionner un fichier.");
      return;
    }

    setIsSubmitting(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("document_type", selectedType);
      
      if (fileUri) {
        // @ts-ignore
        formData.append("file", {
          uri: fileUri,
          name: fileSelected || "document.pdf",
          type: fileType
        });
      } else {
        throw new Error("Aucun fichier réel n'a été sélectionné");
      }
      
      await uploadRealDocument(formData);
      
      setUploadSuccess(true);
      setTitle("");
      setSelectedType(DEFAULT_TYPE);
      setFileSelected(null);
      setFileUri(null);
      if (triggerFeedback) triggerFeedback("Document envoyé avec succès");
      
      loadDocs();
    } catch (error: any) {
      console.error("API Error Response:", error.response?.data);
      console.error(error);
      setUploadError(`Erreur: ${error.response?.data?.detail?.[0]?.msg || "Une erreur est survenue lors de l'envoi du document."}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        
        {/* Upload Card */}
        <Card ui={ui}>
          <Text style={styles.cardTitle}>Ajouter un document RH</Text>
          <Text style={styles.mutedText}>Envoyez vos justificatifs, RIB, arrêts maladie, etc.</Text>
          
          <View style={{ marginTop: 16, gap: 12 }}>
            <TextInput
              style={styles.fieldInput}
              placeholder="Titre du document (ex: RIB 2026)"
              placeholderTextColor={theme.muted}
              value={title}
              onChangeText={setTitle}
            />

            {/* Dropdown for type */}
            <View style={{ zIndex: 10 }}>
              <Pressable 
                onPress={() => setDropdownOpen(!dropdownOpen)}
                style={[styles.fieldInput, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}
              >
                <Text style={{ color: selectedType === DEFAULT_TYPE ? theme.muted : theme.text }}>{selectedType}</Text>
                <Feather name={dropdownOpen ? "chevron-up" : "chevron-down"} size={18} color={theme.muted} />
              </Pressable>
              
              {dropdownOpen && (
                <View style={{ position: 'absolute', top: 50, left: 0, right: 0, backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 8, padding: 4, zIndex: 20 }}>
                  {DOCUMENT_TYPES.map(type => (
                    <Pressable 
                      key={type} 
                      onPress={() => { setSelectedType(type); setDropdownOpen(false); }}
                      style={{ padding: 12, borderRadius: 6, backgroundColor: selectedType === type ? theme.sky + '20' : 'transparent' }}
                    >
                      <Text style={{ color: selectedType === type ? theme.sky : theme.text, fontWeight: selectedType === type ? '600' : 'normal' }}>{type}</Text>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>

            <Pressable onPress={handleFileSelect} style={{ borderWidth: 1, borderStyle: 'dashed', borderColor: theme.sky, borderRadius: 8, padding: 16, alignItems: 'center', backgroundColor: theme.sky + '05' }}>
              <Feather name="upload-cloud" size={24} color={theme.sky} style={{ marginBottom: 8 }} />
              <Text style={{ color: theme.sky, fontWeight: '600', textAlign: 'center' }}>
                {fileSelected ? fileSelected : "Parcourir vos fichiers"}
              </Text>
              <Text style={{ fontSize: 12, color: theme.muted, marginTop: 4 }}>PDF, JPEG, PNG (max 5MB)</Text>
            </Pressable>

            {uploadError && <Text style={{ color: theme.rose, fontSize: 13, marginTop: 4 }}>{uploadError}</Text>}
            {uploadSuccess && <Text style={{ color: theme.emerald, fontSize: 13, marginTop: 4 }}>Document envoyé avec succès !</Text>}

            <PrimaryButton
              label={isSubmitting ? "Envoi en cours..." : "Envoyer le document"}
              icon="send"
              onPress={handleSubmit}
              ui={ui}
            />
          </View>
        </Card>

        {/* List of documents */}
        <Text style={[styles.sectionTitle, { marginTop: 24, marginBottom: 12 }]}>Mes documents envoyés</Text>

        {isLoading ? (
          <ActivityIndicator color={theme.sky} style={{ margin: 24 }} />
        ) : documents.length === 0 ? (
          <EmptyState icon="folder" title="Aucun document" text="Vous n'avez pas encore envoyé de documents." ui={ui} />
        ) : (
          <View style={{ gap: 12 }}>
            {documents.map((doc, idx) => (
              <Card key={idx} ui={ui} style={{ padding: 12 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                    <View style={{ backgroundColor: theme.surfaceAlt, padding: 10, borderRadius: 8, marginRight: 12 }}>
                      <Feather name="file-text" size={20} color={theme.sky} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.bodyStrong, { fontSize: 14 }]} numberOfLines={1}>
                        {(doc as any).title || (doc as any).document_type?.name || "Document RH"}
                      </Text>
                      <Text style={[styles.mutedText, { fontSize: 12, marginTop: 2 }]}>
                        {(doc as any).document_type?.name || "Autre"} • {new Date(doc.created_at).toLocaleDateString()}
                      </Text>
                    </View>
                  </View>
                  <Pressable 
                    onPress={() => downloadAndOpenDocument(doc.id.toString(), (doc as any).title || "Document", triggerFeedback)}
                    style={{ padding: 8, backgroundColor: theme.sky + '15', borderRadius: 8 }}
                  >
                    <Feather name="download" size={16} color={theme.sky} />
                  </Pressable>
                </View>
              </Card>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}
