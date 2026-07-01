import React from "react";
import { View, Text, Pressable } from "react-native";
import { Ui, StatusTone } from "../../types";
import { toneBackground, toneColor } from "../../theme/utils";

export function StatusBadge({ label, tone, ui }: { label: string; tone: StatusTone; ui: Ui }) {
  const { styles, theme } = ui;
  return (
    <View style={[styles.badge, { backgroundColor: toneBackground(tone, theme), flexShrink: 1 }]}>
      <Text numberOfLines={1} ellipsizeMode="tail" style={[styles.badgeText, { color: toneColor(tone, theme) }]}>{label}</Text>
    </View>
  );
}

export function Chip({ active, label, onPress, ui, disabled }: { active?: boolean; label: string; onPress?: () => void; ui: Ui; disabled?: boolean }) {
  const { styles, theme } = ui;

  return (
    <Pressable disabled={disabled || !onPress} onPress={onPress} style={({ pressed }) => [styles.chip, active && styles.chipActive, disabled && { opacity: 0.5 }, pressed && { opacity: 0.9, transform: [{ scale: 0.96 }] }]}>
      <Text style={[styles.chipText, active && { color: theme.sky }]}>{label}</Text>
    </Pressable>
  );
}
