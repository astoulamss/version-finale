import React, { useState, useEffect } from "react";

import { View, Text, TextInput, ScrollView, Pressable, ActivityIndicator, Modal, Alert } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Ui } from "../types";
import { fetchAllEmployees, fetchDepartments, fetchPositions, fetchManagers, fetchUsers, createDepartment, createEmployee, createPosition, updateDepartment, deleteDepartment, updatePosition, deletePosition } from "../services/rh.service";

import { PrimaryButton, SecondaryButton } from "../components/ui/Button";

export function HrTeamScreen({ ui, triggerFeedback }: { ui: Ui; triggerFeedback?: (m?: string) => void }) {
  const { styles, theme } = ui;

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [employees, setEmployees] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [managers, setManagers] = useState<any[]>([]);
  const [allUsers, setAllUsers] = useState<any[]>([]);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("Actifs");
  const [activeTab, setActiveTab] = useState<"employes" | "departements" | "postes">("employes");

  // Modals
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showCreatePosModal, setShowCreatePosModal] = useState(false);
  const [showAssignManagerModal, setShowAssignManagerModal] = useState(false);

  // Dropdowns state for Profile Modal
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showDeptDropdown, setShowDeptDropdown] = useState(false);
  const [showPosDropdown, setShowPosDropdown] = useState(false);
  const [showManagerFormDropdown, setShowManagerFormDropdown] = useState(false);
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  const [showGenderDropdown, setShowGenderDropdown] = useState(false);

  // Forms
  const [deptForm, setDeptForm] = useState({ id: null as number|null, name: "", description: "" });
  const [posForm, setPosForm] = useState({ id: null as number|null, title: "", description: "" });
  const [profileForm, setProfileForm] = useState({ 
    user_id: null as number|null, 
    department_id: null as number|null, 
    position_id: null as number|null, 
    manager_id: null as number|null,
    salary: "", 
    status: "active",
    date_naissance: "",
    sexe: "",
    nationalite: "",
    numero_telephone: "",
    adresse: "",
    hire_date: "",
    departure_date: ""
  });
  const [selectedDeptForManager, setSelectedDeptForManager] = useState<number | null>(null);

  const loadData = () => {
    setRefreshing(true);
    Promise.all([
      fetchAllEmployees().catch(() => []),
      fetchDepartments().catch(() => []),
      fetchPositions().catch(() => []),
      fetchManagers().catch(() => []),
      fetchUsers().catch(() => [])
    ]).then(([emps, depts, pos, mgrs, users]) => {
      setEmployees(emps);
      setDepartments(depts);
      setPositions(pos);
      setManagers(mgrs);
      setAllUsers(users);
      setLoading(false);
      setRefreshing(false);
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveDept = async () => {
    if (!deptForm.name.trim()) return;
    try {
      if (deptForm.id) {
        await updateDepartment(deptForm.id, { name: deptForm.name, description: deptForm.description });
        triggerFeedback?.("Département mis à jour");
      } else {
        await createDepartment({ name: deptForm.name, description: deptForm.description });
        triggerFeedback?.("Département créé");
      }
      setShowDeptModal(false);
      setDeptForm({ id: null, name: "", description: "" });
      loadData();
    } catch (e: any) {
      Alert.alert("Erreur", e.response?.data?.detail || "Action impossible.");
    }
  };

  const handleDeleteDept = (id: number) => {
    Alert.alert("Supprimer le département", "Êtes-vous sûr ? Les employés de ce département seront sans département.", [
      { text: "Annuler", style: "cancel" },
      { text: "Supprimer", style: "destructive", onPress: async () => {
          try {
            await deleteDepartment(id);
            triggerFeedback?.("Département supprimé");
            loadData();
          } catch (e: any) {
            Alert.alert("Erreur", "Impossible de supprimer le département.");
          }
      }}
    ]);
  };

  const handleAssignManager = async (managerId: number) => {
    if (!selectedDeptForManager) return;
    try {
      await updateDepartment(selectedDeptForManager, { manager_id: managerId });
      triggerFeedback?.("Manager assigné");
      setShowAssignManagerModal(false);
      loadData();
    } catch (e: any) {
      Alert.alert("Erreur", "Impossible d'assigner le manager.");
    }
  };

  const handleSavePosition = async () => {
    if (!posForm.title.trim()) return;
    try {
      if (posForm.id) {
        await updatePosition(posForm.id, { title: posForm.title, description: posForm.description });
        triggerFeedback?.("Poste mis à jour");
      } else {
        await createPosition({ title: posForm.title, description: posForm.description });
        triggerFeedback?.("Poste créé");
      }
      setShowCreatePosModal(false);
      setPosForm({ id: null, title: "", description: "" });
      loadData();
    } catch (e: any) {
      Alert.alert("Erreur", e.response?.data?.detail || "Action impossible.");
    }
  };

  const handleDeletePosition = (id: number) => {
    Alert.alert("Supprimer le poste", "Êtes-vous sûr ? Les employés affectés n'auront plus de poste.", [
      { text: "Annuler", style: "cancel" },
      { text: "Supprimer", style: "destructive", onPress: async () => {
          try {
            await deletePosition(id);
            triggerFeedback?.("Poste supprimé");
            loadData();
          } catch (e: any) {
            Alert.alert("Erreur", "Impossible de supprimer le poste.");
          }
      }}
    ]);
  };

  const handleCreateProfile = async () => {
    if (!profileForm.user_id) return Alert.alert("Erreur", "Veuillez sélectionner un utilisateur");
    
    // Parse Dates (from dd/mm/yyyy to yyyy-mm-dd)
    const parseDate = (d: string) => {
      if (!d) return null;
      const parts = d.split('/');
      if (parts.length === 3) return `${parts[2]}-${parts[1]}-${parts[0]}`;
      return null;
    };

    try {
      const payload: any = {
        user_id: profileForm.user_id,
        status: profileForm.status,
      };
      
      if (profileForm.department_id) payload.department_id = profileForm.department_id;
      if (profileForm.position_id) payload.position_id = profileForm.position_id;
      if (profileForm.manager_id) payload.manager_id = profileForm.manager_id;
      if (profileForm.salary) payload.salary = parseFloat(profileForm.salary);
      if (profileForm.date_naissance) payload.date_naissance = parseDate(profileForm.date_naissance);
      if (profileForm.hire_date) payload.hire_date = parseDate(profileForm.hire_date);
      if (profileForm.departure_date) payload.departure_date = parseDate(profileForm.departure_date);
      if (profileForm.nationalite) payload.nationalite = profileForm.nationalite;
      if (profileForm.adresse) payload.adresse = profileForm.adresse;
      if (profileForm.numero_telephone) payload.numero_telephone = profileForm.numero_telephone;
      if (profileForm.sexe) payload.sexe = profileForm.sexe;

      await createEmployee(payload);
      triggerFeedback?.("Profil créé avec succès");
      setShowProfileModal(false);
      setProfileForm({ 
        user_id: null, department_id: null, position_id: null, manager_id: null,
        salary: "", status: "active", date_naissance: "", sexe: "",
        nationalite: "", numero_telephone: "", adresse: "", hire_date: "", departure_date: "" 
      });
      loadData();
    } catch (e: any) {
      Alert.alert("Erreur", e.response?.data?.detail || "Impossible de créer le profil.");
    }
  };

  const usersWithoutProfile = allUsers.filter(u => !employees.some(e => e.user_id === u.id));
  const activeEmployees = employees.filter(e => e.status === "active" || e.status === "Actif" || e.status === "En poste");
  
  const filteredEmployees = employees.filter(emp => {
    const isMatchFilter = filter === "Tous" || 
      (filter === "Actifs" && (emp.status === "active" || emp.status === "Actif" || emp.status === "En poste")) ||
      (filter === "Inactifs" && emp.status !== "active" && emp.status !== "Actif" && emp.status !== "En poste");
    
    const textToSearch = `${emp.user?.prenom} ${emp.user?.nom} ${emp.department?.name} ${emp.position?.title}`.toLowerCase();
    return isMatchFilter && textToSearch.includes(search.toLowerCase());
  });

  const renderKpiCard = (title: string, value: number, icon: any, color: string) => (
    <View style={{
      backgroundColor: theme.card,
      borderRadius: 16,
      padding: 16,
      width: 140,
      marginRight: 12,
      borderWidth: 1,
      borderColor: theme.line,
      justifyContent: 'space-between',
      height: 100
    }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Feather name={icon} size={20} color={color} />
      </View>
      <View>
        <Text style={{ fontSize: 28, fontWeight: '800', color: color }}>{value}</Text>
        <Text style={{ fontSize: 13, color: theme.muted, fontWeight: '500' }}>{title}</Text>
      </View>
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.background }}>
      {/* Header */}
      <View style={{ padding: 16, paddingBottom: 8 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
          <View style={{ backgroundColor: theme.sky + '20', padding: 8, borderRadius: 8, marginRight: 12 }}>
            <Feather name="users" size={20} color={theme.sky} />
          </View>
          <View>
            <Text style={{ fontSize: 22, fontWeight: '800', color: theme.text }}>Personnel</Text>
            <Text style={{ fontSize: 14, color: theme.muted }}>Gestion des employés et départements</Text>
          </View>
        </View>
      </View>

      {/* Tabs */}
      <View style={{ marginBottom: 16 }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16 }}>
          <Pressable onPress={() => setActiveTab("employes")} style={{ paddingBottom: 8, borderBottomWidth: 2, borderBottomColor: activeTab === "employes" ? theme.sky : 'transparent', marginRight: 24 }}>
            <Text style={{ fontWeight: 'bold', fontSize: 16, color: activeTab === "employes" ? theme.sky : theme.muted }}>Employés</Text>
          </Pressable>
          <Pressable onPress={() => setActiveTab("departements")} style={{ paddingBottom: 8, borderBottomWidth: 2, borderBottomColor: activeTab === "departements" ? theme.sky : 'transparent', marginRight: 24 }}>
            <Text style={{ fontWeight: 'bold', fontSize: 16, color: activeTab === "departements" ? theme.sky : theme.muted }}>Départements & Managers</Text>
          </Pressable>
          <Pressable onPress={() => setActiveTab("postes")} style={{ paddingBottom: 8, borderBottomWidth: 2, borderBottomColor: activeTab === "postes" ? theme.sky : 'transparent', marginRight: 16 }}>
            <Text style={{ fontWeight: 'bold', fontSize: 16, color: activeTab === "postes" ? theme.sky : theme.muted }}>Postes</Text>
          </Pressable>
        </ScrollView>
      </View>

      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={theme.sky} />
          <Text style={{ marginTop: 12, color: theme.muted }}>Chargement...</Text>
        </View>
      ) : (
        <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>
          
          {/* Toolbar */}
          <View style={{ paddingHorizontal: 16, marginBottom: 16 }}>
            {activeTab === "employes" && (
              <View style={{ flexDirection: 'row', marginBottom: 12 }}>
                <TextInput
                  style={[styles.fieldInput, { flex: 1, marginRight: 8, height: 44 }]}
                  placeholder="Rechercher..."
                  placeholderTextColor={theme.muted}
                  value={search}
                  onChangeText={setSearch}
                />
                <Pressable
                  style={{
                    backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12,
                    paddingHorizontal: 16, height: 44, justifyContent: 'center', alignItems: 'center', flexDirection: 'row'
                  }}
                  onPress={() => setFilter(filter === "Tous" ? "Actifs" : filter === "Actifs" ? "Inactifs" : "Tous")}
                >
                  <Text style={{ color: theme.text, fontWeight: '600', fontSize: 14 }}>{filter}</Text>
                  <Feather name="chevron-down" size={16} color={theme.muted} style={{ marginLeft: 6 }} />
                </Pressable>
              </View>
            )}

            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 4 }}>
              <Pressable 
                onPress={() => setShowProfileModal(true)}
                style={{ backgroundColor: '#6366F1', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, marginRight: 8, flexDirection: 'row', alignItems: 'center' }}>
                <Feather name="plus-circle" size={16} color="white" style={{ marginRight: 6 }} />
                <Text style={{ color: 'white', fontWeight: '700' }}>Nouveau Profil</Text>
              </Pressable>
              <Pressable 
                onPress={() => { setDeptForm({ id: null, name: "", description: "" }); setShowDeptModal(true); }}
                style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, marginRight: 8, flexDirection: 'row', alignItems: 'center' }}>
                <Feather name="plus-circle" size={16} color={theme.text} style={{ marginRight: 6 }} />
                <Text style={{ color: theme.text, fontWeight: '600' }}>Nouveau Département</Text>
              </Pressable>
              <Pressable 
                onPress={() => { setPosForm({ id: null, title: "", description: "" }); setShowCreatePosModal(true); }}
                style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, marginRight: 8, flexDirection: 'row', alignItems: 'center' }}>
                <Feather name="plus-circle" size={16} color={theme.text} style={{ marginRight: 6 }} />
                <Text style={{ color: theme.text, fontWeight: '600' }}>Nouveau Poste</Text>
              </Pressable>
              <Pressable 
                onPress={loadData}
                style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 10, flexDirection: 'row', alignItems: 'center' }}>
                <Feather name="refresh-cw" size={16} color={theme.text} />
              </Pressable>
            </ScrollView>
          </View>

          {/* KPI Cards */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 16 }}>
            {renderKpiCard("Actifs", activeEmployees.length, "user-check", "#10B981")}
            {renderKpiCard("Départements", departments.length, "grid", "#3B82F6")}
            {renderKpiCard("Postes", positions.length, "briefcase", "#8B5CF6")}
            {renderKpiCard("Managers", managers.length, "users", "#F59E0B")}
          </ScrollView>

          {/* Tab Content */}
          <View style={{ paddingHorizontal: 16 }}>
            {activeTab === "employes" && (
              // Liste Employés
              filteredEmployees.map((emp, index) => {
                const name = emp.user ? `${emp.user.prenom} ${emp.user.nom}` : 'Utilisateur Inconnu';
                const initials = emp.user ? `${emp.user.prenom?.[0]||''}${emp.user.nom?.[0]||''}`.toUpperCase() : 'U';
                const isActive = emp.status === "active" || emp.status === "Actif" || emp.status === "En poste";

                return (
                  <View key={emp.id || index} style={{
                    backgroundColor: theme.card, borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: theme.line, flexDirection: 'row', alignItems: 'center'
                  }}>
                    <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: theme.sky + '20', justifyContent: 'center', alignItems: 'center', marginRight: 16 }}>
                      <Text style={{ color: theme.sky, fontWeight: '800', fontSize: 16 }}>{initials}</Text>
                    </View>

                    <View style={{ flex: 1 }}>
                      <Text style={{ color: theme.text, fontWeight: '700', fontSize: 16, marginBottom: 2 }}>{name}</Text>
                      <Text style={{ color: theme.muted, fontSize: 13 }}>
                        {emp.position?.title || 'Sans poste'} • {emp.department?.name || 'Sans département'}
                      </Text>
                    </View>

                    <View style={{ backgroundColor: isActive ? '#10B98120' : theme.muted + '20', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                      <Text style={{ color: isActive ? '#10B981' : theme.muted, fontSize: 12, fontWeight: '700' }}>{isActive ? 'Actif' : 'Inactif'}</Text>
                    </View>
                  </View>
                );
              })
            )}
            
            {activeTab === "departements" && (
              // Grille Départements
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
                {departments.map((dept) => {
                  const hasManager = !!dept.manager;
                  const managerName = hasManager ? `${dept.manager.prenom} ${dept.manager.nom}` : "Aucun manager affecté";
                  
                  return (
                    <View key={dept.id} style={{
                      backgroundColor: theme.card,
                      borderRadius: 16,
                      padding: 16,
                      marginBottom: 16,
                      borderWidth: 1,
                      borderColor: theme.line,
                      width: '100%' // On mobile usually 100%, or 48% if tablet
                    }}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                        <Text style={{ color: theme.text, fontWeight: '800', fontSize: 18, flex: 1 }}>{dept.name}</Text>
                        
                        {/* Action Buttons */}
                        <View style={{ flexDirection: 'row', gap: 8 }}>
                          <Pressable 
                            onPress={() => { setSelectedDeptForManager(dept.id); setShowAssignManagerModal(true); }}
                            style={{ padding: 8, backgroundColor: theme.background, borderRadius: 8, borderWidth: 1, borderColor: theme.line }}>
                            <Feather name="user-plus" size={16} color={theme.text} />
                          </Pressable>
                          <Pressable 
                            onPress={() => { setDeptForm({ id: dept.id, name: dept.name, description: dept.description || "" }); setShowDeptModal(true); }}
                            style={{ padding: 8, backgroundColor: theme.background, borderRadius: 8, borderWidth: 1, borderColor: theme.line }}>
                            <Feather name="edit-2" size={16} color={theme.text} />
                          </Pressable>
                          <Pressable 
                            onPress={() => handleDeleteDept(dept.id)}
                            style={{ padding: 8, backgroundColor: '#EF444420', borderRadius: 8, borderWidth: 1, borderColor: '#EF444450' }}>
                            <Feather name="trash-2" size={16} color="#EF4444" />
                          </Pressable>
                        </View>
                      </View>

                      <Text style={{ color: theme.muted, fontSize: 14, marginBottom: 16, minHeight: 40 }}>
                        {dept.description || "Aucune description"}
                      </Text>

                      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <Feather name="user" size={14} color={hasManager ? '#6366F1' : theme.muted} style={{ marginRight: 6 }} />
                        <Text style={{ color: hasManager ? '#6366F1' : theme.muted, fontSize: 14, fontWeight: hasManager ? '600' : '400' }}>
                          {managerName}
                        </Text>
                      </View>
                    </View>
                  );
                })}
              </View>
            )}

            {activeTab === "postes" && (
              // Grille Postes
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
                {positions.map((pos) => {
                  const employesDansCePoste = employees.filter(e => e.position_id === pos.id).length;
                  const hasEmployes = employesDansCePoste > 0;
                  
                  return (
                    <View key={pos.id} style={{
                      backgroundColor: theme.card,
                      borderRadius: 16,
                      padding: 16,
                      marginBottom: 16,
                      borderWidth: 1,
                      borderColor: theme.line,
                      width: '100%' // On mobile usually 100%, or 48% if tablet
                    }}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                        <Text style={{ color: theme.text, fontWeight: '800', fontSize: 18, flex: 1 }}>{pos.title}</Text>
                        
                        {/* Action Buttons */}
                        <View style={{ flexDirection: 'row', gap: 8 }}>
                          <Pressable 
                            onPress={() => { setPosForm({ id: pos.id, title: pos.title, description: pos.description || "" }); setShowCreatePosModal(true); }}
                            style={{ padding: 8, backgroundColor: theme.background, borderRadius: 8, borderWidth: 1, borderColor: theme.line }}>
                            <Feather name="edit-2" size={16} color={theme.text} />
                          </Pressable>
                          <Pressable 
                            onPress={() => handleDeletePosition(pos.id)}
                            style={{ padding: 8, backgroundColor: '#EF444420', borderRadius: 8, borderWidth: 1, borderColor: '#EF444450' }}>
                            <Feather name="trash-2" size={16} color="#EF4444" />
                          </Pressable>
                        </View>
                      </View>

                      <Text style={{ color: theme.muted, fontSize: 14, marginBottom: 16, minHeight: 40 }}>
                        {pos.description || "Aucune description"}
                      </Text>

                      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <Feather name="users" size={14} color={hasEmployes ? '#10B981' : theme.muted} style={{ marginRight: 6 }} />
                        <Text style={{ color: hasEmployes ? '#10B981' : theme.muted, fontSize: 14, fontWeight: hasEmployes ? '600' : '400' }}>
                          {hasEmployes ? `${employesDansCePoste} collaborateur${employesDansCePoste > 1 ? 's' : ''}` : "Aucun collaborateur"}
                        </Text>
                      </View>
                    </View>
                  );
                })}
              </View>
            )}
          </View>
        </ScrollView>
      )}

      {/* Modal: Ajouter / Editer Département */}
      <Modal visible={showDeptModal} animationType="slide" transparent>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.background, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <Text style={{ fontSize: 20, fontWeight: 'bold', color: theme.text }}>
                {deptForm.id ? "Éditer le Département" : "Nouveau Département"}
              </Text>
              <Pressable onPress={() => setShowDeptModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>

            <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, marginTop: 12 }}>Nom du département</Text>
            <TextInput
              style={[styles.fieldInput, { marginBottom: 16 }]}
              placeholder="Ex: Marketing, R&D..."
              placeholderTextColor={theme.muted}
              value={deptForm.name}
              onChangeText={t => setDeptForm({...deptForm, name: t})}
            />

            <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, marginTop: 12 }}>Description (Optionnel)</Text>
            <TextInput
              style={[styles.fieldInput, { marginBottom: 24 }]}
              placeholder="Description..."
              placeholderTextColor={theme.muted}
              value={deptForm.description}
              onChangeText={t => setDeptForm({...deptForm, description: t})}
            />

            <PrimaryButton icon="save" label={deptForm.id ? "Enregistrer" : "Créer le département"} onPress={handleSaveDept} ui={ui} />
            <View style={{ height: 12 }} />
            <SecondaryButton icon="x" label="Annuler" onPress={() => setShowDeptModal(false)} ui={ui} />
          </View>
        </View>
      </Modal>

      {/* Modal: Assigner Manager */}
      <Modal visible={showAssignManagerModal} animationType="fade" transparent>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <View style={{ backgroundColor: theme.background, borderRadius: 24, padding: 24, width: '100%', maxHeight: '80%' }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <Text style={{ fontSize: 20, fontWeight: 'bold', color: theme.text }}>Assigner un Manager</Text>
              <Pressable onPress={() => setShowAssignManagerModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>

            <ScrollView style={{ marginBottom: 20 }}>
              {managers.length === 0 ? (
                <Text style={{ color: theme.muted }}>Aucun manager trouvé.</Text>
              ) : (
                managers.map(m => (
                  <Pressable 
                    key={m.id} 
                    onPress={() => handleAssignManager(m.id)}
                    style={{ padding: 16, backgroundColor: theme.card, borderRadius: 12, marginBottom: 8, borderWidth: 1, borderColor: theme.line, flexDirection: 'row', alignItems: 'center' }}>
                    <Feather name="user" size={18} color={theme.sky} style={{ marginRight: 12 }} />
                    <Text style={{ color: theme.text, fontSize: 16, fontWeight: '600' }}>{m.prenom} {m.nom}</Text>
                  </Pressable>
                ))
              )}
            </ScrollView>
            
            <SecondaryButton icon="x" label="Annuler" onPress={() => setShowAssignManagerModal(false)} ui={ui} />
          </View>
        </View>
      </Modal>

      {/* Modal: Nouveau / Editer Poste */}
      <Modal visible={showCreatePosModal} animationType="slide" transparent>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.background, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <Text style={{ fontSize: 20, fontWeight: 'bold', color: theme.text }}>
                {posForm.id ? "Éditer le Poste" : "Nouveau Poste"}
              </Text>
              <Pressable onPress={() => setShowCreatePosModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>

            <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, marginTop: 12 }}>Titre du poste</Text>
            <TextInput
              style={[styles.fieldInput, { marginBottom: 16 }]}
              placeholder="Ex: Développeur, Manager..."
              placeholderTextColor={theme.muted}
              value={posForm.title}
              onChangeText={t => setPosForm({...posForm, title: t})}
            />

            <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, marginTop: 12 }}>Description (Optionnel)</Text>
            <TextInput
              style={[styles.fieldInput, { marginBottom: 24 }]}
              placeholder="Description..."
              placeholderTextColor={theme.muted}
              value={posForm.description}
              onChangeText={t => setPosForm({...posForm, description: t})}
            />

            <PrimaryButton icon="save" label={posForm.id ? "Enregistrer" : "Créer le poste"} onPress={handleSavePosition} ui={ui} />
            <View style={{ height: 12 }} />
            <SecondaryButton icon="x" label="Annuler" onPress={() => setShowCreatePosModal(false)} ui={ui} />
          </View>
        </View>
      </Modal>

      {/* Modal: Nouveau Profil */}
      <Modal visible={showProfileModal} animationType="slide" transparent>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.background, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, maxHeight: '80%' }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <Text style={{ fontSize: 20, fontWeight: 'bold', color: theme.text }}>Ajouter un Profil</Text>
              <Pressable onPress={() => setShowProfileModal(false)}>
                <Feather name="x" size={24} color={theme.text} />
              </Pressable>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 20 }}>
              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, marginTop: 12 }}>Utilisateur *</Text>
              <View style={{ marginBottom: 4, zIndex: 6000 }}>
                {usersWithoutProfile.length === 0 ? (
                  <Text style={{ color: '#EF4444' }}>Aucun utilisateur disponible. Créez-le d'abord depuis l'interface Administrateur.</Text>
                ) : (
                  <>
                    <Pressable
                      onPress={() => { setShowUserDropdown(!showUserDropdown); setShowDeptDropdown(false); setShowPosDropdown(false); setShowManagerFormDropdown(false); setShowStatusDropdown(false); setShowGenderDropdown(false); }}
                      style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, padding: 16 }}
                    >
                      <Text style={{ color: profileForm.user_id ? theme.text : theme.muted, fontSize: 16 }}>
                        {profileForm.user_id ? usersWithoutProfile.find(u => u.id === profileForm.user_id)?.prenom + " " + usersWithoutProfile.find(u => u.id === profileForm.user_id)?.nom : "-- Choisir un utilisateur --"}
                      </Text>
                      <Feather name={showUserDropdown ? "chevron-up" : "chevron-down"} size={20} color={theme.muted} />
                    </Pressable>
                    {showUserDropdown && (
                      <View style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, marginTop: 4, maxHeight: 150, position: 'absolute', top: 56, left: 0, right: 0 }}>
                        <ScrollView nestedScrollEnabled showsVerticalScrollIndicator={false}>
                          {usersWithoutProfile.map((u, i) => (
                            <Pressable
                              key={u.id}
                              onPress={() => { setProfileForm({...profileForm, user_id: u.id}); setShowUserDropdown(false); }}
                              style={{ padding: 16, borderBottomWidth: i < usersWithoutProfile.length - 1 ? 1 : 0, borderBottomColor: theme.line }}
                            >
                              <Text style={{ color: profileForm.user_id === u.id ? theme.sky : theme.text, fontWeight: profileForm.user_id === u.id ? 'bold' : 'normal' }}>
                                {u.prenom} {u.nom}
                              </Text>
                            </Pressable>
                          ))}
                        </ScrollView>
                      </View>
                    )}
                  </>
                )}
              </View>
              <Text style={{ color: theme.muted, fontSize: 12, marginBottom: 12 }}>Seuls les utilisateurs sans profil existant sont listés.</Text>

              <View style={{ flexDirection: 'row', gap: 16, zIndex: 5000, marginTop: 12 }}>
                <View style={{ flex: 1, zIndex: 5000 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Département</Text>
                  <View style={{ marginBottom: 16 }}>
                    <Pressable
                      onPress={() => { setShowDeptDropdown(!showDeptDropdown); setShowUserDropdown(false); setShowPosDropdown(false); setShowManagerFormDropdown(false); setShowStatusDropdown(false); setShowGenderDropdown(false); }}
                      style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, padding: 16 }}
                    >
                      <Text style={{ color: profileForm.department_id ? theme.text : theme.muted, fontSize: 16 }}>
                        {profileForm.department_id ? departments.find(d => d.id === profileForm.department_id)?.name : "-- Aucun --"}
                      </Text>
                      <Feather name={showDeptDropdown ? "chevron-up" : "chevron-down"} size={20} color={theme.muted} />
                    </Pressable>
                    {showDeptDropdown && (
                      <View style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, marginTop: 4, maxHeight: 150, position: 'absolute', top: 56, left: 0, right: 0 }}>
                        <ScrollView nestedScrollEnabled showsVerticalScrollIndicator={false}>
                          <Pressable
                            onPress={() => { setProfileForm({...profileForm, department_id: null}); setShowDeptDropdown(false); }}
                            style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}
                          >
                            <Text style={{ color: profileForm.department_id === null ? theme.sky : theme.text, fontWeight: profileForm.department_id === null ? 'bold' : 'normal' }}>-- Aucun --</Text>
                          </Pressable>
                          {departments.map((d, i) => (
                            <Pressable
                              key={d.id}
                              onPress={() => { setProfileForm({...profileForm, department_id: d.id}); setShowDeptDropdown(false); }}
                              style={{ padding: 16, borderBottomWidth: i < departments.length - 1 ? 1 : 0, borderBottomColor: theme.line }}
                            >
                              <Text style={{ color: profileForm.department_id === d.id ? theme.sky : theme.text, fontWeight: profileForm.department_id === d.id ? 'bold' : 'normal' }}>
                                {d.name}
                              </Text>
                            </Pressable>
                          ))}
                        </ScrollView>
                      </View>
                    )}
                  </View>
                </View>

                <View style={{ flex: 1, zIndex: 4500 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Poste</Text>
                  <View style={{ marginBottom: 16 }}>
                    <Pressable
                      onPress={() => { setShowPosDropdown(!showPosDropdown); setShowUserDropdown(false); setShowDeptDropdown(false); setShowManagerFormDropdown(false); setShowStatusDropdown(false); setShowGenderDropdown(false); }}
                      style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, padding: 16 }}
                    >
                      <Text style={{ color: profileForm.position_id ? theme.text : theme.muted, fontSize: 16 }}>
                        {profileForm.position_id ? positions.find(p => p.id === profileForm.position_id)?.title : "-- Aucun --"}
                      </Text>
                      <Feather name={showPosDropdown ? "chevron-up" : "chevron-down"} size={20} color={theme.muted} />
                    </Pressable>
                    {showPosDropdown && (
                      <View style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, marginTop: 4, maxHeight: 150, position: 'absolute', top: 56, left: 0, right: 0 }}>
                        <ScrollView nestedScrollEnabled showsVerticalScrollIndicator={false}>
                          <Pressable
                            onPress={() => { setProfileForm({...profileForm, position_id: null}); setShowPosDropdown(false); }}
                            style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}
                          >
                            <Text style={{ color: profileForm.position_id === null ? theme.sky : theme.text, fontWeight: profileForm.position_id === null ? 'bold' : 'normal' }}>-- Aucun --</Text>
                          </Pressable>
                          {positions.map((p, i) => (
                            <Pressable
                              key={p.id}
                              onPress={() => { setProfileForm({...profileForm, position_id: p.id}); setShowPosDropdown(false); }}
                              style={{ padding: 16, borderBottomWidth: i < positions.length - 1 ? 1 : 0, borderBottomColor: theme.line }}
                            >
                              <Text style={{ color: profileForm.position_id === p.id ? theme.sky : theme.text, fontWeight: profileForm.position_id === p.id ? 'bold' : 'normal' }}>
                                {p.title}
                              </Text>
                            </Pressable>
                          ))}
                        </ScrollView>
                      </View>
                    )}
                  </View>
                </View>
              </View>

              <View style={{ flexDirection: 'row', gap: 16, zIndex: 4000 }}>
                <View style={{ flex: 1, zIndex: 4000 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Manager</Text>
                  <View style={{ marginBottom: 16 }}>
                    <Pressable
                      onPress={() => { setShowManagerFormDropdown(!showManagerFormDropdown); setShowUserDropdown(false); setShowDeptDropdown(false); setShowPosDropdown(false); setShowStatusDropdown(false); setShowGenderDropdown(false); }}
                      style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, padding: 16 }}
                    >
                      <Text style={{ color: profileForm.manager_id ? theme.text : theme.muted, fontSize: 16 }}>
                        {profileForm.manager_id ? managers.find(m => m.id === profileForm.manager_id)?.nom : "-- Aucun --"}
                      </Text>
                      <Feather name={showManagerFormDropdown ? "chevron-up" : "chevron-down"} size={20} color={theme.muted} />
                    </Pressable>
                    {showManagerFormDropdown && (
                      <View style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, marginTop: 4, maxHeight: 150, position: 'absolute', top: 56, left: 0, right: 0 }}>
                        <ScrollView nestedScrollEnabled showsVerticalScrollIndicator={false}>
                          <Pressable
                            onPress={() => { setProfileForm({...profileForm, manager_id: null}); setShowManagerFormDropdown(false); }}
                            style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}
                          >
                            <Text style={{ color: profileForm.manager_id === null ? theme.sky : theme.text, fontWeight: profileForm.manager_id === null ? 'bold' : 'normal' }}>-- Aucun --</Text>
                          </Pressable>
                          {managers.map((m, i) => (
                            <Pressable
                              key={m.id}
                              onPress={() => { setProfileForm({...profileForm, manager_id: m.id}); setShowManagerFormDropdown(false); }}
                              style={{ padding: 16, borderBottomWidth: i < managers.length - 1 ? 1 : 0, borderBottomColor: theme.line }}
                            >
                              <Text style={{ color: profileForm.manager_id === m.id ? theme.sky : theme.text, fontWeight: profileForm.manager_id === m.id ? 'bold' : 'normal' }}>
                                {m.prenom} {m.nom}
                              </Text>
                            </Pressable>
                          ))}
                        </ScrollView>
                      </View>
                    )}
                  </View>
                </View>

                <View style={{ flex: 1, zIndex: 3500 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Statut</Text>
                  <View style={{ marginBottom: 16 }}>
                    <Pressable
                      onPress={() => { setShowStatusDropdown(!showStatusDropdown); setShowUserDropdown(false); setShowDeptDropdown(false); setShowPosDropdown(false); setShowManagerFormDropdown(false); setShowGenderDropdown(false); }}
                      style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, padding: 16 }}
                    >
                      <Text style={{ color: profileForm.status ? theme.text : theme.muted, fontSize: 16 }}>
                        {profileForm.status === "active" ? "Actif" : "Inactif"}
                      </Text>
                      <Feather name={showStatusDropdown ? "chevron-up" : "chevron-down"} size={20} color={theme.muted} />
                    </Pressable>
                    {showStatusDropdown && (
                      <View style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, marginTop: 4, maxHeight: 150, position: 'absolute', top: 56, left: 0, right: 0 }}>
                        <Pressable
                          onPress={() => { setProfileForm({...profileForm, status: "active"}); setShowStatusDropdown(false); }}
                          style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}
                        >
                          <Text style={{ color: profileForm.status === "active" ? theme.sky : theme.text, fontWeight: profileForm.status === "active" ? 'bold' : 'normal' }}>Actif</Text>
                        </Pressable>
                        <Pressable
                          onPress={() => { setProfileForm({...profileForm, status: "inactive"}); setShowStatusDropdown(false); }}
                          style={{ padding: 16 }}
                        >
                          <Text style={{ color: profileForm.status === "inactive" ? theme.sky : theme.text, fontWeight: profileForm.status === "inactive" ? 'bold' : 'normal' }}>Inactif</Text>
                        </Pressable>
                      </View>
                    )}
                  </View>
                </View>
              </View>

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8, marginTop: 4 }}>Salaire (€)</Text>
              <TextInput
                style={[styles.fieldInput, { marginBottom: 16 }]}
                placeholder="Ex: 35000"
                keyboardType="numeric"
                placeholderTextColor={theme.muted}
                value={profileForm.salary}
                onChangeText={t => setProfileForm({...profileForm, salary: t})}
              />

              <View style={{ flexDirection: 'row', gap: 16, zIndex: 3000 }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Date de naissance</Text>
                  <TextInput
                    style={[styles.fieldInput, { marginBottom: 16 }]}
                    placeholder="jj/mm/aaaa"
                    placeholderTextColor={theme.muted}
                    value={profileForm.date_naissance}
                    onChangeText={t => setProfileForm({...profileForm, date_naissance: t})}
                  />
                </View>

                <View style={{ flex: 1, zIndex: 3000 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Sexe</Text>
                  <View style={{ marginBottom: 16 }}>
                    <Pressable
                      onPress={() => { setShowGenderDropdown(!showGenderDropdown); setShowUserDropdown(false); setShowDeptDropdown(false); setShowPosDropdown(false); setShowManagerFormDropdown(false); setShowStatusDropdown(false); }}
                      style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, padding: 16 }}
                    >
                      <Text style={{ color: profileForm.sexe ? theme.text : theme.muted, fontSize: 16 }}>
                        {profileForm.sexe || "-- Choisir --"}
                      </Text>
                      <Feather name={showGenderDropdown ? "chevron-up" : "chevron-down"} size={20} color={theme.muted} />
                    </Pressable>
                    {showGenderDropdown && (
                      <View style={{ backgroundColor: theme.card, borderWidth: 1, borderColor: theme.line, borderRadius: 12, marginTop: 4, maxHeight: 150, position: 'absolute', top: 56, left: 0, right: 0 }}>
                        <Pressable onPress={() => { setProfileForm({...profileForm, sexe: "Homme"}); setShowGenderDropdown(false); }} style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                          <Text style={{ color: profileForm.sexe === "Homme" ? theme.sky : theme.text }}>Homme</Text>
                        </Pressable>
                        <Pressable onPress={() => { setProfileForm({...profileForm, sexe: "Femme"}); setShowGenderDropdown(false); }} style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                          <Text style={{ color: profileForm.sexe === "Femme" ? theme.sky : theme.text }}>Femme</Text>
                        </Pressable>
                        <Pressable onPress={() => { setProfileForm({...profileForm, sexe: "Autre"}); setShowGenderDropdown(false); }} style={{ padding: 16 }}>
                          <Text style={{ color: profileForm.sexe === "Autre" ? theme.sky : theme.text }}>Autre</Text>
                        </Pressable>
                      </View>
                    )}
                  </View>
                </View>
              </View>

              <View style={{ flexDirection: 'row', gap: 16 }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Nationalité</Text>
                  <TextInput
                    style={[styles.fieldInput, { marginBottom: 16 }]}
                    placeholder="Ex: Française"
                    placeholderTextColor={theme.muted}
                    value={profileForm.nationalite}
                    onChangeText={t => setProfileForm({...profileForm, nationalite: t})}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Numéro de téléphone</Text>
                  <TextInput
                    style={[styles.fieldInput, { marginBottom: 16 }]}
                    placeholder="Ex: +33 6 12 34 56 78"
                    placeholderTextColor={theme.muted}
                    value={profileForm.numero_telephone}
                    onChangeText={t => setProfileForm({...profileForm, numero_telephone: t})}
                  />
                </View>
              </View>

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Adresse</Text>
              <TextInput
                style={[styles.fieldInput, { marginBottom: 16 }]}
                placeholder="Ex: 12 Rue de la Paix, 75002 Paris"
                placeholderTextColor={theme.muted}
                value={profileForm.adresse}
                onChangeText={t => setProfileForm({...profileForm, adresse: t})}
              />

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Date d'embauche</Text>
              <TextInput
                style={[styles.fieldInput, { marginBottom: 16 }]}
                placeholder="jj/mm/aaaa"
                placeholderTextColor={theme.muted}
                value={profileForm.hire_date}
                onChangeText={t => setProfileForm({...profileForm, hire_date: t})}
              />

              <Text style={{ color: theme.text, fontWeight: '600', marginBottom: 8 }}>Date de départ</Text>
              <TextInput
                style={[styles.fieldInput, { marginBottom: 4 }]}
                placeholder="jj/mm/aaaa"
                placeholderTextColor={theme.muted}
                value={profileForm.departure_date}
                onChangeText={t => setProfileForm({...profileForm, departure_date: t})}
              />
              <Text style={{ color: theme.muted, fontSize: 12, marginBottom: 24 }}>Laisser vide si l'employé est toujours en poste.</Text>

              <View style={{ flexDirection: 'row', justifyContent: 'flex-end', gap: 12 }}>
                <SecondaryButton icon="x" label="Annuler" onPress={() => setShowProfileModal(false)} ui={ui} />
                <PrimaryButton icon="save" label="Créer" onPress={handleCreateProfile} ui={ui} disabled={!profileForm.user_id} />
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>

    </View>
  );
}
