import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, Pressable, ActivityIndicator, TextInput, Switch, Modal, KeyboardAvoidingView, Platform } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge, Chip } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { Ui, ViewId } from "../types";
import { isAdminRole } from "../lib/auth";
import { adminService } from "../services/admin.service";
import { useUi } from "../contexts/ThemeContext";
import { useFeedback } from "../contexts/FeedbackContext";

// Composant pour écran non autorisé
function UnauthorizedScreen({ ui: propUi }: { ui?: Ui }) {
  const contextUi = useUi().ui;
  const ui = propUi || contextUi;
  return (
    <View style={[ui.styles.stack, { flex: 1, justifyContent: 'center', alignItems: 'center' }]}>
      <Feather name="shield-off" size={48} color={ui.theme.rose} style={{ marginBottom: 16 }} />
      <Text style={ui.styles.heroTitle}>Accès Refusé</Text>
      <Text style={ui.styles.bodyText}>Vous n'avez pas les droits d'administration.</Text>
    </View>
  );
}

// ------------------------------------------------------------------
// 1. DASHBOARD
// ------------------------------------------------------------------
export function AdminDashboardScreen({ ui: propUi, onNavigate, sessionProfile, triggerFeedback: propFeedback }: any) {
  const contextUi = useUi().ui;
  const ui = propUi || contextUi;
  const contextFeedback = useFeedback().triggerFeedback;
  const triggerFeedback = propFeedback || contextFeedback;
  const { styles, theme } = ui;
  const isAuth = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await adminService.fetchAdminDashboard();
        if (mounted) setData(res);
      } catch (err) {
        console.warn("Failed to load dashboard data");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  return (
    <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" style={styles.stack} showsVerticalScrollIndicator={false}>
      
      {/* HEADER HERO */}
      <View style={{ marginBottom: 24, marginTop: 8 }}>

        <Text style={[styles.heroTitle, { marginBottom: 4 }]}>
          Bonjour, {data?.user_name || "Admin"} !
        </Text>
        <Text style={styles.bodyText}>
          {data?.message || "Bienvenue sur le dashboard administrateur. Vous avez accès à la gestion complète du système."}
        </Text>
      </View>

      {loading ? <ActivityIndicator color={theme.sky} style={{ marginVertical: 20 }} /> : (
        <>
          {/* TABLEAU DE BORD (KPIs) */}
          <View style={{ marginBottom: 24 }}>
            <Text style={[styles.heroTitle, { fontSize: 20, marginBottom: 4 }]}>Tableau de bord</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 12 }}>
               <Card ui={ui} style={{ width: '48%', padding: 16, backgroundColor: '#fff', flexGrow: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 6 }}>
                    <Feather name="users" size={14} color={theme.text} />
                    <Text style={[styles.metaText, { fontSize: 11, fontWeight: '600' }]}>UTILISATEURS ACTIFS</Text>
                  </View>
                  <View style={{ flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' }}>
                    <Text style={[styles.heroTitle, { fontSize: 28, marginVertical: 0 }]}>{data?.kpis?.active_users || 0}</Text>
                    <Text style={{ color: theme.emerald, fontSize: 12, fontWeight: '500' }}>+12 ce mois</Text>
                  </View>
               </Card>
               
               <Card ui={ui} style={{ width: '48%', padding: 16, backgroundColor: '#fff', flexGrow: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 6 }}>
                    <Feather name="alert-triangle" size={14} color={theme.rose} />
                    <Text style={[styles.metaText, { fontSize: 11, fontWeight: '600' }]}>ALERTES CRITIQUES</Text>
                  </View>
                  <Text style={[styles.heroTitle, { fontSize: 28, color: theme.rose, marginVertical: 0 }]}>{data?.kpis?.critical_alerts || 0}</Text>
                  <Text style={[styles.metaText, { marginTop: 4 }]}>non traitées</Text>
               </Card>

               <Card ui={ui} style={{ width: '48%', padding: 16, backgroundColor: '#fff', flexGrow: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 6 }}>
                    <Feather name="message-square" size={14} color={'#7C3AED'} />
                    <Text style={[styles.metaText, { fontSize: 11, fontWeight: '600' }]}>CONVERSATIONS IA</Text>
                  </View>
                  <Text style={[styles.heroTitle, { fontSize: 28, marginVertical: 0 }]}>{data?.kpis?.ai_conversations_24h || 0}</Text>
                  <Text style={[styles.metaText, { marginTop: 4 }]}>dernières 24h</Text>
               </Card>

               <Card ui={ui} style={{ width: '48%', padding: 16, backgroundColor: '#fff', flexGrow: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 6 }}>
                    <Feather name="settings" size={14} color={theme.amber} />
                    <Text style={[styles.metaText, { fontSize: 11, fontWeight: '600' }]}>WORKFLOWS BLOQUÉS</Text>
                  </View>
                  <Text style={[styles.heroTitle, { fontSize: 28, color: theme.amber, marginVertical: 0 }]}>{data?.kpis?.blocked_workflows || 0}</Text>
                  <Text style={[styles.metaText, { marginTop: 4 }]}>en attente</Text>
               </Card>
            </View>
          </View>

          {/* ALERTES NON TRAITEES */}
          <Card ui={ui} style={{ marginBottom: 24, backgroundColor: '#fff', padding: 16 }}>
            <View style={[styles.rowBetween, { marginBottom: 16 }]}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Feather name="alert-triangle" size={18} color={theme.rose} />
                <Text style={[styles.bodyStrong, { fontSize: 16 }]}>Alertes non traitées</Text>
              </View>
              <Pressable style={{ backgroundColor: theme.surface, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6 }} onPress={() => onNavigate("admin_alerts")}>
                <Text style={{ fontSize: 13, fontWeight: '600', color: theme.text }}>Gérer</Text>
              </Pressable>
            </View>

            <View style={{ gap: 12 }}>
              {!data?.unresolved_alerts || data.unresolved_alerts.length === 0 ? (
                <Text style={[styles.metaText, { fontStyle: 'italic', paddingVertical: 8 }]}>Aucune alerte en attente.</Text>
              ) : (
                data.unresolved_alerts.map((alert: any) => (
                  <View key={alert.id} style={{ backgroundColor: '#F9FAFB', borderRadius: 8, overflow: 'hidden' }}>
                    <View style={{ borderLeftWidth: 3, borderLeftColor: theme.rose, padding: 12 }}>
                      <View style={[styles.rowBetween, { marginBottom: 4 }]}>
                        <Text style={{ color: theme.rose, fontWeight: '600', fontSize: 13 }}>{alert.severity === 'high' || alert.severity === 'CRITICAL' ? 'Critique' : 'Système'}</Text>
                        <Text style={[styles.metaText, { fontSize: 11 }]}>{alert.created_at}</Text>
                      </View>
                      <Text style={[styles.bodyText, { color: theme.text }]}>{alert.title || "Erreur Interne (IntegrityError)"}</Text>
                    </View>
                  </View>
                ))
              )}
            </View>
          </Card>

          {/* CHATBOT IA - REQUETES RISQUEES */}
          <Card ui={ui} style={{ marginBottom: 24, backgroundColor: '#fff', padding: 16, borderColor: theme.line, borderWidth: 1 }}>
            <View style={[styles.rowBetween, { marginBottom: 16 }]}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Feather name="shield" size={18} color={theme.sky} />
                <Text style={[styles.bodyStrong, { fontSize: 16 }]}>Chatbot IA — requêtes risquées</Text>
              </View>
              <Pressable style={{ backgroundColor: theme.surface, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6 }} onPress={() => triggerFeedback("Voir logs IA")}>
                <Text style={{ fontSize: 13, fontWeight: '600', color: theme.text }}>Voir logs</Text>
              </Pressable>
            </View>

            <View style={{ gap: 12 }}>
              {!data?.flagged_queries || data.flagged_queries.length === 0 ? (
                <Text style={[styles.metaText, { fontStyle: 'italic', paddingVertical: 8 }]}>Aucune requête signalée.</Text>
              ) : (
                data.flagged_queries.map((log: any) => (
                  <View key={log.id} style={{ backgroundColor: '#fff', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: theme.line }}>
                    <View style={[styles.rowBetween, { marginBottom: 8 }]}>
                      <Text style={[styles.bodyStrong, { fontSize: 13 }]}>{log.user_email}</Text>
                      <View style={{ backgroundColor: '#FFF5ED', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, borderWidth: 1, borderColor: '#FFE4CC' }}>
                        <Text style={{ color: '#C2410C', fontSize: 12, fontWeight: '600' }}>Signalé</Text>
                      </View>
                    </View>
                    <Text style={[styles.bodyText, { fontStyle: 'italic', color: theme.muted }]}>"{log.query}"</Text>
                  </View>
                ))
              )}
            </View>
          </Card>

        </>
      )}
    </ScrollView>
  );
}

// ------------------------------------------------------------------
// 2. COMPTES
// ------------------------------------------------------------------
export function AdminAccountsScreen({ ui, triggerFeedback, sessionProfile }: any) {
  const { styles, theme } = ui;
  const isAuth = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  const [newUser, setNewUser] = useState({ firstName: "", lastName: "", email: "", password: "", role: "collaborateur" });

  useEffect(() => {
    let mounted = true;
    adminService.fetchUsers().then(res => {
      if (mounted) setUsers(res || []);
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => { mounted = false; };
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  const [editingUserId, setEditingUserId] = useState<number | null>(null);

  const handleCreate = async () => {
    if (!newUser.firstName || !newUser.lastName || !newUser.email || (!editingUserId && !newUser.password)) {
      triggerFeedback("Veuillez remplir tous les champs obligatoires");
      return;
    }
    try {
      if (editingUserId) {
        await adminService.updateUser(editingUserId, {
          prenom: newUser.firstName,
          nom: newUser.lastName,
          email: newUser.email,
          role: newUser.role,
        });
        triggerFeedback("Compte modifié avec succès");
      } else {
        await adminService.createUser({ 
          name: `${newUser.firstName} ${newUser.lastName}`, 
          prenom: newUser.firstName,
          nom: newUser.lastName,
          email: newUser.email, 
          role: newUser.role, 
          mots_de_passe: newUser.password,
          mfa: true,
          temp: false
        });
        triggerFeedback("Compte créé avec succès");
      }
      setIsCreating(false);
      setEditingUserId(null);
      setNewUser({ firstName: "", lastName: "", email: "", password: "", role: "collaborateur" });
      
      // Actualisation locale optimiste
      const updatedList = await adminService.fetchUsers();
      if (updatedList) setUsers(updatedList);

    } catch (e) {
      triggerFeedback("Erreur lors de l'enregistrement");
    }
  };

  const handleEdit = (u: any) => {
    setEditingUserId(u.id);
    setNewUser({ firstName: u.prenom || "", lastName: u.nom || "", email: u.email || "", password: "", role: u.role || "collaborateur" });
    setIsCreating(true);
  };

  const handleResetPassword = async (u: any) => {
    try {
      await adminService.resetPassword(u.id, "TempPass123!");
      triggerFeedback(`Mot de passe de ${u.prenom || u.email} réinitialisé`);
    } catch (e) {
      triggerFeedback("Erreur: Mot de passe non réinitialisé");
    }
  };

  const handleToggleStatus = async (u: any) => {
    try {
      const newStatus = u.is_active === false ? true : false;
      await adminService.updateUser(u.id, { is_active: newStatus });
      const updatedUsers = users.map(user => user.id === u.id ? { ...user, is_active: newStatus } : user);
      setUsers(updatedUsers);
      triggerFeedback(`Statut de l'utilisateur modifié`);
    } catch (e) {
      triggerFeedback("Erreur lors du changement de statut");
    }
  };

  const handleDelete = async (u: any) => {
    try {
      await adminService.blockUser(u.id);
      const updatedUsers = users.map(user => user.id === u.id ? { ...user, is_active: false } : user);
      setUsers(updatedUsers);
      triggerFeedback(`Utilisateur bloqué avec succès`);
    } catch (e) {
      triggerFeedback("Erreur lors du blocage de l'utilisateur");
    }
  };

  const filteredUsers = users.filter(u => {
    const s = searchQuery.toLowerCase();
    return (u.prenom?.toLowerCase().includes(s) || u.nom?.toLowerCase().includes(s) || u.email?.toLowerCase().includes(s));
  });

  // --- VUE CRÉATION ---
  // --- VUE CRÉATION ---
  if (isCreating) {
    return (
      <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" style={styles.stack} showsVerticalScrollIndicator={false}>
        <View style={[styles.rowBetween, { marginBottom: 24, paddingHorizontal: 4 }]}>
          <View>
            <Text style={{ fontSize: 24, fontWeight: '800', color: theme.text }}>
              {editingUserId ? "Modifier le compte" : "Nouveau compte"}
            </Text>
            <Text style={{ fontSize: 14, color: theme.muted, marginTop: 4 }}>
              {editingUserId ? "Mettez à jour les informations du collaborateur" : "Ajoutez un nouveau collaborateur au système"}
            </Text>
          </View>
          <Pressable 
            onPress={() => { setIsCreating(false); setEditingUserId(null); }} 
            style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: theme.surfaceAlt, alignItems: 'center', justifyContent: 'center' }}
          >
            <Feather name="x" size={20} color={theme.text} />
          </Pressable>
        </View>

        <Card ui={ui} style={{ padding: 24, backgroundColor: '#ffffff', borderRadius: 24, shadowColor: theme.sky, shadowOpacity: 0.05, shadowRadius: 15, elevation: 4 }}>
          
          {/* IDENTITE */}
          <View style={{ marginBottom: 24 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <View style={{ width: 32, height: 32, borderRadius: 8, backgroundColor: theme.sky + '15', alignItems: 'center', justifyContent: 'center' }}>
                <Feather name="user" size={16} color={theme.sky} />
              </View>
              <Text style={[styles.bodyStrong, { fontSize: 16 }]}>Identité</Text>
            </View>

            <View style={{ flexDirection: 'row', gap: 16 }}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.label, { marginBottom: 8, color: theme.muted }]}>Prénom</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface, borderRadius: 12, paddingHorizontal: 16, height: 50, borderWidth: 1, borderColor: theme.line }}>
                  <TextInput 
                    style={{ flex: 1, fontSize: 15, color: theme.text }} 
                    placeholder="Ex: Jean" 
                    placeholderTextColor={theme.muted + '80'}
                    value={newUser.firstName} 
                    onChangeText={(t) => setNewUser({...newUser, firstName: t})} 
                  />
                </View>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.label, { marginBottom: 8, color: theme.muted }]}>Nom</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface, borderRadius: 12, paddingHorizontal: 16, height: 50, borderWidth: 1, borderColor: theme.line }}>
                  <TextInput 
                    style={{ flex: 1, fontSize: 15, color: theme.text }} 
                    placeholder="Ex: Dupont" 
                    placeholderTextColor={theme.muted + '80'}
                    value={newUser.lastName} 
                    onChangeText={(t) => setNewUser({...newUser, lastName: t})} 
                  />
                </View>
              </View>
            </View>
          </View>

          <View style={{ height: 1, backgroundColor: theme.line, marginBottom: 24 }} />

          {/* CONTACT & ACCES */}
          <View style={{ marginBottom: 24 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <View style={{ width: 32, height: 32, borderRadius: 8, backgroundColor: theme.emerald + '15', alignItems: 'center', justifyContent: 'center' }}>
                <Feather name="mail" size={16} color={theme.emerald} />
              </View>
              <Text style={[styles.bodyStrong, { fontSize: 16 }]}>Contact & Accès</Text>
            </View>

            <View style={{ marginBottom: 16 }}>
              <Text style={[styles.label, { marginBottom: 8, color: theme.muted }]}>Adresse Email</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface, borderRadius: 12, paddingHorizontal: 16, height: 50, borderWidth: 1, borderColor: theme.line }}>
                <Feather name="at-sign" size={18} color={theme.muted} style={{ marginRight: 12 }} />
                <TextInput 
                  style={{ flex: 1, fontSize: 15, color: theme.text }} 
                  placeholder="jean.dupont@entreprise.com" 
                  keyboardType="email-address" 
                  autoCapitalize="none" 
                  placeholderTextColor={theme.muted + '80'}
                  value={newUser.email} 
                  onChangeText={(t) => setNewUser({...newUser, email: t})} 
                />
              </View>
            </View>

            <View>
              <Text style={[styles.label, { marginBottom: 8, color: theme.muted }]}>{editingUserId ? "Nouveau mot de passe (optionnel)" : "Mot de passe initial"}</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface, borderRadius: 12, paddingHorizontal: 16, height: 50, borderWidth: 1, borderColor: theme.line }}>
                <Feather name="lock" size={18} color={theme.muted} style={{ marginRight: 12 }} />
                <TextInput 
                  style={{ flex: 1, fontSize: 15, color: theme.text }} 
                  placeholder="Saisissez un mot de passe sécurisé" 
                  secureTextEntry 
                  placeholderTextColor={theme.muted + '80'}
                  value={newUser.password} 
                  onChangeText={(t) => setNewUser({...newUser, password: t})} 
                />
              </View>
              {!editingUserId && (
                <Text style={{ fontSize: 11, color: theme.muted, marginTop: 6, fontStyle: 'italic' }}>L'utilisateur devra changer ce mot de passe à sa première connexion.</Text>
              )}
            </View>
          </View>

          <View style={{ height: 1, backgroundColor: theme.line, marginBottom: 24 }} />

          {/* ROLE & PERMISSIONS */}
          <View style={{ marginBottom: 32 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <View style={{ width: 32, height: 32, borderRadius: 8, backgroundColor: theme.amber + '15', alignItems: 'center', justifyContent: 'center' }}>
                <Feather name="shield" size={16} color={theme.amber} />
              </View>
              <Text style={[styles.bodyStrong, { fontSize: 16 }]}>Rôle & Permissions</Text>
            </View>

            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12, paddingBottom: 8 }}>
              {[
                { id: "collaborateur", label: "Collaborateur", icon: "user", color: theme.text },
                { id: "manager", label: "Manager", icon: "users", color: theme.sky },
                { id: "rh", label: "RH", icon: "briefcase", color: theme.emerald },
                { id: "admin", label: "Admin", icon: "shield", color: theme.rose },
              ].map((roleOption) => (
                <Pressable
                  key={roleOption.id}
                  onPress={() => setNewUser({...newUser, role: roleOption.id})}
                  style={{
                    flexDirection: 'row',
                    alignItems: 'center',
                    paddingHorizontal: 16,
                    paddingVertical: 12,
                    borderRadius: 16,
                    borderWidth: 2,
                    borderColor: newUser.role === roleOption.id ? roleOption.color : theme.line,
                    backgroundColor: newUser.role === roleOption.id ? roleOption.color + '0A' : theme.surface,
                    gap: 8
                  }}
                >
                  <Feather name={roleOption.icon as any} size={16} color={newUser.role === roleOption.id ? roleOption.color : theme.muted} />
                  <Text style={{ 
                    fontSize: 14, 
                    fontWeight: newUser.role === roleOption.id ? '700' : '500', 
                    color: newUser.role === roleOption.id ? roleOption.color : theme.text 
                  }}>
                    {roleOption.label}
                  </Text>
                </Pressable>
              ))}
            </ScrollView>
          </View>

          <Pressable 
            onPress={handleCreate}
            style={({ pressed }) => ({
              backgroundColor: theme.sky,
              paddingVertical: 16,
              borderRadius: 16,
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'row',
              gap: 8,
              opacity: pressed ? 0.9 : 1,
              shadowColor: theme.sky,
              shadowOffset: { width: 0, height: 4 },
              shadowOpacity: 0.3,
              shadowRadius: 8,
              elevation: 4
            })}
          >
            <Feather name={editingUserId ? "save" : "check"} size={20} color="#ffffff" />
            <Text style={{ color: '#ffffff', fontSize: 16, fontWeight: '700' }}>
              {editingUserId ? "Enregistrer les modifications" : "Créer le compte utilisateur"}
            </Text>
          </Pressable>
        </Card>
      </ScrollView>
    );
  }

  // --- VUE LISTE ---
  return (
    <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" style={styles.stack} showsVerticalScrollIndicator={false}>
      <View style={[styles.rowBetween, { marginBottom: 16 }]}>
        <SectionHeader icon="users" title="Gestion des Comptes" ui={ui} />
        <PrimaryButton icon="plus" label="Créer un compte" onPress={() => setIsCreating(true)} ui={ui} />
      </View>
      
      {/* Barre de recherche */}
      <View style={{ flexDirection: 'row', gap: 12, marginBottom: 24 }}>
        <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderWidth: 1, borderColor: theme.line, borderRadius: 8, paddingHorizontal: 12 }}>
          <Feather name="search" size={18} color={theme.muted} />
          <TextInput 
            style={{ flex: 1, paddingVertical: 12, paddingHorizontal: 8, fontSize: 14, color: theme.text }} 
            placeholder="Rechercher nom, email..." 
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
        <SecondaryButton label="Filtrer" onPress={() => {}} ui={ui} />
      </View>

      <Card ui={ui} style={{ padding: 0, overflow: 'hidden' }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={{ minWidth: 700, flex: 1 }}>
            {/* Header de table */}
            <View style={{ flexDirection: 'row', padding: 16, backgroundColor: '#F9FAFB', borderBottomWidth: 1, borderBottomColor: theme.line }}>
              <Text style={[styles.label, { flex: 2, fontSize: 12 }]}>Utilisateur</Text>
              <Text style={[styles.label, { flex: 1, fontSize: 12 }]}>Rôle</Text>
              <Text style={[styles.label, { flex: 0.5, fontSize: 12 }]}>Actif</Text>
              <Text style={[styles.label, { width: 150, fontSize: 12, textAlign: 'right' }]}>Actions</Text>
            </View>

            {/* Lignes du tableau */}
            {loading ? <ActivityIndicator color={theme.sky} style={{ padding: 20 }} /> : filteredUsers.map((u, index) => (
              <View key={u.id || index} style={{ flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                <View style={{ flex: 2 }}>
                  <Text style={[styles.bodyStrong, { fontSize: 14 }]}>{u.prenom} {u.nom}</Text>
                  <Text style={[styles.metaText, { fontSize: 12 }]}>{u.email}</Text>
                </View>
                
                <View style={{ flex: 1, alignItems: 'flex-start' }}>
                  <StatusBadge label={u.role?.charAt(0).toUpperCase() + u.role?.slice(1) || 'Collaborateur'} tone="info" ui={ui} />
                </View>

                <View style={{ flex: 0.5 }}>
                  <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: u.is_active !== false ? theme.emerald : theme.rose }} />
                </View>

                <View style={{ width: 150, flexDirection: 'row', justifyContent: 'flex-end', gap: 8 }}>
                  <Pressable onPress={() => handleEdit(u)} style={{ padding: 6, borderRadius: 6, backgroundColor: '#F3F4F6' }}>
                    <Feather name="edit-2" size={16} color={theme.text} />
                  </Pressable>
                  <Pressable onPress={() => handleResetPassword(u)} style={{ padding: 6, borderRadius: 6, backgroundColor: '#F3F4F6' }}>
                    <Feather name="key" size={16} color={theme.text} />
                  </Pressable>
                  <Pressable onPress={() => handleToggleStatus(u)} style={{ padding: 6, borderRadius: 6, backgroundColor: u.is_active !== false ? '#FEF2F2' : '#ECFDF5' }}>
                    <Feather name={u.is_active !== false ? "x-circle" : "check-circle"} size={16} color={u.is_active !== false ? theme.rose : theme.emerald} />
                  </Pressable>
                  <Pressable onPress={() => handleDelete(u)} style={{ padding: 6, borderRadius: 6, backgroundColor: theme.rose }}>
                    <Feather name="trash-2" size={16} color="#fff" />
                  </Pressable>
                </View>
              </View>
            ))}
            
            {!loading && filteredUsers.length === 0 && (
               <Text style={[styles.bodyText, { padding: 24, textAlign: 'center', fontStyle: 'italic' }]}>Aucun utilisateur trouvé.</Text>
            )}
          </View>
        </ScrollView>
      </Card>
    </ScrollView>
  );
}

// ------------------------------------------------------------------
// 3. ALERTES
// ------------------------------------------------------------------
export function AdminAlertsScreen({ ui, triggerFeedback, sessionProfile }: any) {
  const { styles, theme } = ui;
  const isAuth = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    adminService.fetchAlerts().then(res => {
      if (mounted) setAlerts(res || []);
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => { mounted = false; };
  }, []);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  return (
    <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" style={styles.stack} showsVerticalScrollIndicator={false}>
      <SectionHeader icon="alert-triangle" title="Alertes Sécurité" ui={ui} />
      
      {loading ? <ActivityIndicator color={theme.sky} style={{ marginTop: 24 }} /> : (
        <View style={{ gap: 12, paddingBottom: 32 }}>
          {alerts.length === 0 ? (
            <Text style={[styles.metaText, { fontStyle: 'italic', textAlign: 'center', marginTop: 24 }]}>Aucune alerte trouvée.</Text>
          ) : (
            alerts.map((a: any) => {
              const isCritical = a.severity?.toUpperCase() === 'CRITICAL' || a.severity?.toUpperCase() === 'HIGH';
              const isResolved = a.status?.toUpperCase() === 'RESOLVED';
              return (
                <Card key={a.id || Math.random()} ui={ui} style={{ padding: 16, borderLeftWidth: 4, borderLeftColor: isResolved ? theme.emerald : (isCritical ? theme.rose : theme.amber) }}>
                  <View style={[styles.rowBetween, { marginBottom: 12 }]}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, gap: 8 }}>
                      <Feather name={isResolved ? "check-circle" : "shield"} size={18} color={isResolved ? theme.emerald : (isCritical ? theme.rose : theme.amber)} />
                      <Text style={[styles.bodyStrong, { fontSize: 16, color: theme.text, flexShrink: 1 }]} numberOfLines={2}>
                        {a.title || a.alert_type || 'Alerte Système'}
                      </Text>
                    </View>
                    <View style={{ backgroundColor: isResolved ? theme.emerald + '20' : theme.surfaceAlt, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                      <Text style={{ fontSize: 11, fontWeight: '700', color: isResolved ? theme.emerald : theme.text }}>
                        {a.status || 'NEW'}
                      </Text>
                    </View>
                  </View>

                  <Text style={[styles.bodyText, { marginBottom: 16, color: theme.muted }]} numberOfLines={2}>
                    {a.description || "Aucune description détaillée n'a été fournie pour cet événement."}
                  </Text>

                  <View style={[styles.rowBetween, { borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 12 }]}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Feather name="clock" size={12} color={theme.muted} />
                      <Text style={[styles.metaText, { fontSize: 11 }]}>
                        {a.created_at ? new Date(a.created_at).toLocaleString() : 'Récemment'}
                      </Text>
                    </View>
                    {!isResolved && (
                      <Pressable onPress={() => triggerFeedback("Alerte marquée comme résolue")} style={{ backgroundColor: theme.sky + '15', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6, flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        <Feather name="check" size={14} color={theme.sky} />
                        <Text style={{ fontSize: 12, fontWeight: '600', color: theme.sky }}>Résoudre</Text>
                      </Pressable>
                    )}
                  </View>
                </Card>
              );
            })
          )}
        </View>
      )}
    </ScrollView>
  );
}

// ------------------------------------------------------------------
// 4. LOGS
// ------------------------------------------------------------------
export function AdminLogsScreen({ ui: propUi, sessionProfile }: any) {
  const contextUi = useUi().ui;
  const ui = propUi || contextUi;
  const { styles, theme } = ui;
  const isAuth = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  const [activeTab, setActiveTab] = useState<'system' | 'chatbot'>('system');
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    
    const loadLogs = async () => {
      try {
        const res = activeTab === 'system' 
          ? await adminService.fetchLogs() 
          : await adminService.fetchChatbotLogs();
        if (mounted) setLogs(res || []);
      } catch (e) {
        if (mounted) {
          if (activeTab === 'system') {
            setLogs([{id: 1, action: "FETCH_ERROR", details: "Could not connect to history service", timestamp: new Date().toISOString()}]);
          } else {
            setLogs([{id: 1, query: "Erreur", response: "Impossible de récupérer les logs d'audit du Chatbot IA", risk_level: "high", created_at: new Date().toISOString()}]);
          }
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadLogs();
    return () => { mounted = false; };
  }, [activeTab]);

  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  return (
    <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" style={styles.stack} showsVerticalScrollIndicator={false}>
      <SectionHeader icon="list" title="Traçabilité & Logs" ui={ui} />
      
      {/* TABS SELECTOR */}
      <View style={{ flexDirection: 'row', backgroundColor: theme.surfaceAlt, padding: 4, borderRadius: 8, marginBottom: 16 }}>
        <Pressable 
          style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'system' ? theme.card : 'transparent', borderRadius: 6 }}
          onPress={() => setActiveTab('system')}
        >
          <Text style={{ fontWeight: activeTab === 'system' ? '600' : '400', color: activeTab === 'system' ? theme.text : theme.muted }}>Logs Système</Text>
        </Pressable>
        <Pressable 
          style={{ flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: activeTab === 'chatbot' ? theme.card : 'transparent', borderRadius: 6 }}
          onPress={() => setActiveTab('chatbot')}
        >
          <Text style={{ fontWeight: activeTab === 'chatbot' ? '600' : '400', color: activeTab === 'chatbot' ? theme.text : theme.muted }}>Logs Chatbot IA</Text>
        </Pressable>
      </View>

      {loading ? <ActivityIndicator color={theme.sky} style={{ marginTop: 24 }} /> : (
        activeTab === 'system' ? (
          logs.map((l: any) => (
            <View key={l.id || Math.random()} style={{ paddingVertical: 12, borderBottomWidth: 1, borderColor: theme.line }}>
              <View style={styles.rowBetween}>
                <Text style={styles.bodyStrong}>{l.action}</Text>
                <Text style={styles.metaText}>{new Date(l.timestamp || Date.now()).toLocaleTimeString()}</Text>
              </View>
              <Text style={styles.metaText}>{l.details}</Text>
            </View>
          ))
        ) : (
          logs.length === 0 ? (
            <Text style={[styles.metaText, { fontStyle: 'italic', paddingVertical: 16, textAlign: 'center' }]}>Aucun log d'IA disponible.</Text>
          ) : (
            logs.map((l: any) => {
              const riskTone = l.risk_level === 'high' || l.risk_level === 'Signalé' || l.risk_level === 'Dangereux' 
                ? 'critical' 
                : l.risk_level === 'medium' 
                ? 'warning' 
                : 'success';
              const riskLabel = l.risk_level === 'high' || l.risk_level === 'Signalé' || l.risk_level === 'Dangereux' 
                ? 'Critique' 
                : l.risk_level === 'medium' 
                ? 'Modéré' 
                : 'Faible';

              return (
                <View key={l.id || Math.random()} style={{ padding: 14, borderRadius: 12, borderWidth: 1, borderColor: theme.line, backgroundColor: theme.card, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1 }}>
                  <View style={[styles.rowBetween, { marginBottom: 10 }]}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Feather name="user" size={14} color={theme.muted} />
                      <Text style={[styles.metaText, { fontWeight: '600' }]}>Utilisateur: {l.user_id ? `ID #${l.user_id}` : 'Anonyme'}</Text>
                    </View>
                    <Text style={styles.metaText}>{new Date(l.created_at || Date.now()).toLocaleDateString()} {new Date(l.created_at || Date.now()).toLocaleTimeString()}</Text>
                  </View>

                  <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                      <Text style={[styles.metaText, { fontSize: 11 }]}>RISQUE :</Text>
                      <StatusBadge label={riskLabel} tone={riskTone} ui={ui} />
                    </View>
                    {l.conversation_id && (
                      <Text style={[styles.metaText, { fontSize: 11 }]}>CONV. #{l.conversation_id}</Text>
                    )}
                  </View>

                  <View style={{ backgroundColor: theme.surfaceAlt, padding: 10, borderRadius: 8, marginBottom: 8 }}>
                    <Text style={{ fontSize: 11, fontWeight: '700', color: theme.muted, textTransform: 'uppercase', marginBottom: 4 }}>Question</Text>
                    <Text style={[styles.bodyText, { fontStyle: 'italic' }]}>"{l.query}"</Text>
                  </View>

                  <View style={{ backgroundColor: theme.surfaceAlt, padding: 10, borderRadius: 8 }}>
                    <Text style={{ fontSize: 11, fontWeight: '700', color: theme.muted, textTransform: 'uppercase', marginBottom: 4 }}>Réponse Assistant</Text>
                    <Text style={styles.bodyText}>{l.response}</Text>
                  </View>
                </View>
              );
            })
          )
        )
      )}
    </ScrollView>
  );
}

import { InfoRow } from "../components/Shared";

// ------------------------------------------------------------------
// 5. PROFIL
// ------------------------------------------------------------------
export function AdminProfileScreen({ ui, sessionProfile, setAuthStep }: any) {
  const { styles, theme } = ui;
  const isAuth = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role);
  
  if (!isAuth) return <UnauthorizedScreen ui={ui} />;

  return (
    <ScrollView automaticallyAdjustKeyboardInsets={true} keyboardShouldPersistTaps="handled" style={styles.stack} showsVerticalScrollIndicator={false}>
      
      <Card ui={ui} style={{ marginBottom: 16 }}>
        <View style={{flexDirection: "row", alignItems: "center", marginBottom: 8}}>
          <View style={[styles.profileAvatar, {width: 64, height: 64, borderRadius: 32}]}>
            <Text style={{fontSize: 24, color: '#ffffff', fontWeight: 'bold'}}>{sessionProfile?.avatarInitials || sessionProfile?.firstName?.charAt(0) || "U"}</Text>
          </View>
          <View style={{marginLeft: 16}}>
            <Text style={styles.heroTitle}>{sessionProfile?.firstName || ""} {sessionProfile?.lastName || ""}</Text>
            <Text style={styles.mutedText}>{sessionProfile?.role || "Utilisateur"} · {sessionProfile?.department || "Général"}</Text>
          </View>
        </View>
      </Card>

      <SectionHeader icon="user" title="Informations Personnelles" ui={ui} />
      <Card ui={ui} style={{ marginBottom: 16 }}>
        <View style={ui.styles.infoGrid}>
          <InfoRow label="Email" value={sessionProfile?.email || "Non renseigné"} ui={ui} />
          <InfoRow label="Téléphone" value={sessionProfile?.phone || "Non renseigné"} ui={ui} />
          <InfoRow label="Localisation" value={sessionProfile?.location || "Non renseigné"} ui={ui} />
          <InfoRow label="Matricule" value={sessionProfile?.employeeId || "Non renseigné"} ui={ui} />
        </View>
      </Card>

      <SectionHeader icon="briefcase" title="Informations Professionnelles" ui={ui} />
      <Card ui={ui} style={{ marginBottom: 16 }}>
        <View style={ui.styles.infoGrid}>
          <InfoRow label="Date d'embauche" value={sessionProfile?.hireDate || "Non renseigné"} ui={ui} />
          <InfoRow label="Ancienneté" value={sessionProfile?.tenure || "Non renseigné"} ui={ui} />
          <InfoRow label="Type de contrat" value={sessionProfile?.contractType || "Non défini"} ui={ui} />
          <InfoRow label="Département" value={sessionProfile?.department || "Non défini"} ui={ui} />
          <InfoRow label="Poste" value={sessionProfile?.position || "Non défini"} ui={ui} />
          <InfoRow label="Manager" value={sessionProfile?.manager || "Non défini"} ui={ui} />
          <InfoRow label="Statut Employé" value={sessionProfile?.status || "Actif"} ui={ui} />
        </View>
      </Card>

      <SectionHeader icon="settings" title="Profil & Paramètres" ui={ui} />
      <Card ui={ui} style={{ marginBottom: 24, padding: 0 }}>
        
        <Pressable onPress={() => {}} style={{flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line}}>
          <View style={{flexDirection: "row", alignItems: "center"}}>
            <View style={{width: 36, height: 36, borderRadius: 10, justifyContent: "center", alignItems: "center", marginRight: 12, backgroundColor: theme.surfaceAlt}}>
              <Feather name="globe" size={18} color={theme.text} />
            </View>
            <Text style={{fontSize: 15, fontWeight: "600", color: theme.text}}>Langue de l'application</Text>
          </View>
          <Feather name="chevron-right" size={20} color={theme.muted} />
        </Pressable>

        <Pressable onPress={() => {}} style={{flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line}}>
          <View style={{flexDirection: "row", alignItems: "center"}}>
            <View style={{width: 36, height: 36, borderRadius: 10, justifyContent: "center", alignItems: "center", marginRight: 12, backgroundColor: theme.surfaceAlt}}>
              <Feather name="lock" size={18} color={theme.text} />
            </View>
            <Text style={{fontSize: 15, fontWeight: "600", color: theme.text}}>Sécurité</Text>
          </View>
          <Feather name="chevron-right" size={20} color={theme.muted} />
        </Pressable>

        <Pressable onPress={() => {}} style={{flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 16, borderBottomWidth: 1, borderBottomColor: theme.line}}>
          <View style={{flexDirection: "row", alignItems: "center"}}>
            <View style={{width: 36, height: 36, borderRadius: 10, justifyContent: "center", alignItems: "center", marginRight: 12, backgroundColor: theme.surfaceAlt}}>
              <Feather name="bell" size={18} color={theme.text} />
            </View>
            <Text style={{fontSize: 15, fontWeight: "600", color: theme.text}}>Préférences de notifications</Text>
          </View>
          <Feather name="chevron-right" size={20} color={theme.muted} />
        </Pressable>

        <Pressable onPress={() => setAuthStep("login")} style={{flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 16}}>
          <View style={{flexDirection: "row", alignItems: "center"}}>
            <View style={{width: 36, height: 36, borderRadius: 10, justifyContent: "center", alignItems: "center", marginRight: 12, backgroundColor: theme.surfaceAlt}}>
              <Feather name="log-out" size={18} color={theme.text} />
            </View>
            <Text style={{fontSize: 15, fontWeight: "600", color: theme.text}}>Se déconnecter</Text>
          </View>
          <Feather name="chevron-right" size={20} color={theme.muted} />
        </Pressable>

      </Card>
    </ScrollView>
  );
}
