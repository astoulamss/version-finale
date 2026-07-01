import React from "react";
import { View, Platform, Pressable, StyleSheet } from "react-native";
import { Feather } from "@expo/vector-icons";
import { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { Ui, FeatherName } from "../types";

const getIconName = (routeName: string): FeatherName => {
  switch (routeName) {
    case 'home': return 'home';
    case 'rh_hub': return 'grid';
    case 'manager_hub': return 'grid';
    case 'assistant': return 'message-square';
    case 'profile': return 'user';
    case 'admin_profile': return 'settings';
    case 'indicateurs': return 'pie-chart';
    case 'validations': return 'check-circle';
    case 'team': return 'users';
    case 'admin_dashboard': return 'shield';
    case 'admin_accounts': return 'users';
    case 'admin_alerts': return 'alert-triangle';
    case 'admin_logs': return 'list';
    default: return 'circle';
  }
};

interface MyCustomTabBarProps extends BottomTabBarProps {
  ui: Ui;
}

export function MyCustomTabBar({ state, navigation, ui }: MyCustomTabBarProps) {
  const isDark = ui.isDark;

  return (
    <View style={styles.outerContainer}>
      <View style={[
        styles.innerContainer,
        {
          backgroundColor: isDark ? 'rgba(6,12,26,0.96)' : 'rgba(255,255,255,0.97)',
          borderColor: isDark ? 'rgba(59,130,246,0.18)' : 'rgba(37,99,235,0.12)',
        }
      ]}>
        {state.routes.map((route, index) => {
          const isFocused = state.index === index;

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });
            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate({ name: route.name, merge: true } as any);
            }
          };

          return (
            <Pressable
              key={route.key}
              onPress={onPress}
              android_ripple={{ color: ui.theme.skySoft, borderless: true, radius: 26 }}
              style={({ pressed }) => [
                styles.tabPressable,
                pressed && { opacity: 0.75 }
              ]}
            >
              <View style={[
                styles.iconWrapper,
                isFocused && {
                  backgroundColor: isDark ? 'rgba(59,130,246,0.20)' : ui.theme.skySoft,
                  borderWidth: 1,
                  borderColor: isDark ? 'rgba(59,130,246,0.35)' : 'rgba(37,99,235,0.20)',
                }
              ]}>
                <Feather
                  name={getIconName(route.name)}
                  size={21}
                  color={isFocused ? ui.theme.sky : ui.theme.muted}
                />
              </View>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outerContainer: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 18 : 8,
    left: 16,
    right: 16,
    alignItems: 'center',
  },
  innerContainer: {
    flexDirection: 'row',
    borderRadius: 52,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 10,
    width: '100%',
    maxWidth: 420,
    shadowColor: '#060C1A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.22,
    shadowRadius: 28,
    elevation: 12,
    justifyContent: 'space-between',
  },
  tabPressable: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWrapper: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 52,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
