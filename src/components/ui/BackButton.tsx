import React from 'react';

import { Pressable, StyleSheet, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Ui } from '../../types';

interface BackButtonProps {
  onPress: () => void;
  ui: Ui;
  variant?: 'default' | 'onImage';
}

export function BackButton({ onPress, ui, variant = 'default' }: BackButtonProps) {
  const isDark = ui.isDark;

  // Définition des couleurs selon la variante et le thème
  // Variante "onImage" = fond toujours très contrasté (sombre translucide) avec icône claire
  const backgroundColor = variant === 'onImage' 
    ? 'rgba(0, 0, 0, 0.4)' 
    : isDark 
      ? 'rgba(255, 255, 255, 0.08)' // Thème sombre standard
      : ui.theme.surfaceAlt;        // Thème clair standard
      
  const iconColor = variant === 'onImage'
    ? '#FFFFFF' // Toujours blanc sur image
    : ui.theme.text;

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel="Retour"
      accessibilityHint="Retourne à l'écran précédent"
      style={({ pressed }) => [
        styles.touchableArea,
        pressed && { opacity: 0.7 }
      ]}
    >
      <View style={[styles.circle, { backgroundColor }]}>
        <Feather name="chevron-left" size={24} color={iconColor} style={styles.icon} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  // Zone de clic étendue (Hitbox) d'au moins 44x44
  touchableArea: {
    minWidth: 44,
    minHeight: 44,
    justifyContent: 'center',
    alignItems: 'center',
    // Marge négative optionnelle si on veut l'aligner parfaitement sur la grille tout en gardant une grande hitbox
    // marginLeft: -4, 
  },
  // Cercle visuel du bouton (38x38)
  circle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    // Petit ajustement optique pour centrer visuellement le chevron
    marginLeft: -2,
  }
});
