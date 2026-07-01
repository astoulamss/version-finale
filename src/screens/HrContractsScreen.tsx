import React, { useState, useEffect } from "react";

import { View, Text, ScrollView, TextInput, Pressable, ActivityIndicator, Alert } from "react-native";
import { Feather } from "@expo/vector-icons";
import { EmployeeProfile, Ui, ViewId, Contract } from "../types";
import { Card } from "../components/ui/Card";
import { SectionHeader } from "../components/ui/SectionHeader";
import { contractService } from "../services/contract.service";
import { adminService } from "../services/admin.service";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { downloadAndOpenDocument } from "../utils/document.utils";
import { BackButton } from "../components/ui/BackButton";

interface Props {
  sessionProfile: EmployeeProfile;
  triggerFeedback: (msg?: string) => void;
  ui: Ui;
  onNavigate: (view: ViewId) => void;
}

export const HrContractsScreen: React.FC<Props> = ({ sessionProfile, triggerFeedback, ui, onNavigate }) => {
  const { theme, styles } = ui;
  
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [editingContractId, setEditingContractId] = useState<number | null>(null);

  // Form state
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [contractType, setContractType] = useState("CDI");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [position, setPosition] = useState("");
  const [salary, setSalary] = useState("");

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [selectedUserName, setSelectedUserName] = useState("Sélectionner un employé");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [contractsData, usersData] = await Promise.all([
        contractService.getAllContracts(),
        adminService.fetchUsers()
      ]);
      setContracts(contractsData);
      setUsers(usersData);
    } catch (error) {
      console.error("Failed to load contracts data", error);
      triggerFeedback("Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrUpdateContract = async () => {
    if (!selectedUserId || !startDate || !position || !contractType) {
      triggerFeedback("Veuillez remplir les champs obligatoires");
      return;
    }

    try {
      setSubmitting(true);
      if (editingContractId) {
        await contractService.updateContract(editingContractId, {
          contract_type: contractType,
          start_date: startDate,
          end_date: endDate || undefined,
          position,
          salary
        });
        triggerFeedback("Contrat modifié avec succès");
      } else {
        await contractService.createContract(selectedUserId, {
          contract_type: contractType,
          start_date: startDate,
          end_date: endDate || undefined,
          position,
          salary
        });
        triggerFeedback("Contrat créé avec succès");
      }
      setShowForm(false);
      resetForm();
      loadData();
    } catch (error: any) {
      console.error("Failed to save contract", error);
      triggerFeedback(error.response?.data?.detail || "Erreur lors de l'enregistrement");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (contract: Contract) => {
    setEditingContractId(contract.id);
    setSelectedUserId(contract.user_id);
    setSelectedUserName(getUserName(contract.user_id));
    setContractType(contract.contract_type);
    setStartDate(contract.start_date);
    setEndDate(contract.end_date || "");
    setPosition(contract.position);
    setSalary(contract.salary || "");
    setShowForm(true);
  };

  const handleDelete = async (contractId: number) => {
    try {
      await contractService.deleteContract(contractId);
      triggerFeedback("Contrat supprimé");
      loadData();
    } catch (error) {
      console.error("Failed to delete contract", error);
      triggerFeedback("Erreur lors de la suppression");
    }
  };

  const handleGenerateDoc = async (contractId: number, userName: string) => {
    try {
      triggerFeedback("Génération du document en cours...");
      const response = await contractService.generateDocument(contractId);
      
      if (response.document_id) {
        await downloadAndOpenDocument(response.document_id, `Contrat_${userName}`, triggerFeedback);
      } else {
        triggerFeedback("Document généré avec succès !");
      }
    } catch (error) {
      console.error("Failed to generate doc", error);
      triggerFeedback("Erreur lors de la génération du document");
    }
  };

  const resetForm = () => {
    setEditingContractId(null);
    setSelectedUserId(null);
    setSelectedUserName("Sélectionner un employé");
    setContractType("CDI");
    setStartDate("");
    setEndDate("");
    setPosition("");
    setSalary("");
  };

  const getUserName = (userId: number) => {
    const user = users.find(u => u.id === userId);
    return user ? `${user.prenom} ${user.nom}` : `Utilisateur #${userId}`;
  };

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.background }}>
        <ActivityIndicator size="large" color={theme.sky} />
      </View>
    );
  }

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        
        <View style={styles.rowStart}>
          <View style={{ marginLeft: -8, marginRight: 8 }}>
            <BackButton onPress={() => onNavigate('operations')} ui={ui} />
          </View>
          <View>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Contrats Actifs</Text>
            <Text style={styles.mutedText}>Gestion centralisée des contrats collaborateurs</Text>
          </View>
        </View>

        {!showForm ? (
          <View style={{ marginBottom: 16 }}>
            <PrimaryButton 
              label="Nouveau Contrat" 
              icon="plus" 
              onPress={() => setShowForm(true)} 
              ui={ui} 
            />
          </View>
        ) : (
          <Card ui={ui} style={{ marginBottom: 24 }}>
            <View style={[styles.rowBetween, { marginBottom: 16 }]}>
              <Text style={[styles.heroTitle, { fontSize: 18 }]}>
                {editingContractId ? "Modifier le Contrat" : "Créer un Contrat"}
              </Text>
              <Pressable onPress={() => { setShowForm(false); resetForm(); }}>
                <Feather name="x" size={24} color={theme.muted} />
              </Pressable>
            </View>

            <View style={styles.stack}>
              <View style={{ zIndex: 10 }}>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Employé *</Text>
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
                  <Text style={{ color: theme.text }}>{selectedUserName}</Text>
                  <Feather name={dropdownOpen ? "chevron-up" : "chevron-down"} size={20} color={theme.text} />
                </Pressable>

                {dropdownOpen && (
                  <View style={{
                    backgroundColor: theme.background,
                    borderColor: theme.line,
                    borderWidth: 1,
                    borderTopWidth: 0,
                    borderBottomLeftRadius: 8,
                    borderBottomRightRadius: 8,
                    maxHeight: 200,
                    marginTop: -4,
                  }}>
                    <ScrollView nestedScrollEnabled={true}>
                      {users.map(u => (
                        <Pressable
                          key={u.id}
                          onPress={() => {
                            setSelectedUserId(u.id);
                            setSelectedUserName(`${u.prenom} ${u.nom}`);
                            setDropdownOpen(false);
                          }}
                          style={{ padding: 12, borderBottomWidth: 1, borderBottomColor: theme.line }}
                        >
                          <Text style={{ color: theme.text }}>{u.prenom} {u.nom}</Text>
                        </Pressable>
                      ))}
                    </ScrollView>
                  </View>
                )}
              </View>

              <View>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Type de Contrat *</Text>
                <View style={styles.rowStart}>
                  {['CDI', 'CDD', 'Stage', 'Alternance'].map(type => (
                    <Pressable
                      key={type}
                      onPress={() => setContractType(type)}
                      style={{
                        flex: 1,
                        padding: 10,
                        backgroundColor: contractType === type ? theme.sky : theme.cardElevated,
                        alignItems: 'center',
                        borderWidth: 1,
                        borderColor: contractType === type ? theme.sky : theme.line,
                        marginHorizontal: 2,
                        borderRadius: 8
                      }}
                    >
                      <Text style={{ color: contractType === type ? theme.textInverse : theme.text, fontSize: 12, fontWeight: '600' }}>
                        {type}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              <View>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Poste *</Text>
                <TextInput
                  style={{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                  placeholder="Ex: Développeur Fullstack"
                  placeholderTextColor={theme.muted}
                  value={position}
                  onChangeText={setPosition}
                />
              </View>

              <View style={styles.rowBetween}>
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Date de début *</Text>
                  <TextInput
                    style={{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                    placeholder="YYYY-MM-DD"
                    placeholderTextColor={theme.muted}
                    value={startDate}
                    onChangeText={setStartDate}
                  />
                </View>
                <View style={{ flex: 1, marginLeft: 8 }}>
                  <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Date de fin (Optionnel)</Text>
                  <TextInput
                    style={{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                    placeholder="YYYY-MM-DD"
                    placeholderTextColor={theme.muted}
                    value={endDate}
                    onChangeText={setEndDate}
                  />
                </View>
              </View>

              <View>
                <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Salaire (Optionnel)</Text>
                <TextInput
                  style={{ backgroundColor: theme.background, color: theme.text, borderColor: theme.line, borderWidth: 1, padding: 12, borderRadius: 8 }}
                  placeholder="Ex: 45000€"
                  placeholderTextColor={theme.muted}
                  value={salary}
                  onChangeText={setSalary}
                />
              </View>

              <View style={{ marginTop: 16 }}>
                <PrimaryButton 
                  label={submitting ? "Enregistrement..." : (editingContractId ? "Enregistrer" : "Créer le Contrat")} 
                  icon="check" 
                  onPress={handleCreateOrUpdateContract} 
                  ui={ui} 
                />
              </View>
            </View>
          </Card>
        )}

        <SectionHeader icon="list" title={`Tous les contrats (${contracts.length})`} ui={ui} />
        
        {contracts.length === 0 ? (
          <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 40 }}>
            <Feather name="file-text" size={48} color={theme.muted} style={{ marginBottom: 16, opacity: 0.5 }} />
            <Text style={styles.mutedText}>Aucun contrat enregistré.</Text>
          </Card>
        ) : (
          <View style={styles.stack}>
            {contracts.map(contract => (
              <Card key={contract.id} ui={ui} style={{ padding: 16 }}>
                <View style={styles.rowBetween}>
                  <Text style={[styles.bodyStrong, { fontSize: 16, flex: 1 }]} numberOfLines={1}>
                    {getUserName(contract.user_id)}
                  </Text>
                  <StatusBadge 
                    label={contract.contract_type} 
                    tone={contract.contract_type === 'CDI' ? "success" : "info"} 
                    ui={ui} 
                  />
                </View>
                <View style={{ marginTop: 12, marginBottom: 12 }}>
                  <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Poste :</Text> {contract.position}</Text>
                  <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Début :</Text> {contract.start_date}</Text>
                  {contract.end_date && <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Fin :</Text> {contract.end_date}</Text>}
                  {contract.salary && <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Salaire :</Text> {contract.salary}</Text>}
                </View>
                
                <View style={[styles.rowStart, { borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 12 }]}>
                  <Pressable 
                    onPress={() => handleGenerateDoc(contract.id, getUserName(contract.user_id))}
                    style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16 }}
                  >
                    <Feather name="file-text" size={16} color={theme.sky} style={{ marginRight: 6 }} />
                    <Text style={{ color: theme.sky, fontSize: 14, fontWeight: '600' }}>Générer PDF</Text>
                  </Pressable>

                  <Pressable 
                    onPress={() => handleEdit(contract)}
                    style={{ flexDirection: 'row', alignItems: 'center', marginRight: 16 }}
                  >
                    <Feather name="edit-2" size={16} color={theme.emerald} style={{ marginRight: 6 }} />
                    <Text style={{ color: theme.emerald, fontSize: 14, fontWeight: '600' }}>Modifier</Text>
                  </Pressable>
                  
                  <Pressable 
                    onPress={() => handleDelete(contract.id)}
                    style={{ flexDirection: 'row', alignItems: 'center' }}
                  >
                    <Feather name="trash-2" size={16} color={theme.amber} style={{ marginRight: 6 }} />
                    <Text style={{ color: theme.amber, fontSize: 14, fontWeight: '600' }}>Supprimer</Text>
                  </Pressable>
                </View>
              </Card>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
};
