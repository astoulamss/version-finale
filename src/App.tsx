import React, { useState, useEffect, useRef } from "react";
import { View, KeyboardAvoidingView, Platform, Pressable, Text, Modal, StyleSheet } from "react-native";
import * as Notifications from "expo-notifications";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { Feather } from "@expo/vector-icons";

// React Navigation
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

// Contexts
import { LanguageProvider, SupportedLanguage, useLanguage } from "./contexts/LanguageContext";
import { ThemeProvider, useUi } from "./contexts/ThemeContext";
import { FeedbackProvider, useFeedback } from "./contexts/FeedbackContext";

// Types
import { ViewId, EmployeeProfile, OnboardingTask, RecentDocument, Ui, ChatMessage, HrNotification, AuthStep } from "./types";

// Services & Helpers
import { chatbotService } from "./services/chatbot.service";
import { isRhRole, isManagerRole, isAdminRole } from "./lib/auth";
import { fetchMyNotifications, markNotificationRead, markAllNotificationsRead, registerExpoPushToken, unregisterExpoPushToken } from "./services/dashboard.service";

// Components
import { MyCustomTabBar } from "./components/MyCustomTabBar";
import { ScreenWrapper } from "./components/ScreenWrapper";
import { AppHeader } from "./components/AppHeader";

// Screens
import { AuthFlow } from "./screens/AuthFlow";
import { HomeScreen } from "./screens/HomeScreen";
import { AbsencesScreen } from "./screens/AbsencesScreen";
import { AssistantScreen } from "./screens/AssistantScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { OnboardingScreen } from "./screens/OnboardingScreen";
import { OffboardingScreen } from "./screens/OffboardingScreen";
import { TrainingsScreen } from "./screens/TrainingsScreen";
import { DocumentsScreen } from "./screens/DocumentsScreen";
import { ContractScreen } from "./screens/ContractScreen";
import { NotificationsScreen } from "./screens/NotificationsScreen";
import { RhHubScreen } from "./screens/RhHubScreen";
import { AnnouncementsScreen } from "./screens/AnnouncementsScreen";
import { HrContractsScreen } from "./screens/HrContractsScreen";
import { HrTrainingsScreen } from "./screens/HrTrainingsScreen";
import { RequestsRhView } from "./screens/RhScreens";
import { HrAnalyticsScreen } from "./screens/HrAnalyticsScreen";

import { LeaveScreen, PayrollScreen, RequestsScreen, MobilityScreen, TicketsScreen, SurveysScreen, TimesheetScreen } from "./screens/EmployeeScreens";
import { ManagerTeamScreen, ManagerTasksScreen, ManagerOffboardingScreen, ManagerOnboardingScreen, ManagerHubScreen } from "./screens/ManagerScreens";
import { ManagerLeavesScreen } from "./screens/ManagerLeavesScreen";
import { ManagerAbsencesScreen } from "./screens/ManagerAbsencesScreen";
import { AdminDashboardScreen, AdminAccountsScreen, AdminAlertsScreen, AdminLogsScreen, AdminProfileScreen } from "./screens/AdminScreens";
import { QvtDashboardScreen } from "./screens/QvtScreens";
import { DirectionDashboardScreen } from "./screens/DirectionScreens";
import { HrTeamScreen } from "./screens/HrTeamScreen";

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Show push alerts even when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

async function registerForPushNotificationsAsync(): Promise<string | null> {
  try {
    // expo-notifications types don't expose 'granted' due to a broken re-export from 'expo', but it exists at runtime
    const perms = await Notifications.getPermissionsAsync();
    let isGranted: boolean = (perms as any).granted ?? false;
    if (!isGranted) {
      const req = await Notifications.requestPermissionsAsync();
      isGranted = (req as any).granted ?? false;
    }
    if (!isGranted) return null;

    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("default", {
        name: "YDAYS Notifications",
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: "#1f3b42",
      });
    }

    const tokenData = await Notifications.getExpoPushTokenAsync();
    return tokenData.data;
  } catch {
    return null;
  }
}

// Inner Navigator definition
function MainTabs({ navigation, ui, sessionProfile, chatInput, setChatInput, messages, setMessages, conversationId, setConversationId, handleSendAi, aiTyping, biometricEnabled, setBiometricEnabled, setThemeMode, language, setLanguage, languageOpen, setLanguageOpen, notificationEnabled, setNotificationEnabled, setShowLogout, triggerFeedback }: any) {
  const isRh = isRhRole(sessionProfile?.roleId ?? sessionProfile?.role);
  const isManager = isManagerRole(sessionProfile?.roleId ?? sessionProfile?.role);
  const isAdmin = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role);

  return (
    <Tab.Navigator
      tabBar={(props) => <MyCustomTabBar {...props} ui={ui} />}
      screenOptions={{ headerShown: false }}
    >
      {isAdmin ? (
        <>
          <Tab.Screen name="admin_dashboard">
            {() => (
              <ScreenWrapper ui={ui}>
                <AdminDashboardScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => navigation.navigate(dest)} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="assistant">
            {() => (
              <ScreenWrapper isScrollable={false} ui={ui}>
                <AssistantScreen 
                  aiTyping={aiTyping}
                  chatInput={chatInput}
                  messages={messages}
                  activeConversationId={conversationId}
                  onInputChange={setChatInput}
                  onSend={handleSendAi}
                  onNewConversation={() => {
                    setConversationId(null);
                    setMessages([]);
                  }}
                  onSelectConversation={async (id: number) => {
                    setConversationId(id);
                    try {
                      const details = await chatbotService.getConversationDetails(id);
                      if (details.messages) {
                        const mapped = details.messages.map((m: any) => ({
                          id: m.id.toString(),
                          role: m.sender === 'user' ? 'employee' : 'ai',
                          text: m.message,
                          time: new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                        }));
                        setMessages(mapped);
                      } else {
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to fetch conversation details", e);
                    }
                  }}
                  onDeleteConversation={async (id: number) => {
                    try {
                      await chatbotService.deleteConversation(id);
                      if (conversationId === id) {
                        setConversationId(null);
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to delete conversation", e);
                    }
                  }}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                  sessionProfile={sessionProfile}
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="admin_accounts">
            {() => (
              <ScreenWrapper ui={ui}>
                <AdminAccountsScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="admin_alerts">
            {() => (
              <ScreenWrapper ui={ui}>
                <AdminAlertsScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="admin_logs">
            {() => (
              <ScreenWrapper ui={ui}>
                <AdminLogsScreen sessionProfile={sessionProfile} ui={ui} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="admin_profile">
            {() => (
              <ScreenWrapper ui={ui}>
                <AdminProfileScreen sessionProfile={sessionProfile} setAuthStep={() => setShowLogout(true)} ui={ui} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
        </>
      ) : isRh ? (
        <>
          <Tab.Screen name="home">
            {() => (
              <ScreenWrapper ui={ui}>
                <HomeScreen 
                  onboardingProgress={50}
                  onNavigate={(dest: any) => navigation.navigate(dest)}
                  onAskAi={(prompt: string) => {
                    setChatInput(prompt);
                    navigation.navigate("assistant");
                  }}
                  onStartDocument={() => triggerFeedback("Document started")}
                  onSelectDocumentDetails={() => triggerFeedback("Doc details")}
                  onNotificationClick={() => triggerFeedback("Notification")}
                  recentNotifications={[]}
                  sessionProfile={sessionProfile} 
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="assistant">
            {() => (
              <ScreenWrapper isScrollable={false} ui={ui}>
                <AssistantScreen 
                  aiTyping={aiTyping}
                  chatInput={chatInput}
                  messages={messages}
                  activeConversationId={conversationId}
                  onInputChange={setChatInput}
                  onSend={handleSendAi}
                  onNewConversation={() => {
                    setConversationId(null);
                    setMessages([]);
                  }}
                  onSelectConversation={async (id: number) => {
                    setConversationId(id);
                    try {
                      const details = await chatbotService.getConversationDetails(id);
                      if (details.messages) {
                        const mapped = details.messages.map((m: any) => ({
                          id: m.id.toString(),
                          role: m.sender === 'user' ? 'employee' : 'ai',
                          text: m.message,
                          time: new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                        }));
                        setMessages(mapped);
                      } else {
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to fetch conversation details", e);
                    }
                  }}
                  onDeleteConversation={async (id: number) => {
                    try {
                      await chatbotService.deleteConversation(id);
                      if (conversationId === id) {
                        setConversationId(null);
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to delete conversation", e);
                    }
                  }}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                  sessionProfile={sessionProfile}
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="indicateurs">
            {() => (
              <ScreenWrapper ui={ui}>
                <HrAnalyticsScreen sessionProfile={sessionProfile!} ui={ui} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="rh_hub">
            {() => (
              <ScreenWrapper isScrollable={false} ui={ui}>
                <RhHubScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => navigation.navigate(dest)} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="validations">
            {() => (
              <ScreenWrapper ui={ui}>
                <RequestsRhView sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="profile">
            {() => (
              <ScreenWrapper ui={ui}>
                <ProfileScreen 
                  biometricEnabled={biometricEnabled}
                  isDark={!!ui.isDark}
                  language={language}
                  languageOpen={languageOpen}
                  notificationEnabled={notificationEnabled}
                  onEditProfile={() => triggerFeedback("Edit Profile")}
                  onOpenPrivacy={() => triggerFeedback("Privacy")}
                  onLogout={() => setShowLogout(true)}
                  onNavigate={(dest: any) => navigation.navigate(dest)}
                  sessionProfile={sessionProfile} 
                  setBiometricEnabled={setBiometricEnabled}
                  setIsDark={(val) => setThemeMode(val ? "dark" : "light")}
                  setLanguage={setLanguage}
                  setLanguageOpen={setLanguageOpen}
                  setNotificationEnabled={setNotificationEnabled}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
        </>
      ) : isManager ? (
        <>
          <Tab.Screen name="home">
            {() => (
              <ScreenWrapper ui={ui}>
                <HomeScreen 
                  onboardingProgress={50}
                  onNavigate={(dest: any) => navigation.navigate(dest)}
                  onAskAi={(prompt: string) => {
                    setChatInput(prompt);
                    navigation.navigate("assistant");
                  }}
                  onStartDocument={() => triggerFeedback("Document started")}
                  onSelectDocumentDetails={() => triggerFeedback("Doc details")}
                  onNotificationClick={() => triggerFeedback("Notification")}
                  recentNotifications={[]}
                  sessionProfile={sessionProfile} 
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="assistant">
            {() => (
              <ScreenWrapper isScrollable={false} ui={ui}>
                <AssistantScreen 
                  aiTyping={aiTyping}
                  chatInput={chatInput}
                  messages={messages}
                  activeConversationId={conversationId}
                  onInputChange={setChatInput}
                  onSend={handleSendAi}
                  onNewConversation={() => {
                    setConversationId(null);
                    setMessages([]);
                  }}
                  onSelectConversation={async (id: number) => {
                    setConversationId(id);
                    try {
                      const details = await chatbotService.getConversationDetails(id);
                      if (details.messages) {
                        const mapped = details.messages.map((m: any) => ({
                          id: m.id.toString(),
                          role: m.sender === 'user' ? 'employee' : 'ai',
                          text: m.message,
                          time: new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                        }));
                        setMessages(mapped);
                      } else {
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to fetch conversation details", e);
                    }
                  }}
                  onDeleteConversation={async (id: number) => {
                    try {
                      await chatbotService.deleteConversation(id);
                      if (conversationId === id) {
                        setConversationId(null);
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to delete conversation", e);
                    }
                  }}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                  sessionProfile={sessionProfile}
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="team">
            {() => (
              <ScreenWrapper ui={ui}>
                <ManagerTeamScreen sessionProfile={sessionProfile} ui={ui} onNavigate={(dest: any) => navigation.navigate(dest)} onSelectEmployee={() => {}} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="manager_hub">
            {() => (
              <ScreenWrapper ui={ui}>
                <ManagerHubScreen sessionProfile={sessionProfile} ui={ui} onNavigate={(dest: any) => navigation.navigate(dest)} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="profile">
            {() => (
              <ScreenWrapper ui={ui}>
                <ProfileScreen 
                  biometricEnabled={biometricEnabled}
                  isDark={!!ui.isDark}
                  language={language}
                  languageOpen={languageOpen}
                  notificationEnabled={notificationEnabled}
                  onEditProfile={() => triggerFeedback("Edit Profile")}
                  onOpenPrivacy={() => triggerFeedback("Privacy")}
                  onLogout={() => setShowLogout(true)}
                  onNavigate={(dest: any) => navigation.navigate(dest)}
                  sessionProfile={sessionProfile} 
                  setBiometricEnabled={setBiometricEnabled}
                  setIsDark={(val) => setThemeMode(val ? "dark" : "light")}
                  setLanguage={setLanguage}
                  setLanguageOpen={setLanguageOpen}
                  setNotificationEnabled={setNotificationEnabled}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
        </>
      ) : (
        <>
          <Tab.Screen name="home">
            {() => (
              <ScreenWrapper ui={ui}>
                <HomeScreen 
                  onboardingProgress={50}
                  onNavigate={(dest: any) => navigation.navigate(dest)}
                  onAskAi={(prompt: string) => {
                    setChatInput(prompt);
                    navigation.navigate("assistant");
                  }}
                  onStartDocument={() => triggerFeedback("Document started")}
                  onSelectDocumentDetails={() => triggerFeedback("Doc details")}
                  onNotificationClick={() => triggerFeedback("Notification")}
                  recentNotifications={[]}
                  sessionProfile={sessionProfile} 
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="rh_hub">
            {() => (
              <ScreenWrapper isScrollable={false} ui={ui}>
                <RhHubScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => navigation.navigate(dest)} />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="assistant">
            {() => (
              <ScreenWrapper isScrollable={false} ui={ui}>
                <AssistantScreen 
                  aiTyping={aiTyping}
                  chatInput={chatInput}
                  messages={messages}
                  activeConversationId={conversationId}
                  onInputChange={setChatInput}
                  onSend={handleSendAi}
                  onNewConversation={() => {
                    setConversationId(null);
                    setMessages([]);
                  }}
                  onSelectConversation={async (id: number) => {
                    setConversationId(id);
                    try {
                      const details = await chatbotService.getConversationDetails(id);
                      if (details.messages) {
                        const mapped = details.messages.map((m: any) => ({
                          id: m.id.toString(),
                          role: m.sender === 'user' ? 'employee' : 'ai',
                          text: m.message,
                          time: new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                        }));
                        setMessages(mapped);
                      } else {
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to fetch conversation details", e);
                    }
                  }}
                  onDeleteConversation={async (id: number) => {
                    try {
                      await chatbotService.deleteConversation(id);
                      if (conversationId === id) {
                        setConversationId(null);
                        setMessages([]);
                      }
                    } catch (e) {
                      console.warn("Failed to delete conversation", e);
                    }
                  }}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                  sessionProfile={sessionProfile}
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
          <Tab.Screen name="profile">
            {() => (
              <ScreenWrapper ui={ui}>
                <ProfileScreen 
                  biometricEnabled={biometricEnabled}
                  isDark={!!ui.isDark}
                  language={language}
                  languageOpen={languageOpen}
                  notificationEnabled={notificationEnabled}
                  onEditProfile={() => triggerFeedback("Edit Profile")}
                  onOpenPrivacy={() => triggerFeedback("Privacy")}
                  onLogout={() => setShowLogout(true)}
                  onNavigate={(dest: any) => navigation.navigate(dest)}
                  sessionProfile={sessionProfile} 
                  setBiometricEnabled={setBiometricEnabled}
                  setIsDark={(val) => setThemeMode(val ? "dark" : "light")}
                  setLanguage={setLanguage}
                  setLanguageOpen={setLanguageOpen}
                  setNotificationEnabled={setNotificationEnabled}
                  triggerFeedback={triggerFeedback} 
                  ui={ui} 
                />
              </ScreenWrapper>
            )}
          </Tab.Screen>
        </>
      )}
    </Tab.Navigator>
  );
}

// AppNavigator containing NavigationContainer, unified header, outer stack and footer modal
function AppNavigator({ sessionProfile, setAuthStep }: any) {
  const { ui, setThemeMode } = useUi();
  const { triggerFeedback } = useFeedback();

  // Modal States
  const [selectedTask, setSelectedTask] = useState<OnboardingTask | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<RecentDocument | null>(null);
  const [showLogout, setShowLogout] = useState(false);

  // Push notification state
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const notifListenerRef = useRef<any>(null);
  const responseListenerRef = useRef<any>(null);

  // Assistant State
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [aiTyping, setAiTyping] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);

  const handleSendAi = async (suggestion?: string) => {
    const prompt = typeof suggestion === 'string' ? suggestion : chatInput;
    if (!prompt) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "employee", text: prompt, time: "Maintenant" }]);
    if (typeof suggestion !== 'string') setChatInput("");
    setAiTyping(true);
    
    try {
      let currentConvId = conversationId;
      if (!currentConvId) {
        console.log("=== API CHATBOT LOG : Création conversation ===");
        const conv = await chatbotService.createConversation(prompt.substring(0, 30));
        currentConvId = conv.id;
        setConversationId(currentConvId);
      }
      
      const response = await chatbotService.sendMessage(currentConvId!, prompt);
      const botResponse = Array.isArray(response) 
        ? response.find(r => r.sender === "bot") || response[response.length - 1]
        : response;
      
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: "ai", 
        text: botResponse.message || botResponse.text || "Réponse reçue.", 
        time: "Maintenant"
      }]);
    } catch (err: any) {
      let errorMessage = "Je ne suis pas disponible";
      if (err.message && err.message.toLowerCase().includes("timeout")) {
        errorMessage = "Le serveur a mis trop de temps à répondre.";
      } else if (err.message && err.message.toLowerCase().includes("network")) {
        errorMessage = "Impossible de joindre le serveur.";
      } else if (err.response) {
        errorMessage = `Le serveur a renvoyé une erreur ${err.response.status}.`;
      }
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: "system", 
        text: `Désolé, une erreur est survenue: ${errorMessage}`, 
        time: "Maintenant"
      }]);
    } finally {
      setAiTyping(false);
    }
  };

  // Profile State
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const { language, setLanguage } = useLanguage();
  const [languageOpen, setLanguageOpen] = useState(false);
  const [notificationEnabled, setNotificationEnabled] = useState(true);

  // Notifications State
  const [notificationsFilter, setNotificationsFilter] = useState("all");
  const [notificationsItems, setNotificationsItems] = useState<HrNotification[]>([]);

  useEffect(() => {
    if (sessionProfile) {
      const loadNotifications = async () => {
        try {
          const data = await fetchMyNotifications();
          const mapped: HrNotification[] = data.map((n: any) => ({
            id: String(n.id),
            title: "Alerte RH",
            body: n.message || "",
            category: (n.message || "").toLowerCase().includes("document") || (n.message || "").toLowerCase().includes("contrat")
              ? "Documents"
              : (isAdminRole(sessionProfile.roleId ?? sessionProfile.role) ? "Système"
                 : isRhRole(sessionProfile.roleId ?? sessionProfile.role) ? "RH"
                 : isManagerRole(sessionProfile.roleId ?? sessionProfile.role) ? "Équipe" 
                 : "Alertes"),
            priority: "critical",
            time: new Date(n.created_at).toLocaleDateString(),
            unread: !n.is_read
          }));
          setNotificationsItems(mapped);
          const unread = data.filter((n: any) => !n.is_read).length;
          Notifications.setBadgeCountAsync(unread).catch(() => {});
        } catch (e) {
          console.warn("Erreur lors du chargement des notifications:", e);
        }
      };
      loadNotifications();
      const interval = setInterval(loadNotifications, 15000);
      return () => clearInterval(interval);
    }
  }, [sessionProfile?.role, sessionProfile?.email]);

  // Push notification registration + listeners
  useEffect(() => {
    if (!sessionProfile) return;

    registerForPushNotificationsAsync().then(async (token) => {
      if (token) {
        setExpoPushToken(token);
        try {
          await registerExpoPushToken(token, Platform.OS === "ios" ? "ios" : "android");
        } catch (e) {
          console.warn("[Push] Impossible d'enregistrer le token:", e);
        }
      }
    });

    notifListenerRef.current = Notifications.addNotificationReceivedListener(() => {
      fetchMyNotifications().then((data) => {
        const unread = data.filter((n: any) => !n.is_read).length;
        Notifications.setBadgeCountAsync(unread).catch(() => {});
      }).catch(() => {});
    });

    responseListenerRef.current = Notifications.addNotificationResponseReceivedListener(() => {
      navRef.current?.navigate("notifications");
    });

    return () => {
      notifListenerRef.current?.remove();
      responseListenerRef.current?.remove();
    };
  }, [sessionProfile?.id]);

  const notificationsCount = notificationsItems.filter(n => n.unread).length;

  const handleMarkRead = (id?: string) => {
    if (id) {
      setNotificationsItems(prev => prev.map(n => n.id === id ? { ...n, unread: false } : n));
      markNotificationRead(id).catch(e => console.warn("Erreur lors de la lecture d'une notification:", e));
    } else {
      setNotificationsItems(prev => prev.map(n => ({ ...n, unread: false })));
      markAllNotificationsRead().catch(e => console.warn("Erreur lors de la lecture globale des notifications:", e));
    }
  };

  const handleLogout = async () => {
    if (expoPushToken) {
      try { await unregisterExpoPushToken(expoPushToken); } catch {}
    }
    Notifications.setBadgeCountAsync(0).catch(() => {});
    setShowLogout(false);
    setAuthStep("login");
  };

  const navRef = React.useRef<any>(null);
  const [currentHeader, setCurrentHeader] = useState<any>(null);

  // Sync custom header with navigation state
  const handleStateChange = () => {
    if (navRef.current) {
      setCurrentHeader(
        <AppHeader 
          sessionProfile={sessionProfile} 
          notificationsCount={notificationsCount} 
          ui={ui} 
          navigation={navRef.current} 
        />
      );
    }
  };

  // Initialize header when reference is ready
  useEffect(() => {
    if (navRef.current) {
      handleStateChange();
    }
  }, [notificationsCount, ui.isDark, sessionProfile]);

  return (
    <NavigationContainer ref={navRef} onStateChange={handleStateChange}>
      <SafeAreaView style={[styles.flex1, { backgroundColor: ui.theme.card }]}>
        <StatusBar style={ui.isDark ? "light" : "dark"} />
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={[styles.flex1, { backgroundColor: ui.theme.background }]}>
          {currentHeader}
          <View style={styles.flex1}>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
              <Stack.Screen name="Main">
                {(props: any) => (
                  <MainTabs 
                    {...props} 
                    ui={ui} 
                    sessionProfile={sessionProfile}
                    chatInput={chatInput}
                    setChatInput={setChatInput}
                    messages={messages}
                    setMessages={setMessages}
                    conversationId={conversationId}
                    setConversationId={setConversationId}
                    handleSendAi={handleSendAi}
                    aiTyping={aiTyping}
                    biometricEnabled={biometricEnabled}
                    setBiometricEnabled={setBiometricEnabled}
                    setThemeMode={setThemeMode}
                    language={language}
                    setLanguage={setLanguage}
                    languageOpen={languageOpen}
                    setLanguageOpen={setLanguageOpen}
                    notificationEnabled={notificationEnabled}
                    setNotificationEnabled={setNotificationEnabled}
                    setShowLogout={setShowLogout}
                    triggerFeedback={triggerFeedback}
                  />
                )}
              </Stack.Screen>

              <Stack.Screen name="onboarding">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <OnboardingScreen onSelectTask={setSelectedTask} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="offboarding">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <OffboardingScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="employee_offboarding">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <OffboardingScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="absences">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <AbsencesScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="leave">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <LeaveScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="documents">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <DocumentsScreen triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="employee_trainings">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <TrainingsScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="timesheet">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <TimesheetScreen triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="operations">
                {(props: any) => (
                  <ScreenWrapper isScrollable={false} ui={ui}>
                    <RhHubScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="announcements">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <AnnouncementsScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="hr_contracts">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <HrContractsScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="hr_trainings">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <HrTrainingsScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="hr_team">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <HrTeamScreen ui={ui} triggerFeedback={triggerFeedback} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="qvt_dashboard">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <QvtDashboardScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="direction_dashboard">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <DirectionDashboardScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="manager_leaves">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <ManagerLeavesScreen sessionProfile={sessionProfile} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="manager_absences">
                {(props: any) => (
                  <ScreenWrapper ui={ui}>
                    <ManagerAbsencesScreen sessionProfile={sessionProfile} ui={ui} onNavigate={(dest: any) => props.navigation.navigate(dest)} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="alerts">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <ManagerTasksScreen sessionProfile={sessionProfile} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="manager_offboarding">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <ManagerOffboardingScreen ui={ui} sessionProfile={sessionProfile} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="manager_onboarding">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <ManagerOnboardingScreen sessionProfile={sessionProfile} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="contract">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <ContractScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="notifications">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <NotificationsScreen 
                      filter={notificationsFilter} 
                      notificationsState={notificationsItems} 
                      onFilterChange={setNotificationsFilter} 
                      onNotificationClick={(n) => { handleMarkRead(n.id); triggerFeedback("Notification ouverte"); }} 
                      onMarkRead={handleMarkRead} 
                      sessionProfile={sessionProfile} 
                      ui={ui} 
                    />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="requests">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <RequestsScreen triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="payroll">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <PayrollScreen sessionProfile={sessionProfile} triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="mobility">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <MobilityScreen triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="tickets">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <TicketsScreen triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>

              <Stack.Screen name="surveys">
                {() => (
                  <ScreenWrapper ui={ui}>
                    <SurveysScreen triggerFeedback={triggerFeedback} ui={ui} />
                  </ScreenWrapper>
                )}
              </Stack.Screen>
            </Stack.Navigator>
          </View>
        </KeyboardAvoidingView>

        {/* --- MODALS --- */}
        <Modal visible={!!selectedTask} transparent animationType="slide" onRequestClose={() => setSelectedTask(null)}>
          <View style={[styles.modalBackdrop, styles.modalBottomAlign]}>
            <View style={[styles.modalBottomCard, { backgroundColor: ui.theme.card }]}>
              <Text style={[styles.modalTitle, { color: ui.theme.text }]}>{selectedTask?.title}</Text>
              <Text style={[styles.modalDescription, { color: ui.theme.muted }]}>{selectedTask?.description}</Text>
              
              <Pressable 
                onPress={() => { setSelectedTask(null); triggerFeedback("Tâche validée avec succès"); }} 
                style={({ pressed }) => [
                  styles.modalButton, 
                  styles.submitButton, 
                  { backgroundColor: ui.theme.emerald },
                  pressed && { opacity: 0.8 }
                ]}
              >
                <Text style={[styles.buttonText, { color: '#fff' }]}>Marquer comme terminé</Text>
              </Pressable>
              
              <Pressable 
                onPress={() => setSelectedTask(null)} 
                style={({ pressed }) => [
                  styles.closePressable,
                  pressed && { opacity: 0.6 }
                ]}
              >
                <Text style={[styles.closeButtonText, { color: ui.theme.muted }]}>Fermer</Text>
              </Pressable>
            </View>
          </View>
        </Modal>

        <Modal visible={!!selectedDoc} transparent animationType="slide" onRequestClose={() => setSelectedDoc(null)}>
          <View style={[styles.modalBackdrop, styles.modalBottomAlign]}>
            <View style={[styles.modalBottomCard, { backgroundColor: ui.theme.card }]}>
              <View style={styles.docHeader}>
                <View style={[styles.docIconWrapper, { backgroundColor: ui.theme.skySoft }]}>
                  <Feather name="file-text" size={20} color={ui.theme.sky} />
                </View>
                <View>
                  <Text style={[styles.docTitle, { color: ui.theme.text }]}>{selectedDoc?.title}</Text>
                  <Text style={[styles.docCategory, { color: ui.theme.muted }]}>{selectedDoc?.category}</Text>
                </View>
              </View>
              
              <Pressable 
                onPress={() => { setSelectedDoc(null); triggerFeedback("Téléchargement démarré"); }} 
                style={({ pressed }) => [
                  styles.modalButton, 
                  styles.submitButton, 
                  { backgroundColor: ui.theme.sky },
                  pressed && { opacity: 0.8 }
                ]}
              >
                <Text style={[styles.buttonText, { color: '#fff' }]}>Télécharger le document</Text>
              </Pressable>
              
              <Pressable 
                onPress={() => setSelectedDoc(null)} 
                style={({ pressed }) => [
                  styles.closePressable,
                  pressed && { opacity: 0.6 }
                ]}
              >
                <Text style={[styles.closeButtonText, { color: ui.theme.muted }]}>Fermer</Text>
              </Pressable>
            </View>
          </View>
        </Modal>

        <Modal visible={showLogout} transparent animationType="fade" onRequestClose={() => setShowLogout(false)}>
          <View style={[styles.modalBackdrop, styles.modalCenterAlign]}>
            <View style={[styles.modalCenterCard, { backgroundColor: ui.theme.card }]}>
              <Feather name="log-out" size={40} color={ui.theme.rose} style={styles.logoutIcon} />
              <Text style={[styles.modalTitle, { color: ui.theme.text }]}>Déconnexion</Text>
              <Text style={[styles.logoutMessage, { color: ui.theme.muted }]}>Êtes-vous sûr de vouloir vous déconnecter de votre session ?</Text>
              
              <View style={styles.buttonRow}>
                <Pressable 
                  onPress={() => setShowLogout(false)} 
                  style={({ pressed }) => [
                    styles.modalButton, 
                    styles.cancelButton, 
                    { backgroundColor: ui.theme.surfaceAlt },
                    pressed && { opacity: 0.8 }
                  ]}
                >
                  <Text style={[styles.buttonText, { color: ui.theme.text }]}>Annuler</Text>
                </Pressable>
                <Pressable 
                  onPress={handleLogout}
                  style={({ pressed }) => [
                    styles.modalButton,
                    styles.confirmButton,
                    { backgroundColor: ui.theme.rose },
                    pressed && { opacity: 0.8 }
                  ]}
                >
                  <Text style={[styles.buttonText, { color: '#fff' }]}>Déconnexion</Text>
                </Pressable>
              </View>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </NavigationContainer>
  );
}

// Sub-app content wrapper that uses contexts
function AppContent() {
  const [authStep, setAuthStep] = useState<AuthStep>("login");
  const [sessionProfile, setSessionProfile] = useState<EmployeeProfile | null>(null);
  const [rememberMe, setRememberMe] = useState(false);
  const { ui } = useUi();
  const { triggerFeedback } = useFeedback();
  const { language } = useLanguage(); // Force app re-render on language change

  if (authStep !== "app" || !sessionProfile) {
    return (
      <AuthFlow
        authStep={authStep}
        rememberMe={rememberMe}
        sessionProfile={sessionProfile}
        setActiveView={() => {}} // Navigation handles active view
        setAuthStep={setAuthStep}
        setRememberMe={setRememberMe}
        setSessionProfile={setSessionProfile}
        triggerFeedback={triggerFeedback}
        ui={ui}
      />
    );
  }

  return <AppNavigator sessionProfile={sessionProfile} setAuthStep={setAuthStep} />;
}

// Export default wrapping with Providers
export default function App() {
  return (
    <SafeAreaProvider>
      <LanguageProvider>
        <ThemeProvider>
          <FeedbackProvider>
            <AppContent />
          </FeedbackProvider>
        </ThemeProvider>
      </LanguageProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  flex1: {
    flex: 1,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  modalBottomAlign: {
    justifyContent: 'flex-end',
  },
  modalCenterAlign: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalBottomCard: {
    padding: 24,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  modalCenterCard: {
    padding: 24,
    borderRadius: 20,
    width: '100%',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  modalDescription: {
    fontSize: 16,
    marginBottom: 24,
  },
  docHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  docIconWrapper: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  docTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  docCategory: {
    fontSize: 14,
  },
  logoutIcon: {
    marginBottom: 16,
  },
  logoutMessage: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
  },
  buttonRow: {
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-between',
  },
  modalButton: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButton: {
    marginBottom: 12,
  },
  cancelButton: {
    flex: 1,
    marginRight: 8,
  },
  confirmButton: {
    flex: 1,
    marginLeft: 8,
  },
  buttonText: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  closeButtonText: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  closePressable: {
    padding: 16,
    alignItems: 'center',
  },
});

