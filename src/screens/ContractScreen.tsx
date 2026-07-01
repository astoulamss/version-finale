import React, { useState, useEffect } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Card, AICard } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { Ui, Contract, EmployeeProfile } from "../types";
import { contractService } from "../services/contract.service";


interface Props {
  ui: Ui;
  sessionProfile: EmployeeProfile;
  triggerFeedback: (msg?: string) => void;
}

export function ContractScreen({ ui, sessionProfile, triggerFeedback }: Props) {
  const { styles, theme } = ui;
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    
    const loadContract = async () => {
      try {
        setLoading(true);
        const data = await contractService.getMyContract();
        if (mounted) {
          setContract(data);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          if (err.response?.status === 404) {
            setContract(null);
            setError(null);
          } else {
            setError("Erreur lors du chargement de votre contrat.");
          }
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadContract();

    return () => { mounted = false; };
  }, []);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} showsVerticalScrollIndicator={false}>
      <View style={[styles.stack, { paddingBottom: 40 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
          <View>
            <Text style={[styles.heroTitle, { fontSize: 24, marginBottom: 4 }]}>Mon Contrat</Text>
            <Text style={styles.mutedText}>Détails et documents légaux</Text>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator color={theme.sky} style={{ marginVertical: 32 }} />
        ) : error ? (
          <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 32 }}>
            <Feather name="alert-circle" size={40} color={theme.amber} style={{ marginBottom: 16 }} />
            <Text style={[styles.bodyStrong, { color: theme.amber }]}>{error}</Text>
          </Card>
        ) : !contract ? (
          <Card ui={ui} style={{ alignItems: 'center', paddingVertical: 40 }}>
            <Feather name="file-text" size={48} color={theme.muted} style={{ marginBottom: 16, opacity: 0.5 }} />
            <Text style={[styles.bodyStrong, { marginBottom: 8 }]}>Aucun contrat actif</Text>
            <Text style={[styles.bodyText, { color: theme.muted, textAlign: 'center' }]}>
              {"Votre contrat n'a pas encore été renseigné dans le système."}
            </Text>
          </Card>
        ) : (
          <>
            <AICard ui={ui}>
              <View style={styles.rowBetween}>
                <Text style={styles.cardTitle}>{contract.position}</Text>
                <StatusBadge 
                  label={contract.contract_type} 
                  tone={contract.contract_type === 'CDI' ? "success" : "info"} 
                  ui={ui} 
                />
              </View>
              <View style={{ marginTop: 12 }}>
                <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Début :</Text> {contract.start_date}</Text>
                {contract.end_date && <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Fin :</Text> {contract.end_date}</Text>}
                {contract.salary && <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Rémunération :</Text> {contract.salary}</Text>}
                <Text style={styles.bodyText}><Text style={styles.bodyStrong}>Statut :</Text> {"Actif"}</Text>
              </View>
            </AICard>

            <SectionHeader icon="help-circle" title="Besoin d'aide ?" ui={ui} />
            <Card ui={ui}>
              <Text style={[styles.bodyText, { marginBottom: 12 }]}>
                {"Pour toute question concernant votre contrat ou si vous souhaitez demander un avenant, vous pouvez contacter les RH."}
              </Text>
              <SecondaryButton label="Ouvrir un ticket RH" icon="tag" onPress={() => {}} ui={ui} />
            </Card>
          </>
        )}
      </View>
    </ScrollView>
  );
}
