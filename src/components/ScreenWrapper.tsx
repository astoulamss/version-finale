import React from "react";
import { View, ScrollView, StyleSheet } from "react-native";
import { Ui } from "../types";

interface ScreenWrapperProps {
  children: React.ReactNode;
  isScrollable?: boolean;
  ui: Ui;
}

export function ScreenWrapper({ children, isScrollable = true, ui }: ScreenWrapperProps) {
  if (isScrollable) {
    return (
      <ScrollView contentContainerStyle={[ui.styles.scrollContent, styles.scrollPadding]} showsVerticalScrollIndicator={false}>
        {children}
      </ScrollView>
    );
  }
  return (
    <View style={[ui.styles.scrollContent, styles.flatContainer]}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  scrollPadding: {
    paddingBottom: 110,
  },
  flatContainer: {
    flex: 1,
    paddingBottom: 100,
  },
});
