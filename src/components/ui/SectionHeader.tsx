import React from "react";
import { View, Text, Pressable } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Ui, FeatherName } from "../../types";

export function SectionHeader({
  action,
  icon,
  onAction,
  title,
  ui,
}: {
  action?: string;
  icon: FeatherName;
  onAction?: () => void;
  title: string;
  ui: Ui;
}) {
  const { styles, theme } = ui;

  return (
    <View style={styles.sectionHeader}>
      <View style={styles.rowStart}>
        <View style={styles.sectionIcon}>
          <Feather name={icon} size={16} color={theme.sky} />
        </View>
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      {action && (
        <Pressable onPress={onAction} style={({ pressed }) => [pressed && { opacity: 0.7 }]}>
          <Text style={styles.linkText}>{action}</Text>
        </Pressable>
      )}
    </View>
  );
}
