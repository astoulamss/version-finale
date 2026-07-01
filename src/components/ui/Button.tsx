import React from "react";
import { Pressable, Text, ActivityIndicator } from "react-native";
import { Feather } from "@expo/vector-icons";
import { Ui, FeatherName } from "../../types";

export function PrimaryButton({
  icon, label, onPress, ui, disabled, loading
}: {
  icon?: FeatherName; label: string; onPress: () => void;
  ui: Ui; disabled?: boolean; loading?: boolean;
}) {
  const { styles } = ui;
  return (
    <Pressable
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.primaryButton,
        (disabled || loading) && { opacity: 0.45 },
        pressed && !disabled && !loading && { opacity: 0.88, transform: [{ scale: 0.975 }] },
      ]}
    >
      {loading ? (
        <ActivityIndicator color="#FFFFFF" size="small" />
      ) : (
        <>
          {icon && <Feather name={icon} size={18} color="#FFFFFF" />}
          <Text style={styles.primaryButtonText}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

export function SecondaryButton({
  icon, label, onPress, ui, disabled, loading
}: {
  icon?: FeatherName; label: string; onPress: () => void;
  ui: Ui; disabled?: boolean; loading?: boolean;
}) {
  const { styles, theme } = ui;
  return (
    <Pressable
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.secondaryButton,
        (disabled || loading) && { opacity: 0.45 },
        pressed && !disabled && !loading && { opacity: 0.88, transform: [{ scale: 0.975 }] },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={theme.sky} size="small" />
      ) : (
        <>
          {icon && <Feather name={icon} size={17} color={theme.sky} />}
          <Text style={styles.secondaryButtonText}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

export function IconButton({
  icon, onPress, ui, disabled, loading
}: {
  icon: FeatherName; onPress: () => void;
  ui: Ui; disabled?: boolean; loading?: boolean;
}) {
  const { styles, theme } = ui;
  return (
    <Pressable
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.iconButton,
        (disabled || loading) && { opacity: 0.45 },
        pressed && !disabled && !loading && { opacity: 0.88, transform: [{ scale: 0.95 }] },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={theme.text} size="small" />
      ) : (
        <Feather name={icon} size={18} color={theme.text} />
      )}
    </Pressable>
  );
}

export function DestructiveButton({
  icon, label, onPress, ui, disabled, loading
}: {
  icon?: FeatherName; label: string; onPress: () => void;
  ui: Ui; disabled?: boolean; loading?: boolean;
}) {
  const { theme } = ui;
  return (
    <Pressable
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        {
          alignItems: 'center' as const,
          backgroundColor: theme.rose,
          borderRadius: 12,
          flexDirection: 'row' as const,
          gap: 8,
          justifyContent: 'center' as const,
          minHeight: 48,
          paddingHorizontal: 16,
        },
        (disabled || loading) && { opacity: 0.45 },
        pressed && !disabled && !loading && { opacity: 0.88, transform: [{ scale: 0.975 }] },
      ]}
    >
      {loading ? (
        <ActivityIndicator color="#FFFFFF" size="small" />
      ) : (
        <>
          {icon && <Feather name={icon} size={18} color="#FFFFFF" />}
          <Text style={{ color: '#FFFFFF', fontSize: 16, fontWeight: '600' }}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}
