import React, { useMemo } from "react";
import { View, ScrollView } from "react-native";
import { Chip } from "../components/ui/Badge";
import { SectionHeader } from "../components/ui/SectionHeader";
import { EmptyState } from "../components/ui/EmptyState";
import { NotificationCard } from "../components/Shared";

import { Ui, HrNotification, EmployeeProfile } from "../types";
import { isAdminRole, isQvtRole, isManagerRole, isRhRole } from "../lib/auth";
const emptyStateExamples = { notifications: "Vous êtes à jour !" };

export function NotificationsScreen({
  filter,
  notificationsState,
  onFilterChange,
  onNotificationClick,
  onMarkRead,
  sessionProfile,
  ui,
}: {
  filter: string;
  notificationsState: HrNotification[];
  onFilterChange: (filter: string) => void;
  onNotificationClick: (notif: HrNotification) => void;
  onMarkRead: (id?: string) => void;
  sessionProfile: EmployeeProfile;
  ui: Ui;
}) {
  const role = sessionProfile.roleId ?? sessionProfile.role;

  const categories = useMemo(() => {
    if (isAdminRole(role)) return ["Tous", "Sécurité", "Système", "Comptes"];
    if (isQvtRole(role)) return ["Tous", "Santé", "Prévention", "Alertes"];
    if (isManagerRole(role)) return ["Tous", "Équipe", "Documents"];
    if (isRhRole(role)) return ["Tous", "RH", "Onboarding", "Documents"];
    
    return ["Tous", "Mes alertes", "Documents"];
  }, [role]);

  const activeFilter = useMemo(() => 
    categories.includes(filter) ? filter : "Tous"
  , [filter, categories]);

  const filtered = notificationsState?.filter((item) => activeFilter === "Tous" || item?.category === activeFilter) || [];
  const { styles } = ui;
  const hasUnread = useMemo(() => notificationsState?.some(n => n.unread), [notificationsState]);

  return (
    <View style={styles.stack}>
      <SectionHeader
        icon="bell"
        title="Centre de notifications"
        ui={ui}
      />
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.horizontalRail}>
          {categories?.map((category) => (
            <Chip active={category === activeFilter} key={category} label={category} onPress={() => onFilterChange(category)} ui={ui} />
          ))}
        </View>
      </ScrollView>

      {filtered.length === 0 ? (
        <EmptyState icon="bell-off" text={emptyStateExamples.notifications} title="Aucune notification" ui={ui} />
      ) : (
        filtered?.map((notification) => (
          <NotificationCard
            key={notification.id}
            notification={notification}
            onPress={() => onNotificationClick(notification)}
            onMarkRead={() => onMarkRead(notification.id)}
            ui={ui}
          />
        ))
      )}
    </View>
  );
}

