import React from "react";
import { View, Text } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Ui, FeatherName } from "../../types";
import { Card } from "./Card";

export function EmptyState({ icon, text, title, ui }: { icon: FeatherName; text: string; title: string; ui: Ui }) {
  const { styles, theme } = ui;
  return (
    <Card ui={ui}>
      <View style={styles.emptyState}>
        <View style={styles.emptyIcon}>
          <Feather name={icon} size={24} color={theme.sky} />
        </View>
        <Text style={styles.cardTitle}>{title}</Text>
        <Text style={styles.bodyText}>{text}</Text>
      </View>
    </Card>
  );
}
