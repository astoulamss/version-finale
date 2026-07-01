
import React, { useState, useRef, useEffect } from "react";
import { View, Text, Pressable, Animated, Easing, TextInput, StyleSheet, ScrollView, Dimensions, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Feather } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { PrimaryButton, SecondaryButton } from "../components/ui/Button";
import { AuthStep, EmployeeProfile, ViewId, Ui } from "../types";
import { getRoleLabel, UserRoleId, mapApiUserToProfile } from "../lib/auth";
import authService from "../services/auth.service";
import { saveToken } from "../utils/token.utils";

import { API_BASE_URL } from "../services/api";

// Temporary mock imports that are still in App.tsx
import { SkeletonBlock, ProfileSummary } from "../components/Shared";

const { height } = Dimensions.get('window');

const roleDisplayDetails: Record<UserRoleId, { title: string; cta: string; emoji: string }> = {
  collaborateur: {
    title: "Connexion Collaborateur",
    cta: "Se connecter",
    emoji: "👤",
  },
  rh: {
    title: "Connexion RH",
    cta: "Se connecter",
    emoji: "🏢",
  },
  manager: {
    title: "Connexion Manager",
    cta: "Se connecter",
    emoji: "👥",
  },
  admin: {
    title: "Connexion Administrateur",
    cta: "Se connecter",
    emoji: "🛡",
  },
  medecine_travail: {
    title: "Connexion Médecine / QVT",
    cta: "Se connecter",
    emoji: "❤️",
  },
  direction: {
    title: "Connexion Direction",
    cta: "Se connecter",
    emoji: "📈",
  },
};

export function AuthFlow({
  authStep,
  rememberMe,
  sessionProfile,
  setActiveView,
  setAuthStep,
  setRememberMe,
  setSessionProfile,
  triggerFeedback,
  ui,
}: {
  authStep: AuthStep;
  rememberMe: boolean;
  sessionProfile: EmployeeProfile | null;
  setActiveView: (view: ViewId) => void;
  setAuthStep: (step: AuthStep) => void;
  setRememberMe: (value: boolean) => void;
  setSessionProfile: (profile: EmployeeProfile) => void;
  triggerFeedback: (label?: string) => void;
  ui: Ui;
}) {
  const { styles, theme } = ui;
  const pulse = useRef(new Animated.Value(0.55)).current;
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [selectedRole, setSelectedRole] = useState<UserRoleId>("collaborateur");
  const [authError, setAuthError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const roleDetails = roleDisplayDetails[selectedRole] ?? roleDisplayDetails.collaborateur;

  async function handleSignIn() {
    setIsLoading(true);
    setAuthError("");
    
    try {
      const response = await authService.login(loginEmail, loginPassword);
      
      const { fetchMyEmployeeProfile } = require('../services/dashboard.service');
      let employeeData: any = null;
      try {
        employeeData = await fetchMyEmployeeProfile();
      } catch (err) {
        console.log("Employé non trouvé pour cet utilisateur, utilisation des données par défaut");
      }

      if (!response || !response.user) {
        throw new Error("Réponse serveur invalide (utilisateur manquant)");
      }

      const userProfile = mapApiUserToProfile(response.user, employeeData);

      setSessionProfile(userProfile);
      
      const role = response.user.role?.toLowerCase()?.trim() ?? "";
      
      // Fallback de sécurité (Point 3)
      if (!["admin", "manager", "rh", "medecine_travail", "direction", "collaborateur", "qvt"].includes(role)) {
        setAuthError("Votre rôle n'est pas reconnu par le système mobile.");
        setIsLoading(false);
        return;
      }

      if (role === "admin") {
        setActiveView("admin_dashboard");
      } else if (role === "medecine_travail" || role === "qvt") {
        setActiveView("qvt_dashboard");
      } else if (role === "direction") {
        setActiveView("direction_dashboard");
      } else {
        setActiveView("home");
      }

      setAuthStep("app");
      triggerFeedback(`Connexion réussie`);
    } catch (error: any) {
      const debugMsg = `ERR: ${error.message} | RESP: ${JSON.stringify(error.response?.data || 'NO_RESP')}`;
      setAuthError(debugMsg);
      triggerFeedback("Connexion refusée");
    } finally {
      setIsLoading(false);
    }
  }

  // selectRoleAction supprimé car l'application est branchée au vrai backend

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          duration: 900,
          easing: Easing.out(Easing.ease),
          toValue: 1,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          duration: 900,
          easing: Easing.in(Easing.quad),
          toValue: 0.55,
          useNativeDriver: true,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  return (
    <View style={localStyles.fullScreenContainer}>
      <StatusBar style="light" />
      
      {authStep === "splash" && (
        <SafeAreaView style={styles.authSafeArea}>
          <View style={styles.authShell}>
            <View style={styles.splashContent}>
              <Animated.View style={[styles.logoOrb, { opacity: pulse, transform: [{ scale: pulse }] }]}>
                <Feather name="cpu" size={34} color="#ffffff" />
              </Animated.View>
              <Text style={styles.authTitle}>SMART RH</Text>
              <Text style={styles.authSubtitle}>Plateforme IA RH</Text>
              <View style={styles.illustrationCard}>
                <View style={styles.illustrationNode}>
                  <Feather name="user-check" size={24} color={theme.sky} />
                </View>
                <View style={styles.illustrationLine} />
                <View style={styles.illustrationNode}>
                  <Feather name="message-circle" size={24} color={theme.emerald} />
                </View>
                <View style={styles.illustrationLine} />
                <View style={styles.illustrationNode}>
                  <Feather name="shield" size={24} color={theme.sky} />
                </View>
              </View>
              <SkeletonBlock ui={ui} />
              <PrimaryButton icon="arrow-right" label="Demarrer" onPress={() => setAuthStep("login")} ui={ui} />
            </View>
          </View>
        </SafeAreaView>
      )}

      {authStep === "login" && (
        <>
          {/* Header Section */}
          <View style={[localStyles.headerSection, { backgroundColor: theme.navy }]}>
            <SafeAreaView style={localStyles.headerInner}>
              <View style={localStyles.brandCenter}>
                <View style={[localStyles.logoOrbLarge, { backgroundColor: theme.sky, shadowColor: theme.sky }]}>
                  <Feather name="cpu" size={26} color="#ffffff" />
                </View>
                <Text style={localStyles.logoTitle}>SMART RH</Text>
                <View style={[localStyles.brandPill, { borderColor: 'rgba(255,255,255,0.18)' }]}>
                  <Feather name="lock" size={11} color="rgba(255,255,255,0.65)" />
                  <Text style={localStyles.brandPillText}>Accès sécurisé</Text>
                </View>
              </View>
            </SafeAreaView>
          </View>

          {/* Main Panel (overlapping header) */}
          <KeyboardAvoidingView 
            behavior={Platform.OS === "ios" ? "padding" : "height"} 
            style={[localStyles.mainPanel, { backgroundColor: theme.background }]}
          >
            <ScrollView contentContainerStyle={localStyles.mainPanelScroll} keyboardShouldPersistTaps="handled">

              {/* Form Section */}
              <View style={localStyles.formSection}>
                <Text style={[localStyles.formHeading, { color: theme.text }]}>Connexion</Text>
                <Text style={[localStyles.formHint, { color: theme.muted }]}>Entrez vos identifiants pour accéder à votre espace.</Text>
                <View style={localStyles.inputGroup}>
                  <Text style={[localStyles.labelText, { color: theme.text }]}>Email professionnel</Text>
                  <TextInput
                    autoCapitalize="none"
                    autoCorrect={false}
                    onChangeText={setLoginEmail}
                    placeholder="prenom.nom@ydays.company"
                    style={[localStyles.premiumInput, { borderColor: theme.line, color: theme.text, backgroundColor: theme.card }]}
                    placeholderTextColor={theme.muted}
                    value={loginEmail}
                  />
                </View>

                <View style={localStyles.inputGroup}>
                  <Text style={[localStyles.labelText, { color: theme.text }]}>Mot de passe</Text>
                  <View style={[localStyles.premiumInputContainer, { borderColor: theme.line, backgroundColor: theme.card }]}>
                    <TextInput
                      autoCapitalize="none"
                      autoCorrect={false}
                      onChangeText={setLoginPassword}
                      placeholder="Mot de passe"
                      secureTextEntry={!showPassword}
                      style={[localStyles.premiumInputInner, { color: theme.text }]}
                      placeholderTextColor={theme.muted}
                      value={loginPassword}
                    />
                    <Pressable onPress={() => setShowPassword(!showPassword)} style={{ padding: 12 }}>
                      <Feather name={showPassword ? "eye" : "eye-off"} size={20} color={theme.muted} />
                    </Pressable>
                  </View>
                </View>

                {authError ? <Text style={styles.errorText}>{authError}</Text> : null}

                <View style={localStyles.rowBetween}>
                  <Pressable onPress={() => setRememberMe(!rememberMe)} style={localStyles.inlineToggle}>
                    <Feather name={rememberMe ? "check-square" : "square"} size={20} color={theme.emerald} />
                    <Text style={[localStyles.bodyStrong, { color: theme.text }]}>Se souvenir de moi</Text>
                  </Pressable>
                  <Pressable onPress={() => setAuthStep("forgot-password")}>
                    <Text style={[localStyles.linkText, { color: theme.sky }]}>Mot de passe oublié ?</Text>
                  </Pressable>
                </View>
              </View>

              {/* Actions Section */}
              <View style={localStyles.actionsSection}>
                <PrimaryButton
                  icon="log-in"
                  label={isLoading ? "Connexion en cours..." : roleDetails.cta}
                  onPress={handleSignIn}
                  ui={ui}
                />
              </View>

            </ScrollView>
          </KeyboardAvoidingView>
        </>
      )}

      {/* Forgot Password Step */}
      {authStep === "forgot-password" && (
        <SafeAreaView style={styles.authSafeArea}>
          <View style={styles.authShell}>
            <View style={styles.authCard}>
              <Text style={styles.authCardTitle}>Réinitialiser le mot de passe</Text>
              <Text style={styles.authCardText}>Entrez votre adresse email et votre nouveau mot de passe.</Text>
              
              <View style={{ marginTop: 20, gap: 16 }}>
                <View>
                  <Text style={[localStyles.labelText, { color: theme.text }]}>Adresse email</Text>
                  <TextInput
                    autoCapitalize="none"
                    autoCorrect={false}
                    onChangeText={setLoginEmail}
                    placeholder="prenom.nom@ydays.company"
                    style={[localStyles.premiumInput, { borderColor: theme.line, color: theme.text, backgroundColor: theme.card }]}
                    placeholderTextColor={theme.muted}
                    value={loginEmail}
                  />
                </View>
                
                <View>
                  <Text style={[localStyles.labelText, { color: theme.text }]}>Nouveau mot de passe</Text>
                  <TextInput
                    autoCapitalize="none"
                    autoCorrect={false}
                    onChangeText={setLoginPassword}
                    placeholder="Nouveau mot de passe"
                    secureTextEntry={true}
                    style={[localStyles.premiumInput, { borderColor: theme.line, color: theme.text, backgroundColor: theme.card }]}
                    placeholderTextColor={theme.muted}
                    value={loginPassword}
                  />
                </View>
                
                {authError ? <Text style={styles.errorText}>{authError}</Text> : null}

                <View style={{ marginTop: 8 }}>
                  <PrimaryButton 
                    icon="key" 
                    label={isLoading ? "Chargement..." : "Modifier le mot de passe"} 
                    onPress={async () => {
                      if (!loginEmail || !loginPassword) {
                        setAuthError("Veuillez remplir tous les champs.");
                        return;
                      }
                      setIsLoading(true);
                      setAuthError("");
                      try {
                        const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ email: loginEmail, new_password: loginPassword })
                        });
                        const data = await response.json();
                        if (response.ok) {
                          triggerFeedback("Mot de passe réinitialisé");
                          setAuthStep("login");
                        } else {
                          setAuthError(data.detail || "Erreur lors de la réinitialisation");
                        }
                      } catch (e: any) {
                        setAuthError("Erreur réseau");
                      } finally {
                        setIsLoading(false);
                      }
                    }} 
                    ui={ui} 
                  />
                  <View style={{ height: 12 }} />
                  <SecondaryButton icon="arrow-left" label="Retour à la connexion" onPress={() => setAuthStep("login")} ui={ui} />
                </View>
              </View>
            </View>
          </View>
        </SafeAreaView>
      )}

      {/* OTP and First-Login steps */}
      {(authStep === "otp" || authStep === "first-login") && (
        <SafeAreaView style={styles.authSafeArea}>
          <View style={styles.authShell}>
            {authStep === "otp" && (
              <View style={styles.authCard}>
                <Text style={styles.authCardTitle}>Vérification sécurisée</Text>
                <Text style={styles.authCardText}>Saisissez le code envoyé sur votre email professionnel. Nouveau code disponible dans 00:42.</Text>
                <View style={styles.otpRow}>
                  {["2", "0", "2", "6"].map((digit, index) => (
                    <View key={`${digit}-${index}`} style={styles.otpCell}>
                      <Text style={styles.otpDigit}>{digit}</Text>
                    </View>
                  ))}
                </View>
                <PrimaryButton icon="shield" label="Verifier le code" onPress={() => setAuthStep("first-login")} ui={ui} />
                <SecondaryButton icon="refresh-cw" label="Renvoyer le code" onPress={() => triggerFeedback("Code renvoye")} ui={ui} />
              </View>
            )}

            {authStep === "first-login" && (
              <View style={styles.authCard}>
                <Text style={styles.authCardTitle}>{"Connexion"}</Text>
                <Text style={styles.authCardText}>Votre profil RH a été pré-rempli. Vérifiez les informations avant d'activer votre espace collaborateur.</Text>
                {sessionProfile && <ProfileSummary sessionProfile={sessionProfile} ui={ui} />}
                <View style={styles.validationList}>
                  {["Identite confirmee", "Poste et departement verifies", "Permissions IA affichees"].map((item) => (
                    <View key={item} style={styles.checkRow}>
                      <Feather name="check-circle" size={16} color={theme.emerald} />
                      <Text style={styles.bodyText}>{item}</Text>
                    </View>
                  ))}
                </View>
                <PrimaryButton icon="check" label="Valider mon profil" onPress={() => setAuthStep("app")} ui={ui} />
              </View>
            )}
          </View>
        </SafeAreaView>
      )}
    </View>
  );
}

const localStyles = StyleSheet.create({
  fullScreenContainer: {
    flex: 1,
    backgroundColor: "#060C1A",
  },
  headerSection: {
    height: height * 0.30,
    justifyContent: "flex-end",
    paddingBottom: 32,
  },
  headerInner: {
    flex: 1,
    justifyContent: "flex-end",
    alignItems: "center",
  },
  brandCenter: {
    alignItems: "center",
    gap: 10,
  },
  logoOrbLarge: {
    width: 56,
    height: 56,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.45,
    shadowRadius: 20,
    elevation: 10,
  },
  logoTitle: {
    color: "#ffffff",
    fontSize: 28,
    fontWeight: "900",
    letterSpacing: 1.5,
  },
  brandPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginTop: 2,
  },
  brandPillText: {
    color: "rgba(255,255,255,0.65)",
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.3,
  },
  mainPanel: {
    flex: 1,
    marginTop: -40,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    paddingHorizontal: 24,
    paddingTop: 36,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -5 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 10,
  },
  mainPanelScroll: {
    flex: 1,
  },
  formSection: {
    marginTop: 10,
  },
  inputGroup: {
    marginBottom: 20,
  },
  labelText: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  premiumInput: {
    borderWidth: 1,
    borderRadius: 16,
    height: 56,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  premiumInputContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 16,
    height: 56,
  },
  premiumInputInner: {
    flex: 1,
    paddingHorizontal: 16,
    fontSize: 16,
    height: "100%",
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 4,
  },
  inlineToggle: {
    flexDirection: "row",
    alignItems: "center",
  },
  bodyStrong: {
    fontSize: 14,
    fontWeight: "600",
    marginLeft: 8,
  },
  linkText: {
    fontSize: 14,
    fontWeight: "600",
  },
  actionsSection: {
    marginTop: 28,
    gap: 12,
  },
  formHeading: {
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 6,
  },
  formHint: {
    fontSize: 13,
    marginBottom: 20,
  },
});
