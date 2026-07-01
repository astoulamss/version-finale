import React, { useState, useEffect, useMemo } from 'react';

import { View, Text, ScrollView, Pressable, ActivityIndicator, TextInput, Platform, StyleSheet, Modal, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Ui } from '../types';
import { Card } from '../components/ui/Card';
import { PrimaryButton } from '../components/ui/Button';
import { interviewsService } from '../services/interviews.service';
import api from '../services/api';

export function HrInterviewsScreen({ ui }: { ui: Ui }) {
  const { styles, theme } = ui;
  const [tab, setTab] = useState<'form' | 'history'>('form');
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [interviews, setInterviews] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  
  // Form state
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [reviewDate, setReviewDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [rating, setRating] = useState<number>(0);
  const [comments, setComments] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);

  // History state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRating, setFilterRating] = useState<number | null>(null);

  // Modals state for Native Selectors
  const [showEmployeePicker, setShowEmployeePicker] = useState(false);
  const [showRatingPicker, setShowRatingPicker] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [intRes, empRes, posRes] = await Promise.all([
        interviewsService.fetchInterviews(),
        api.get('/api/employees/'),
        api.get('/api/employees/positions')
      ]);
      setInterviews(intRes || []);
      setEmployees(empRes.data || []);
      setPositions(posRes.data || []);
    } catch (e) {
      console.error("Error loading interviews data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async () => {
    if (!selectedEmployeeId || rating === 0) return;
    try {
      setSubmitting(true);
      await interviewsService.createInterview({
        employee_id: selectedEmployeeId,
        review_date: reviewDate,
        performance_rating: rating,
        comments
      });
      alert('Entretien enregistré avec succès');
      setSelectedEmployeeId(null);
      setRating(0);
      setComments('');
      await loadData();
      setTab('history');
    } catch (e: any) {
      alert(e.response?.data?.detail || "Erreur lors de l'enregistrement de l'entretien");
    } finally {
      setSubmitting(false);
    }
  };

  const getEmployeeDetails = (id: number) => {
    const emp = employees.find(e => e.id === id);
    if (!emp) return { name: `ID: ${id}`, position: '-' };
    
    const name = emp.user ? `${emp.user.prenom} ${emp.user.nom}` : `ID: ${id}`;
    
    // Fallbacks for position: 1. Attached object, 2. Looked up array
    const pos = positions.find(p => p.id === emp.position_id);
    const positionName = emp.position?.title || pos?.title || '-';
    
    return { name, position: positionName };
  };

  const filteredHistory = useMemo(() => {
    let result = interviews;
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      result = result.filter(inv => {
        const details = getEmployeeDetails(inv.employee_id);
        return details.name.toLowerCase().includes(q);
      });
    }
    if (filterRating !== null) {
      result = result.filter(inv => inv.performance_rating === filterRating);
    }
    return result;
  }, [interviews, employees, searchQuery, filterRating, positions]);

  if (loading && employees.length === 0) {
    return (
      <View style={[styles.stack, { flex: 1, justifyContent: "center" }]}>
        <ActivityIndicator color={theme.sky} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      
      <View style={{ flexDirection: 'row', marginBottom: 20, backgroundColor: theme.surfaceAlt, padding: 4, borderRadius: 10, alignSelf: 'flex-start' }}>
        <Pressable 
          onPress={() => setTab('form')}
          style={{ paddingHorizontal: 24, paddingVertical: 10, borderRadius: 6, backgroundColor: tab === 'form' ? theme.background : 'transparent', shadowColor: tab === 'form' ? '#000' : 'transparent', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: tab === 'form' ? 2 : 0 }}
        >
          <Text style={{ fontWeight: '700', color: tab === 'form' ? theme.navy : theme.muted, fontSize: 14 }}>Nouvel Entretien</Text>
        </Pressable>
        <Pressable 
          onPress={() => setTab('history')}
          style={{ paddingHorizontal: 24, paddingVertical: 10, borderRadius: 6, backgroundColor: tab === 'history' ? theme.background : 'transparent', shadowColor: tab === 'history' ? '#000' : 'transparent', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2, elevation: tab === 'history' ? 2 : 0 }}
        >
          <Text style={{ fontWeight: '700', color: tab === 'history' ? theme.navy : theme.muted, fontSize: 14 }}>Historique</Text>
        </Pressable>
      </View>

      {tab === 'form' ? (
        <Card ui={ui}>
          <View style={styles.rowStart}>
            <View style={[styles.actionIcon, { backgroundColor: theme.sky + '20' }]}>
              <Feather name="mic" size={20} color={theme.sky} />
            </View>
            <Text style={[styles.cardTitle, { fontSize: 20 }]}>Saisir un nouvel entretien</Text>
          </View>

          <View style={{ marginTop: 24, gap: 20 }}>
            {/* Employé Evalué */}
            <View>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Employé évalué <Text style={{ color: theme.rose }}>*</Text></Text>
              {Platform.OS === 'web' ? (
                <select 
                  value={selectedEmployeeId || ''} 
                  onChange={(e) => setSelectedEmployeeId(Number(e.target.value))}
                  style={{ width: '100%', padding: 12, borderRadius: 8, borderColor: theme.line, borderWidth: 1, backgroundColor: theme.background, color: theme.text, fontSize: 14, outline: 'none' }}
                >
                  <option value="" disabled>Sélectionner un employé...</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={emp.id}>
                      {emp.user ? `${emp.user.prenom} ${emp.user.nom}` : `Employee ID: ${emp.id}`}
                    </option>
                  ))}
                </select>
              ) : (
                <Pressable
                  onPress={() => setShowEmployeePicker(true)}
                  style={{ width: '100%', padding: 12, borderRadius: 8, borderColor: theme.line, borderWidth: 1, backgroundColor: theme.background, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <Text style={{ color: selectedEmployeeId ? theme.text : theme.muted }}>
                    {selectedEmployeeId 
                      ? (employees.find(e => e.id === selectedEmployeeId)?.user ? `${employees.find(e => e.id === selectedEmployeeId)?.user.prenom} ${employees.find(e => e.id === selectedEmployeeId)?.user.nom}` : `Employee ID: ${selectedEmployeeId}`)
                      : "Sélectionner un employé..."}
                  </Text>
                  <Feather name="chevron-down" size={18} color={theme.muted} />
                </Pressable>
              )}
            </View>

            {/* Date de l'entretien */}
            <View>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Date de l'entretien <Text style={{ color: theme.rose }}>*</Text></Text>
              <TextInput
                style={{ borderWidth: 1, borderColor: theme.line, borderRadius: 8, padding: 12, backgroundColor: theme.background, color: theme.text, fontSize: 14 }}
                value={reviewDate}
                onChangeText={setReviewDate}
                placeholder="YYYY-MM-DD"
              />
            </View>

            {/* Note de performance */}
            <View>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Note de performance (sur 5) <Text style={{ color: theme.rose }}>*</Text></Text>
              <View style={{ flexDirection: 'row', gap: 12 }}>
                {[1, 2, 3, 4, 5].map(star => (
                  <Pressable key={star} onPress={() => setRating(star)} style={{ padding: 8 }}>
                    <Feather name="star" size={28} color={star <= rating ? '#F59E0B' : theme.line} fill={star <= rating ? '#F59E0B' : 'transparent'} />
                  </Pressable>
                ))}
              </View>
              {rating === 0 && <Text style={{ color: theme.rose, fontSize: 12, marginTop: 4 }}>Une note est requise pour enregistrer l'entretien.</Text>}
            </View>

            {/* Commentaires */}
            <View>
              <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Compte-rendu et commentaires</Text>
              <TextInput
                style={{ borderWidth: 1, borderColor: theme.line, borderRadius: 8, padding: 12, backgroundColor: theme.background, color: theme.text, fontSize: 14, minHeight: 120, textAlignVertical: 'top' }}
                multiline
                numberOfLines={6}
                value={comments}
                onChangeText={setComments}
                placeholder="Décrivez les objectifs, le bilan de l'année, les points d'amélioration..."
                placeholderTextColor={theme.muted}
              />
            </View>
            
            <View style={{ marginTop: 12, alignItems: 'flex-end' }}>
              <View style={{ opacity: (!selectedEmployeeId || rating === 0) ? 0.5 : 1 }}>
                <PrimaryButton 
                  label={submitting ? "Enregistrement..." : "Enregistrer l'entretien"} 
                  onPress={handleSave} 
                  ui={ui} 
                  icon="save" 
                />
              </View>
            </View>
          </View>
        </Card>
      ) : (
        <Card ui={ui} style={{ paddingHorizontal: 0, paddingBottom: 0, overflow: 'hidden' }}>
          <View style={{ paddingHorizontal: 16, marginBottom: 20 }}>
            <View style={[styles.rowBetween, { marginBottom: 16 }]}>
              <View style={styles.rowStart}>
                <Feather name="clock" size={22} color={theme.navy} style={{ marginRight: 8 }} />
                <Text style={[styles.cardTitle, { fontSize: 20 }]}>Historique des entretiens</Text>
              </View>
            </View>
            
            <View style={[styles.rowStart, { gap: 12 }]}>
              {/* Search */}
              <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', backgroundColor: theme.background, borderColor: theme.line, borderWidth: 1, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 8 }}>
                <Feather name="search" size={16} color={theme.muted} style={{ marginRight: 8 }} />
                <TextInput
                  style={{ flex: 1, color: theme.text, fontSize: 14 }}
                  placeholder="Rechercher un employé..."
                  placeholderTextColor={theme.muted}
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                />
              </View>
              
              {/* Filter */}
              <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.background, borderColor: theme.line, borderWidth: 1, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 8 }}>
                <Feather name="filter" size={16} color={theme.muted} style={{ marginRight: 8 }} />
                {Platform.OS === 'web' ? (
                  <select 
                    value={filterRating || ''} 
                    onChange={(e) => setFilterRating(e.target.value ? Number(e.target.value) : null)}
                    style={{ backgroundColor: 'transparent', color: theme.text, fontSize: 14, outline: 'none', border: 'none' }}
                  >
                    <option value="">Toutes les notes</option>
                    {[1, 2, 3, 4, 5].map(r => <option key={r} value={r}>{r} étoiles</option>)}
                  </select>
                ) : (
                  <Pressable onPress={() => setShowRatingPicker(true)}>
                    <Text style={{ color: filterRating ? theme.text : theme.muted, fontSize: 14 }}>
                      {filterRating ? `${filterRating} étoiles` : "Toutes les notes"}
                    </Text>
                  </Pressable>
                )}
              </View>
            </View>
          </View>

          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={{ minWidth: 900 }}>
              <View style={{ flexDirection: 'row', backgroundColor: theme.background, paddingVertical: 14, paddingHorizontal: 20, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                <Text style={[styles.metaText, { flex: 2, fontWeight: '700' }]}>Date</Text>
                <Text style={[styles.metaText, { flex: 3, fontWeight: '700' }]}>Employé évalué</Text>
                <Text style={[styles.metaText, { flex: 3, fontWeight: '700' }]}>Poste / Rôle</Text>
                <Text style={[styles.metaText, { flex: 2, fontWeight: '700' }]}>Performance</Text>
                <Text style={[styles.metaText, { flex: 4, fontWeight: '700' }]}>Compte-rendu</Text>
              </View>
              
              {filteredHistory.length === 0 ? (
                <View style={{ padding: 40, alignItems: 'center' }}>
                  <Feather name="inbox" size={48} color={theme.line} style={{ marginBottom: 16 }} />
                  <Text style={styles.mutedText}>Aucun entretien trouvé.</Text>
                </View>
              ) : (
                filteredHistory.map((inv, idx) => {
                  const details = getEmployeeDetails(inv.employee_id);
                  return (
                    <View key={inv.id} style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 16, paddingHorizontal: 20, borderBottomWidth: idx < filteredHistory.length - 1 ? 1 : 0, borderBottomColor: theme.line }}>
                      
                      <View style={{ flex: 2 }}>
                        <Text style={styles.bodyText}>{inv.review_date}</Text>
                      </View>
                      
                      <View style={{ flex: 3 }}>
                        <Text style={styles.bodyStrong}>{details.name}</Text>
                      </View>
                      
                      <View style={{ flex: 3 }}>
                        <Text style={styles.bodyText}>{details.position}</Text>
                      </View>
                      
                      <View style={{ flex: 2, flexDirection: 'row', alignItems: 'center', gap: 2 }}>
                        {[1, 2, 3, 4, 5].map(star => (
                          <Feather key={star} name="star" size={12} color={star <= inv.performance_rating ? '#F59E0B' : theme.line} fill={star <= inv.performance_rating ? '#F59E0B' : 'transparent'} />
                        ))}
                      </View>
                      
                      <View style={{ flex: 4 }}>
                        <Text style={styles.bodyText} numberOfLines={2}>{inv.comments || '-'}</Text>
                      </View>
                      
                    </View>
                  );
                })
              )}
            </View>
          </ScrollView>
        </Card>
      )}
      
      {/* Picker Modal for Employee (Mobile) */}
      <Modal visible={showEmployeePicker} transparent animationType="slide" onRequestClose={() => setShowEmployeePicker(false)}>
        <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <View style={{ backgroundColor: theme.background, borderTopLeftRadius: 16, borderTopRightRadius: 16, maxHeight: '80%' }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
              <Text style={styles.cardTitle}>Sélectionner un employé</Text>
              <Pressable onPress={() => setShowEmployeePicker(false)} style={{ padding: 4 }}>
                <Feather name="x" size={24} color={theme.navy} />
              </Pressable>
            </View>
            <ScrollView style={{ padding: 16 }}>
              {employees.map(emp => (
                <TouchableOpacity 
                  key={emp.id} 
                  style={{ paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: theme.line }}
                  onPress={() => {
                    setSelectedEmployeeId(emp.id);
                    setShowEmployeePicker(false);
                  }}
                >
                  <Text style={[styles.bodyText, selectedEmployeeId === emp.id && { color: theme.sky, fontWeight: '700' }]}>
                    {emp.user ? `${emp.user.prenom} ${emp.user.nom}` : `Employee ID: ${emp.id}`}
                  </Text>
                </TouchableOpacity>
              ))}
              <View style={{ height: 40 }} />
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Picker Modal for Rating Filter (Mobile) */}
      <Modal visible={showRatingPicker} transparent animationType="fade" onRequestClose={() => setShowRatingPicker(false)}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <View style={{ backgroundColor: theme.background, borderRadius: 12, width: 300, overflow: 'hidden' }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
              <Text style={styles.cardTitle}>Filtrer par note</Text>
              <Pressable onPress={() => setShowRatingPicker(false)}>
                <Feather name="x" size={20} color={theme.navy} />
              </Pressable>
            </View>
            <TouchableOpacity 
              style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}
              onPress={() => { setFilterRating(null); setShowRatingPicker(false); }}
            >
              <Text style={[styles.bodyText, filterRating === null && { color: theme.sky, fontWeight: '700' }]}>Toutes les notes</Text>
            </TouchableOpacity>
            {[1, 2, 3, 4, 5].map(r => (
              <TouchableOpacity 
                key={r} 
                style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}
                onPress={() => { setFilterRating(r); setShowRatingPicker(false); }}
              >
                <Text style={[styles.bodyText, filterRating === r && { color: theme.sky, fontWeight: '700' }]}>{r} étoiles</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </Modal>
      
    </ScrollView>
  );
}
