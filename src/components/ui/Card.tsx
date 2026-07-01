import React from "react";
import { View, Pressable } from "react-native";
import { Ui, StatusTone } from "../../types";

export function Card({ children, tone = "neutral", onPress, ui, style }: { children: React.ReactNode; tone?: StatusTone; onPress?: () => void; ui: Ui; style?: object }) {
  const { styles } = ui;
  const content = <View style={[styles.card, tone !== "neutral" && styles[`tone_${tone}`], style]}>{children}</View>;
  if (onPress) {
    return <Pressable onPress={onPress} style={({ pressed }) => [pressed && { opacity: 0.9, transform: [{ scale: 0.98 }] }]}>{content}</Pressable>;
  }
  return content;
}

export function AICard({ children, ui, style }: { children: React.ReactNode; ui: Ui; style?: object }) {
  return <View style={[ui.styles.aiCard, style]}>{children}</View>;
}
