import React, { useState, useEffect, useMemo } from 'react';

import { View, Text, ScrollView, Pressable, ActivityIndicator, TextInput, Platform } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Ui } from '../types';
import { Card } from '../components/ui/Card';
import { documentsService } from '../services/documents.service';
import api from '../services/api';

export function HrDocumentsScreen({ ui }: { ui: Ui }) {
  const { styles, theme } = ui;
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [documents, setDocuments] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [docsRes, empRes] = await Promise.all([
        documentsService.fetchAllDocuments(),
        api.get('/api/employees/')
      ]);
      setDocuments(docsRes || []);
      setEmployees(empRes.data || []);
    } catch (e) {
      console.error("Error loading HR documents data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSend = async (id: number) => {
    try {
      await documentsService.sendDocument(id);
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Erreur lors de l'envoi");
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Êtes-vous sûr de vouloir supprimer ce document ?")) {
      try {
        await documentsService.deleteDocument(id);
        loadData();
      } catch (e: any) {
        alert(e.response?.data?.detail || "Erreur lors de la suppression");
      }
    }
  };

  const handleDownload = async (doc: any) => {
    try {
      const safeTitle = doc.title.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_');
      const filename = `${safeTitle}.pdf`;
      await documentsService.downloadDocument(doc.id, filename);
    } catch (e: any) {
      alert(e.response?.data?.detail || "Erreur lors du téléchargement");
    }
  };

  const getEmployeeName = (id: number) => {
    const emp = employees.find(e => e.user_id === id);
    if (emp && emp.user) return `${emp.user.prenom} ${emp.user.nom}`;
    return `ID: ${id}`;
  };

  const formatDate = (isoString: string) => {
    if (!isoString) return "-";
    const date = new Date(isoString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const mins = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${mins}`;
  };

  const filteredDocuments = useMemo(() => {
    let result = documents;
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      result = result.filter(doc => {
        const titleMatch = doc.title?.toLowerCase().includes(q);
        const nameMatch = getEmployeeName(doc.employee_id).toLowerCase().includes(q);
        return titleMatch || nameMatch;
      });
    }
    // Sort by created_at descending
    return result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [documents, employees, searchQuery]);

  if (loading && documents.length === 0) {
    return (
      <View style={[styles.stack, { flex: 1, justifyContent: "center" }]}>
        <ActivityIndicator color={theme.sky} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      
      <Card ui={ui} style={{ marginBottom: 40, paddingHorizontal: 0, paddingBottom: 0, overflow: 'hidden' }}>
        
        {/* HEADER SECTION */}
        <View style={{ paddingHorizontal: 16, marginBottom: 20 }}>
          <View style={[styles.rowBetween, { marginBottom: 16 }]}>
            <View style={styles.rowStart}>
              <Feather name="file-text" size={22} color={theme.navy} style={{ marginRight: 8 }} />
              <Text style={[styles.cardTitle, { fontSize: 20 }]}>Dossier Documentaire</Text>
            </View>
            <View style={styles.rowStart}>
              <Pressable style={{ backgroundColor: theme.surfaceAlt, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8 }}>
                <Text style={{ color: theme.navy, fontWeight: '700', fontSize: 13 }}>Importer Fichier</Text>
              </Pressable>
              <Pressable style={{ backgroundColor: theme.surfaceAlt, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8 }}>
                <Text style={{ color: theme.navy, fontWeight: '700', fontSize: 13 }}>Créer Manuel</Text>
              </Pressable>
              <Pressable style={{ backgroundColor: '#6366F1', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Feather name="zap" size={14} color="#ffffff" />
                <Text style={{ color: '#ffffff', fontWeight: '700', fontSize: 13 }}>Générer par IA</Text>
              </Pressable>
            </View>
          </View>
          
          <View style={styles.rowBetween}>
            <Text style={[styles.bodyStrong, { fontSize: 16 }]}>Documents générés ou importés par les RH</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.background, borderColor: theme.line, borderWidth: 1, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 6, width: 300 }}>
              <Feather name="search" size={14} color={theme.muted} style={{ marginRight: 8 }} />
              <TextInput
                style={{ flex: 1, color: theme.text, fontSize: 13 }}
                placeholder="Rechercher par titre ou employé..."
                placeholderTextColor={theme.muted}
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
            </View>
          </View>
        </View>

        {/* DATA TABLE */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={{ minWidth: 1000 }}>
              {/* Header Row */}
              <View style={{ flexDirection: 'row', backgroundColor: theme.background, paddingVertical: 14, paddingHorizontal: 20, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                <Text style={[styles.metaText, { flex: 3, fontWeight: '700' }]}>Titre</Text>
                <Text style={[styles.metaText, { flex: 2, fontWeight: '700' }]}>Destinataire</Text>
                <Text style={[styles.metaText, { flex: 2, fontWeight: '700' }]}>Catégorie</Text>
                <Text style={[styles.metaText, { flex: 2, fontWeight: '700' }]}>Date</Text>
                <Text style={[styles.metaText, { flex: 1, fontWeight: '700', textAlign: 'center' }]}>Statut</Text>
                <Text style={[styles.metaText, { flex: 1, fontWeight: '700', textAlign: 'center' }]}>Envoi</Text>
                <Text style={[styles.metaText, { flex: 1, fontWeight: '700', textAlign: 'center' }]}>Actions</Text>
              </View>
              
              {/* Data Rows */}
              {filteredDocuments.length === 0 ? (
                <View style={{ padding: 40, alignItems: 'center' }}>
                  <Feather name="folder" size={48} color={theme.line} style={{ marginBottom: 16 }} />
                  <Text style={styles.mutedText}>Aucun document trouvé.</Text>
                </View>
              ) : (
                filteredDocuments.map((doc, idx) => (
                  <View key={doc.id} style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 16, paddingHorizontal: 20, borderBottomWidth: idx < filteredDocuments.length - 1 ? 1 : 0, borderBottomColor: theme.line }}>
                    
                    {/* Titre */}
                    <View style={{ flex: 3, flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      {doc.generated_by_ai && <Feather name="zap" size={14} color="#6366F1" />}
                      <Text style={[styles.bodyStrong, { color: theme.navy }]} numberOfLines={1}>
                        {doc.title.replace(new RegExp(`[\\s-]*${getEmployeeName(doc.employee_id)}$`, 'i'), '')}
                      </Text>
                    </View>
                    
                    {/* Destinataire */}
                    <View style={{ flex: 2 }}>
                      <Text style={styles.bodyText} numberOfLines={1}>{getEmployeeName(doc.employee_id)}</Text>
                    </View>
                    
                    {/* Catégorie */}
                    <View style={{ flex: 2 }}>
                      <Text style={styles.bodyText} numberOfLines={1}>{doc.document_type || '-'}</Text>
                    </View>
                    
                    {/* Date */}
                    <View style={{ flex: 2 }}>
                      <Text style={styles.bodyText}>{formatDate(doc.created_at)}</Text>
                    </View>
                    
                    {/* Statut */}
                    <View style={{ flex: 1, alignItems: 'center' }}>
                      <View style={{ backgroundColor: theme.emeraldSoft, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 999 }}>
                        <Text style={{ color: theme.emerald, fontSize: 12, fontWeight: '700', textTransform: 'capitalize' }}>
                          {doc.status || 'Final'}
                        </Text>
                      </View>
                    </View>
                    
                    {/* Envoi */}
                    <View style={{ flex: 1, alignItems: 'center' }}>
                      {doc.is_sent ? (
                        <Text style={{ color: theme.emerald, fontSize: 13, fontWeight: '600' }}>✓ Envoyé</Text>
                      ) : (
                        <Text style={{ color: theme.muted, fontSize: 13 }}>En attente</Text>
                      )}
                    </View>
                    
                    {/* Actions */}
                    <View style={{ flex: 1, flexDirection: 'row', justifyContent: 'center', gap: 8 }}>
                      <Pressable style={{ padding: 6, backgroundColor: theme.surfaceAlt, borderRadius: 6 }}>
                        <Feather name="eye" size={16} color={theme.navy} />
                      </Pressable>
                      <Pressable onPress={() => handleDownload(doc)} style={{ padding: 6, backgroundColor: theme.surfaceAlt, borderRadius: 6 }}>
                        <Feather name="download" size={16} color={theme.navy} />
                      </Pressable>
                      <Pressable onPress={() => !doc.is_sent && handleSend(doc.id)} style={{ padding: 6, backgroundColor: theme.surfaceAlt, borderRadius: 6, opacity: doc.is_sent ? 0.3 : 1 }}>
                        <Feather name="send" size={16} color={theme.sky} />
                      </Pressable>
                      <Pressable onPress={() => handleDelete(doc.id)} style={{ padding: 6, backgroundColor: theme.surfaceAlt, borderRadius: 6 }}>
                        <Feather name="trash-2" size={16} color={theme.muted} />
                      </Pressable>
                    </View>
                    
                  </View>
                ))
              )}
            </View>
          </ScrollView>
      </Card>
      
    </ScrollView>
  );
}
