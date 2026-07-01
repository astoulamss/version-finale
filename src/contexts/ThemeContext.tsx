import React, { createContext, useContext, useState } from "react";
import { darkTheme, lightTheme } from "../theme/colors";
import { createStyles } from "../theme/styles";
import { Ui } from "../types";

interface ThemeContextProps {
  ui: Ui;
  setThemeMode: (mode: "dark" | "light") => void;
}

const ThemeContext = createContext<ThemeContextProps | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themeMode, setThemeModeState] = useState<"dark" | "light">("light");
  const activeTheme = themeMode === "dark" ? darkTheme : lightTheme;

  const ui: Ui = {
    styles: createStyles(activeTheme),
    theme: activeTheme,
    toggleTheme: () => setThemeModeState((m) => (m === "dark" ? "light" : "dark")),
    isDark: themeMode === "dark",
  };

  const setThemeMode = (mode: "dark" | "light") => {
    setThemeModeState(mode);
  };

  return (
    <ThemeContext.Provider value={{ ui, setThemeMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useUi = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useUi must be used within a ThemeProvider");
  }
  return context;
};
