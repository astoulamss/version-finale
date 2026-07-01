import React, { createContext, useContext } from "react";
import { Alert } from "react-native";

interface FeedbackContextProps {
  triggerFeedback: (msg?: string) => void;
}

const FeedbackContext = createContext<FeedbackContextProps | undefined>(undefined);

export const FeedbackProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const triggerFeedback = (msg?: string) => {
    if (!msg) return;
    console.log("Feedback:", msg);
    // On peut afficher un Toast ou un Alert.
    // Laissons le console.log pour le moment ou une popup discrète s'il y a lieu.
  };

  return (
    <FeedbackContext.Provider value={{ triggerFeedback }}>
      {children}
    </FeedbackContext.Provider>
  );
};

export const useFeedback = () => {
  const context = useContext(FeedbackContext);
  if (!context) {
    throw new Error("useFeedback must be used within a FeedbackProvider");
  }
  return context;
};
