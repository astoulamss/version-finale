import React, { useState, useEffect, useMemo } from 'react';

import { View, Text, ScrollView, Pressable, ActivityIndicator, TextInput, Platform } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Ui } from '../types';
import { Card } from '../components/ui/Card';
import { SectionHeader } from '../components/ui/SectionHeader';
import { PrimaryButton, SecondaryButton } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/Badge';
import { leavesService } from '../services/leaves.service';
import { employeeService } from '../services/employee.service';
import api from '../services/api';

export function HrLeavesScreen({ ui }: { ui: Ui }) {
  const { styles, theme } = ui;
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [pendingLeaves, setPendingLeaves] = useState<any[]>([]);
  const [balances, setBalances] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [leavesRes, balancesRes, empRes] = await Promise.all([
        leavesService.fetchAllLeaves(),
        leavesService.fetchAllBalances(),
        api.get('/api/employees/')
      ]);

      const pending = leavesRes.filter((l: any) => l.status === 'pending');
      setPendingLeaves(pending);
      setBalances(balancesRes || []);
      setEmployees(empRes.data || []);
    } catch (e) {
      console.error("Error loading HR leaves data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateStatus = async (leaveId: number, status: 'approved' | 'rejected') => {
    try {
      await leavesService.updateLeaveStatus(leaveId, status);
      // Refresh to update pending list and balances
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Erreur lors de la mise à jour");
    }
  };

  // Group balances by employee
  const employeeBalances = useMemo(() => {
    const map = new Map<number, any>();

    // Initialize map with employees who have balances
    balances.forEach((bal) => {
      if (!map.has(bal.employee_id)) {
        const emp = employees.find(e => e.user_id === bal.employee_id);
        map.set(bal.employee_id, {
          employee_id: bal.employee_id,
          name: emp ? `${emp.user?.prenom} ${emp.user?.nom}` : `ID: ${bal.employee_id}`,
          role: emp?.position?.title || (emp?.manager_id ? 'Employé' : 'Manager'),
          balances: {}
        });
      }
      
      const empData = map.get(bal.employee_id);
      // Map leave type names to our standard columns
      let typeKey = 'Congé Personnel'; // default
      if (bal.leave_type_name === 'Congé Payé' || bal.leave_type_id === 1) typeKey = 'Congé Payé';
      if (bal.leave_type_name === 'Arrêt Maladie' || bal.leave_type_id === 2) typeKey = 'Arrêt Maladie';
      if (bal.leave_type_name === 'Congé Sans Solde' || bal.leave_type_id === 5) typeKey = 'Congé Sans Solde';
      if (bal.leave_type_name === 'Maternité / Paternité' || bal.leave_type_id === 3) typeKey = 'Maternité / Paternité';

      empData.balances[typeKey] = bal.remaining_days;
    });

    const result = Array.from(map.values());
    
    // Filter by search
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      return result.filter(emp => emp.name.toLowerCase().includes(q));
    }
    
    // Sort alphabetically
    return result.sort((a, b) => a.name.localeCompare(b.name));
  }, [balances, employees, searchQuery]);

  const getEmployeeName = (id: number) => {
    const emp = employees.find(e => e.user_id === id);
    if (emp && emp.user) return `${emp.user.prenom} ${emp.user.nom}`;
    return `ID: ${id}`;
  };

  if (loading && employees.length === 0) {
    return (
      <View style={[styles.stack, { flex: 1, justifyContent: "center" }]}>
        <ActivityIndicator color={theme.sky} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.stack} showsVerticalScrollIndicator={false}>
      
      {/* SECTION 1: Validation */}
      <Card ui={ui} style={{ marginBottom: 24 }}>
        <View style={[styles.rowStart, { marginBottom: 16 }]}>
          <Feather name="calendar" size={20} color={theme.navy} style={{ marginRight: 8 }} />
          <Text style={styles.cardTitle}>Validation de Congés Globaux (RH/Admin)</Text>
        </View>

        {pendingLeaves.length === 0 ? (
          <Text style={[styles.bodyText, { textAlign: 'center', marginVertical: 24, color: theme.muted }]}>Aucune demande de congé en attente de validation système.</Text>
        ) : (
          pendingLeaves.map(leave => (
            <View key={leave.id} style={[styles.card, { marginBottom: 12, backgroundColor: theme.surfaceAlt }]}>
              <View style={{ flexDirection: 'column', gap: 12 }}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.bodyStrong}>{getEmployeeName(leave.employee_id)}</Text>
                  <Text style={styles.metaText}>{leave.leave_type_name || leave.leave_type}</Text>
                  <Text style={[styles.bodyText, { marginTop: 4 }]}>
                    Du <Text style={styles.bodyStrong}>{leave.start_date}</Text> au <Text style={styles.bodyStrong}>{leave.end_date}</Text>
                  </Text>
                  {leave.reason ? (
                    <Text style={[styles.metaText, { marginTop: 4, fontStyle: 'italic' }]}>"{leave.reason}"</Text>
                  ) : null}
                </View>
                <View style={{ flexDirection: 'row', gap: 10, justifyContent: 'flex-end' }}>
                  <Pressable 
                    onPress={() => handleUpdateStatus(leave.id, 'rejected')}
                    style={{ backgroundColor: theme.roseSoft, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, flex: 1, alignItems: 'center' }}
                  >
                    <Text style={{ color: theme.rose, fontWeight: '700', fontSize: 13 }}>Refuser</Text>
                  </Pressable>
                  <Pressable 
                    onPress={() => handleUpdateStatus(leave.id, 'approved')}
                    style={{ backgroundColor: theme.emeraldSoft, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, flex: 1, alignItems: 'center' }}
                  >
                    <Text style={{ color: theme.emerald, fontWeight: '700', fontSize: 13 }}>Approuver</Text>
                  </Pressable>
                </View>
              </View>
            </View>
          ))
        )}
      </Card>

      {/* SECTION 2: Balances */}
      <Card ui={ui} style={{ marginBottom: 40, paddingHorizontal: 0, paddingBottom: 0, overflow: 'hidden' }}>
        <View style={[styles.rowBetween, { paddingHorizontal: 16, marginBottom: 16 }]}>
          <View style={styles.rowStart}>
            <Feather name="calendar" size={20} color={theme.navy} style={{ marginRight: 8 }} />
            <Text style={styles.cardTitle}>Soldes de Congés Globaux</Text>
          </View>
          <TextInput
            style={{
              backgroundColor: theme.background,
              borderColor: theme.line,
              borderWidth: 1,
              borderRadius: 6,
              paddingHorizontal: 12,
              paddingVertical: 6,
              width: 250,
              color: theme.text,
              fontSize: 13
            }}
            placeholder="Rechercher un collaborateur..."
            placeholderTextColor={theme.muted}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>

        {Platform.OS === 'web' ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={{ minWidth: 800 }}>
              {/* Header Row */}
              <View style={{ flexDirection: 'row', backgroundColor: theme.background, paddingVertical: 12, paddingHorizontal: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                <Text style={[styles.bodyStrong, { flex: 2, fontSize: 13 }]}>Collaborateur</Text>
                <Text style={[styles.bodyStrong, { flex: 1, fontSize: 13, textAlign: 'center' }]}>Congé Payé</Text>
                <Text style={[styles.bodyStrong, { flex: 1, fontSize: 13, textAlign: 'center' }]}>Arrêt Maladie</Text>
                <Text style={[styles.bodyStrong, { flex: 1, fontSize: 13, textAlign: 'center' }]}>Congé Sans Solde</Text>
                <Text style={[styles.bodyStrong, { flex: 1, fontSize: 13, textAlign: 'center' }]}>Maternité / Paternité</Text>
                <Text style={[styles.bodyStrong, { flex: 1, fontSize: 13, textAlign: 'center' }]}>Congé Personnel</Text>
              </View>
              
              {/* Data Rows */}
              {employeeBalances.length === 0 ? (
                <View style={{ padding: 24, alignItems: 'center' }}>
                  <Text style={styles.mutedText}>Aucun solde trouvé.</Text>
                </View>
              ) : (
                employeeBalances.map((emp, idx) => (
                  <View key={emp.employee_id} style={{ flexDirection: 'row', paddingVertical: 16, paddingHorizontal: 16, borderBottomWidth: idx < employeeBalances.length - 1 ? 1 : 0, borderBottomColor: theme.line }}>
                    <View style={{ flex: 2, justifyContent: 'center' }}>
                      <Text style={styles.bodyStrong}>
                        {emp.name} <Text style={[styles.metaText, { fontWeight: 'normal' }]}>({emp.role})</Text>
                      </Text>
                    </View>
                    <Text style={[styles.bodyStrong, { flex: 1, textAlign: 'center', color: theme.navy }]}>{emp.balances['Congé Payé'] ?? '-'} j</Text>
                    <Text style={[styles.bodyStrong, { flex: 1, textAlign: 'center', color: theme.navy }]}>{emp.balances['Arrêt Maladie'] ?? '-'} j</Text>
                    <Text style={[styles.bodyStrong, { flex: 1, textAlign: 'center', color: theme.navy }]}>{emp.balances['Congé Sans Solde'] ?? '-'} j</Text>
                    <Text style={[styles.bodyStrong, { flex: 1, textAlign: 'center', color: theme.navy }]}>{emp.balances['Maternité / Paternité'] ?? '-'} j</Text>
                    <Text style={[styles.bodyStrong, { flex: 1, textAlign: 'center', color: theme.navy }]}>{emp.balances['Congé Personnel'] ?? '-'} j</Text>
                  </View>
                ))
              )}
            </View>
          </ScrollView>
        ) : (
          <View style={{ paddingHorizontal: 16, paddingBottom: 16 }}>
            {employeeBalances.length === 0 ? (
              <Text style={[styles.mutedText, { textAlign: 'center', marginVertical: 16 }]}>Aucun solde trouvé.</Text>
            ) : (
              employeeBalances.map((emp) => (
                <View key={emp.employee_id} style={{ backgroundColor: theme.surfaceAlt, borderRadius: 8, padding: 12, marginBottom: 12 }}>
                  <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>
                    {emp.name} <Text style={[styles.metaText, { fontWeight: 'normal' }]}>({emp.role})</Text>
                  </Text>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                    <View style={{ backgroundColor: theme.card, padding: 8, borderRadius: 6, flex: 1, minWidth: '45%' }}>
                      <Text style={styles.metaText}>Congé Payé</Text>
                      <Text style={[styles.bodyStrong, { color: theme.navy }]}>{emp.balances['Congé Payé'] ?? '-'} j</Text>
                    </View>
                    <View style={{ backgroundColor: theme.card, padding: 8, borderRadius: 6, flex: 1, minWidth: '45%' }}>
                      <Text style={styles.metaText}>Arrêt Maladie</Text>
                      <Text style={[styles.bodyStrong, { color: theme.navy }]}>{emp.balances['Arrêt Maladie'] ?? '-'} j</Text>
                    </View>
                    <View style={{ backgroundColor: theme.card, padding: 8, borderRadius: 6, flex: 1, minWidth: '45%' }}>
                      <Text style={styles.metaText}>Congé Sans Solde</Text>
                      <Text style={[styles.bodyStrong, { color: theme.navy }]}>{emp.balances['Congé Sans Solde'] ?? '-'} j</Text>
                    </View>
                    <View style={{ backgroundColor: theme.card, padding: 8, borderRadius: 6, flex: 1, minWidth: '45%' }}>
                      <Text style={styles.metaText}>Maternité / Paternité</Text>
                      <Text style={[styles.bodyStrong, { color: theme.navy }]}>{emp.balances['Maternité / Paternité'] ?? '-'} j</Text>
                    </View>
                    <View style={{ backgroundColor: theme.card, padding: 8, borderRadius: 6, flex: 1, minWidth: '45%' }}>
                      <Text style={styles.metaText}>Congé Personnel</Text>
                      <Text style={[styles.bodyStrong, { color: theme.navy }]}>{emp.balances['Congé Personnel'] ?? '-'} j</Text>
                    </View>
                  </View>
                </View>
              ))
            )}
          </View>
        )}
      </Card>
      
    </ScrollView>
  );
}
