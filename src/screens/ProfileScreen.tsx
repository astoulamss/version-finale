import React, { useState, useEffect } from "react";
import { View, Text, Pressable, ScrollView, TextInput, StyleSheet, Switch, DevSettings } from "react-native";
import { Feather } from "@expo/vector-icons";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { SettingSwitch, SettingRow, ProfileSummary, InfoRow } from "../components/Shared";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusBadge } from "../components/ui/Badge";
import { EmployeeProfile, ViewId, Ui } from "../types";
import { useLanguage, SupportedLanguage } from "../contexts/LanguageContext";
import { BackButton } from "../components/ui/BackButton";
import AsyncStorage from "@react-native-async-storage/async-storage";

type SettingsView = "main" | "language" | "security" | "notifications";

export function ProfileScreen({
  biometricEnabled,
  isDark,
  language,
  languageOpen,
  notificationEnabled,
  onEditProfile,
  onOpenPrivacy,
  onLogout,
  onNavigate,
  sessionProfile,
  setBiometricEnabled,
  setIsDark,
  setLanguage,
  setLanguageOpen,
  setNotificationEnabled,
  triggerFeedback,
  ui,
}: {
  biometricEnabled: boolean;
  isDark: boolean;
  language: SupportedLanguage;
  languageOpen: boolean;
  notificationEnabled: boolean;
  onEditProfile: () => void;
  onOpenPrivacy: () => void;
  onLogout: () => void;
  onNavigate?: (view: ViewId) => void;
  sessionProfile: EmployeeProfile;
  setBiometricEnabled: (value: boolean) => void;
  setIsDark: (value: boolean) => void;
  setLanguage: (value: SupportedLanguage) => void;
  setLanguageOpen: (value: boolean) => void;
  setNotificationEnabled: (value: boolean) => void;
  triggerFeedback: (label?: string) => void;
  ui: Ui;
}) {
  const { styles, theme } = ui;
  const { t, isRTL } = useLanguage();
  const [activeView, setActiveView] = useState<SettingsView>("main");

  // Security State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [secSuccess, setSecSuccess] = useState(false);

  // Notification State
  const [notifState, setNotifState] = useState({
    push: true,
    hr_requests: true,
    leave_validations: true,
    manager_messages: true,
    evaluations: false,
    trainings: true
  });

  useEffect(() => {
    AsyncStorage.getItem('notif_prefs').then(val => {
      if (val) setNotifState(JSON.parse(val));
    });
  }, []);

  const saveNotifState = async (newState: typeof notifState) => {
    setNotifState(newState);
    await AsyncStorage.setItem('notif_prefs', JSON.stringify(newState));
    triggerFeedback("Enregistrer les préférences");
  };

  const validatePassword = () => {
    const hasLength = newPassword.length >= 8;
    const hasUpper = /[A-Z]/.test(newPassword);
    const hasLower = /[a-z]/.test(newPassword);
    const hasNumber = /[0-9]/.test(newPassword);
    const hasSpecial = /[^A-Za-z0-9]/.test(newPassword);
    const match = newPassword === confirmPassword && newPassword !== "";
    return { hasLength, hasUpper, hasLower, hasNumber, hasSpecial, match };
  };

  const v = validatePassword();
  const isPasswordValid = v.hasLength && v.hasUpper && v.hasLower && v.hasNumber && v.hasSpecial && v.match && currentPassword.length > 0;

  const [isLoading, setIsLoading] = useState(false);

  const handlePasswordSubmit = async () => {
    if (isPasswordValid) {
      setIsLoading(true);
      try {
        const authService = require("../services/auth.service").default;
        await authService.changePassword(currentPassword, newPassword);
        
        setSecSuccess(true);
        triggerFeedback("Votre mot de passe a été modifié avec succès.");
        setTimeout(() => {
          setSecSuccess(false);
          setCurrentPassword("");
          setNewPassword("");
          setConfirmPassword("");
          setActiveView("main");
        }, 2000);
      } catch (e: any) {
        triggerFeedback(e.message || "Erreur de changement de mot de passe");
      } finally {
        setIsLoading(false);
      }
    } else {
      triggerFeedback("Veuillez respecter les critères de sécurité");
    }
  };

  const handleLanguageSelect = async (lang: SupportedLanguage) => {
    await setLanguage(lang);
    triggerFeedback(t("profile.language", { lang }));
  };

  const ChevronRow = ({ icon, label, onPress }: { icon: any, label: string, onPress: () => void }) => (
    <Pressable onPress={onPress} style={localStyles.chevronRow}>
      <View style={localStyles.rowLeft}>
        <View style={[localStyles.iconBox, { backgroundColor: theme.surfaceAlt }]}>
          <Feather name={icon} size={18} color={theme.text} />
        </View>
        <Text style={[localStyles.rowLabel, { color: theme.text }]}>{label}</Text>
      </View>
      <Feather name="chevron-right" size={20} color={theme.muted} />
    </Pressable>
  );

  const HeaderNav = ({ title, onBack }: { title: string, onBack: () => void }) => (
    <View style={localStyles.headerNav}>
      <View style={{ marginRight: 12 }}>
        <BackButton onPress={onBack} ui={ui} />
      </View>
      <Text style={[localStyles.headerTitle, { color: theme.text }]}>{title}</Text>
    </View>
  );

  if (activeView === "language") {
    return (
      <View style={styles.stack}>
        <HeaderNav title="Langue de l'application" onBack={() => setActiveView("main")} />
        <Card ui={ui}>
          {(["fr", "en", "ar"] as SupportedLanguage[]).map((langKey) => (
            <Pressable
              key={langKey}
              onPress={() => handleLanguageSelect(langKey)}
              style={localStyles.languageOption}
            >
              <Text style={[styles.bodyStrong, { color: language === langKey ? theme.sky : theme.text }]}>
                {t(`language.${langKey}`)}
              </Text>
              {language === langKey && <Feather name="check" size={20} color={theme.sky} />}
            </Pressable>
          ))}
        </Card>
      </View>
    );
  }

  const PasswordField = ({ label, placeholder, value, onChangeText, errorContent }: any) => {
    const [show, setShow] = React.useState(false);
    return (
      <View style={{ marginBottom: 24 }}>
        <Text style={{ fontSize: 14, fontWeight: "600", marginBottom: 8, color: theme.text }}>{label}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: theme.line, borderRadius: 8, paddingHorizontal: 12, height: 48, backgroundColor: theme.card }}>
          <Feather name="lock" size={18} color={theme.muted} style={{ marginRight: 8 }} />
          <TextInput
            secureTextEntry={!show}
            style={{ flex: 1, color: theme.text, fontSize: 15, height: '100%' }}
            placeholder={placeholder}
            placeholderTextColor={theme.muted}
            value={value}
            onChangeText={onChangeText}
          />
          <Pressable onPress={() => setShow(!show)} style={{ padding: 4 }}>
            <Feather name={show ? "eye-off" : "eye"} size={18} color={theme.muted} />
          </Pressable>
        </View>
        {errorContent}
      </View>
    );
  };

  if (activeView === "security") {
    return (
      <View style={styles.stack}>
        <View style={{ backgroundColor: theme.card, borderRadius: 12, padding: 20, borderWidth: 1, borderColor: theme.line }}>
          {secSuccess ? (
            <View style={{ alignItems: "center", padding: 20 }}>
              <Feather name="check-circle" size={48} color={theme.emerald} />
              <Text style={[styles.cardTitle, { marginTop: 16, textAlign: "center" }]}>Votre mot de passe a été modifié avec succès.</Text>
            </View>
          ) : (
            <>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 24, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: theme.line }}>
                <View style={{ marginRight: 12 }}>
                  <BackButton onPress={() => setActiveView("main")} ui={ui} />
                </View>
                <Feather name="lock" size={20} color={theme.text} style={{ marginRight: 10 }} />
                <Text style={{ fontSize: 18, fontWeight: 'bold', color: theme.text }}>Sécurité & Mot de passe</Text>
              </View>

              <PasswordField 
                label="Mot de passe actuel" 
                placeholder="Mot de passe actuel" 
                value={currentPassword} 
                onChangeText={setCurrentPassword} 
              />

              <PasswordField 
                label="Nouveau mot de passe" 
                placeholder="Nouveau mot de passe" 
                value={newPassword} 
                onChangeText={setNewPassword} 
                errorContent={newPassword.length > 0 ? (
                  <View style={{ marginTop: 8 }}>
                    <Text style={{ color: v.hasLength ? theme.emerald : theme.rose, fontSize: 12 }}>{v.hasLength ? "✓" : "✗"} {"Au moins 8 caractères"}</Text>
                    <Text style={{ color: v.hasUpper ? theme.emerald : theme.rose, fontSize: 12 }}>{v.hasUpper ? "✓" : "✗"} {"Au moins 1 majuscule"}</Text>
                    <Text style={{ color: v.hasLower ? theme.emerald : theme.rose, fontSize: 12 }}>{v.hasLower ? "✓" : "✗"} {"Au moins 1 minuscule"}</Text>
                    <Text style={{ color: v.hasNumber ? theme.emerald : theme.rose, fontSize: 12 }}>{v.hasNumber ? "✓" : "✗"} {"Au moins 1 chiffre"}</Text>
                    <Text style={{ color: v.hasSpecial ? theme.emerald : theme.rose, fontSize: 12 }}>{v.hasSpecial ? "✓" : "✗"} {"Au moins 1 caractère spécial"}</Text>
                  </View>
                ) : null}
              />

              <PasswordField 
                label="Confirmer le nouveau mot de passe" 
                placeholder="Répétez le nouveau mot de passe" 
                value={confirmPassword} 
                onChangeText={setConfirmPassword} 
                errorContent={confirmPassword.length > 0 && !v.match ? (
                  <Text style={{ color: theme.rose, fontSize: 12, marginTop: 4 }}>Les mots de passe ne correspondent pas</Text>
                ) : null}
              />

              <Pressable 
                onPress={handlePasswordSubmit} 
                style={({ pressed }) => [{
                  backgroundColor: theme.sky,
                  paddingVertical: 14,
                  borderRadius: 8,
                  alignItems: 'center',
                  marginTop: 8,
                  opacity: pressed || isLoading ? 0.8 : 1
                }]}
                disabled={isLoading}
              >
                <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 15 }}>
                  {isLoading ? "Chargement..." : "Confirmer le nouveau mot de passe"}
                </Text>
              </Pressable>
            </>
          )}
        </View>
      </View>
    );
  }

  if (activeView === "notifications") {
    const ToggleRow = ({ labelKey, field }: { labelKey: string, field: keyof typeof notifState }) => (
      <View style={localStyles.toggleRow}>
        <Text style={[localStyles.rowLabel, { color: theme.text }]}>{t(`notifications.${labelKey}`)}</Text>
        <Switch
          value={notifState[field]}
          onValueChange={(val) => saveNotifState({ ...notifState, [field]: val })}
          trackColor={{ false: theme.line, true: theme.sky }}
        />
      </View>
    );

    return (
      <View style={styles.stack}>
        <HeaderNav title="Préférences de notifications" onBack={() => setActiveView("main")} />
        <Card ui={ui}>
          <ToggleRow labelKey="push" field="push" />
          <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
          <ToggleRow labelKey="hr_requests" field="hr_requests" />
          <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
          <ToggleRow labelKey="leave_validations" field="leave_validations" />
          <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
          <ToggleRow labelKey="manager_messages" field="manager_messages" />
          <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
          <ToggleRow labelKey="evaluations" field="evaluations" />
          <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
          <ToggleRow labelKey="trainings" field="trainings" />
        </Card>
      </View>
    );
  }

  // MAIN VIEW
  return (
    <View style={styles.stack}>
      <Card ui={ui}>
        <View style={{flexDirection: "row", alignItems: "center", marginBottom: 8}}>
          <View style={[styles.profileAvatar, {width: 64, height: 64, borderRadius: 32}]}>
            <Text style={{fontSize: 24, color: '#ffffff', fontWeight: 'bold'}}>{sessionProfile.avatarInitials}</Text>
          </View>
          <View style={{marginLeft: 16}}>
            <Text style={styles.heroTitle}>{sessionProfile.firstName} {sessionProfile.lastName}</Text>
            <Text style={styles.mutedText}>{sessionProfile.role} · {sessionProfile.department}</Text>
          </View>
        </View>
      </Card>
      <SectionHeader icon="user" title="Informations Personnelles" ui={ui} />
      <Card ui={ui}>
        <View style={ui.styles.infoGrid}>
          <InfoRow label="Email" value={sessionProfile.email} ui={ui} />
          <InfoRow label="Téléphone" value={sessionProfile.phone || "Non renseigné"} ui={ui} />
          <InfoRow label="Localisation" value={sessionProfile.location || "Non renseigné"} ui={ui} />
          <InfoRow label="Matricule" value={sessionProfile.employeeId} ui={ui} />
        </View>
      </Card>

      <SectionHeader icon="briefcase" title="Informations Professionnelles" ui={ui} />
      <Card ui={ui}>
        <View style={ui.styles.infoGrid}>
          <InfoRow label="Date d'embauche" value={sessionProfile.hireDate || "Non renseigné"} ui={ui} />
          <InfoRow label="Ancienneté" value={sessionProfile.tenure} ui={ui} />
          <InfoRow label="Type de contrat" value={sessionProfile.contractType || "Non défini"} ui={ui} />
          <InfoRow label="Département" value={sessionProfile.department} ui={ui} />
          <InfoRow label="Poste" value={sessionProfile.position || "Non défini"} ui={ui} />
          <InfoRow label="Manager" value={sessionProfile.manager} ui={ui} />
          <InfoRow label="Statut Employé" value={sessionProfile.status || "Actif"} ui={ui} />
        </View>
      </Card>

      
      <SectionHeader icon="settings" title="Profil & Paramètres" ui={ui} />
      <Card ui={ui}>
        <ChevronRow icon="globe" label="Langue de l'application" onPress={() => setActiveView("language")} />
        <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
        <ChevronRow icon="lock" label="Sécurité" onPress={() => setActiveView("security")} />
        <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
        <ChevronRow icon="bell" label="Préférences de notifications" onPress={() => setActiveView("notifications")} />
        <View style={[localStyles.divider, { backgroundColor: theme.line }]} />
        <ChevronRow icon="log-out" label="Se déconnecter" onPress={onLogout} />
      </Card>
    </View>
  );
}

const localStyles = StyleSheet.create({
  chevronRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
  },
  rowLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  rowLabel: {
    fontSize: 15,
    fontWeight: "600",
  },
  divider: {
    height: 1,
    marginVertical: 4,
  },
  headerNav: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: "800",
  },
  languageOption: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(0,0,0,0.05)",
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    height: 48,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  toggleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
  }
});
