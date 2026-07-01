import React from "react";
import { View, Pressable, Text, StyleSheet, Image } from "react-native";
import { Feather } from "@expo/vector-icons";
import { NavigationProp } from "@react-navigation/native";
import { isAdminRole } from "../lib/auth";
import { Ui, EmployeeProfile } from "../types";
import { BackButton } from "./ui/BackButton";

interface AppHeaderProps {
  sessionProfile: EmployeeProfile | null;
  notificationsCount: number;
  onLogout?: () => void;
  ui: Ui;
  navigation: NavigationProp<any>;
}

export function AppHeader({ sessionProfile, notificationsCount, ui, navigation }: AppHeaderProps) {
  const canGoBack = navigation.canGoBack();
  const state = navigation.getState();
  const currentRouteName = state?.routes ? state.routes[state.routes.length - 1]?.name : '';
  const isDark = ui.isDark;

  const initials = `${sessionProfile?.firstName?.[0] ?? 'U'}${sessionProfile?.lastName?.[0] ?? 'S'}`;

  if (!canGoBack || currentRouteName === 'Main') {
    const isAdmin = isAdminRole(sessionProfile?.roleId ?? sessionProfile?.role ?? "");

    return (
      <View style={[
        styles.header,
        {
          backgroundColor: isDark ? 'rgba(6,12,26,0.97)' : 'rgba(248,250,255,0.97)',
          borderBottomColor: isDark ? 'rgba(59,130,246,0.14)' : 'rgba(37,99,235,0.10)',
        }
      ]}>
        <Pressable
          onPress={() => navigation.navigate(isAdmin ? "admin_profile" : "profile")}
          style={({ pressed }) => [styles.avatarRow, pressed && { opacity: 0.8 }]}
        >
          <View style={[styles.avatar, { backgroundColor: ui.theme.sky }]}>
            {sessionProfile?.photoUrl ? (
              <Image source={{ uri: sessionProfile.photoUrl }} style={styles.avatarImage} />
            ) : (
              <Text style={styles.avatarText}>{initials}</Text>
            )}
          </View>
          <View style={{ justifyContent: 'center' }}>
            <Text style={[styles.name, { color: ui.theme.text }]}>{sessionProfile?.firstName} {sessionProfile?.lastName}</Text>
          </View>
        </Pressable>

        <Pressable
          onPress={() => navigation.navigate("notifications")}
          style={({ pressed }) => [
            styles.bell,
            {
              backgroundColor: isDark ? 'rgba(59,130,246,0.12)' : ui.theme.skySoft,
              borderColor: isDark ? 'rgba(59,130,246,0.25)' : 'rgba(37,99,235,0.18)',
            },
            pressed && { opacity: 0.75 }
          ]}
        >
          <Feather name="bell" size={20} color={ui.theme.sky} />
          {notificationsCount > 0 && (
            <View style={[styles.badge, { backgroundColor: ui.theme.rose }]}>
              <Text style={styles.badgeText}>
                {notificationsCount > 9 ? '9+' : notificationsCount}
              </Text>
            </View>
          )}
        </Pressable>
      </View>
    );
  }

  return (
    <View style={[
      styles.backHeader,
      {
        backgroundColor: isDark ? 'rgba(6,12,26,0.97)' : 'rgba(248,250,255,0.97)',
        borderBottomColor: isDark ? 'rgba(59,130,246,0.14)' : 'rgba(37,99,235,0.10)',
      }
    ]}>
      <BackButton onPress={() => navigation.goBack()} ui={ui} />
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarImage: {
    width: 42,
    height: 42,
    borderRadius: 21,
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  greeting: {
    fontSize: 12,
    fontWeight: '500',
  },
  name: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  bell: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  badge: {
    position: 'absolute',
    top: -2,
    right: -2,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '800',
  },
  backHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  backTitle: {
    fontSize: 17,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
});
