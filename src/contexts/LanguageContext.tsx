import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { I18nManager } from 'react-native';
import fr from '../i18n/fr.json';
import en from '../i18n/en.json';
import ar from '../i18n/ar.json';

const dictionaries: Record<string, any> = { fr, en, ar };

export type SupportedLanguage = 'fr' | 'en' | 'ar';

interface LanguageContextProps {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => Promise<void>;
  t: (key: string, variables?: Record<string, string | number>) => string;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextProps | undefined>(undefined);


export let currentLangGlobal: SupportedLanguage = 'fr';

export const globalT = (key: string, variables?: Record<string, string | number>) => {
  const keys = key.split('.');
  let value = dictionaries[currentLangGlobal];
  for (const k of keys) {
    if (!value) break;
    value = value[k];
  }
  let translated = value || key;
  if (variables && typeof translated === 'string') {
    Object.keys(variables).forEach((v) => {
      translated = translated.replace(new RegExp(`\{\{${v}\}\}`, 'g'), String(variables[v]));
    });
  }
  return translated;
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<SupportedLanguage>('fr');
  const [isRTL, setIsRTL] = useState(false);

  useEffect(() => {
    const loadLang = async () => {
      try {
        const savedLang = await AsyncStorage.getItem('app_language');
        if (savedLang && ['fr', 'en', 'ar'].includes(savedLang)) {
          setLanguageState(savedLang as SupportedLanguage);
          currentLangGlobal = savedLang as SupportedLanguage;
          
          // Ensure native RTL matches
          const rtl = savedLang === 'ar';
          setIsRTL(rtl);
          if (I18nManager.isRTL !== rtl) {
             I18nManager.allowRTL(rtl);
             I18nManager.forceRTL(rtl);
          }
        }
      } catch (e) {
        console.warn("Failed to load language", e);
      }
    };
    loadLang();
  }, []);

  const setLanguage = async (lang: SupportedLanguage) => {
    try {
      await AsyncStorage.setItem('app_language', lang);
      setLanguageState(lang);
      currentLangGlobal = lang;
      
      const rtl = lang === 'ar';
      setIsRTL(rtl);
      if (I18nManager.isRTL !== rtl) {
        I18nManager.allowRTL(rtl);
        I18nManager.forceRTL(rtl);
      }
    } catch (e) {
      console.warn("Failed to set language", e);
    }
  };

  const t = (key: string, variables?: Record<string, string | number>): string => {
    const dictionary = dictionaries[language] || dictionaries.fr;
    const keys = key.split('.');
    let value = dictionary;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key;
      }
    }
    
    let result = typeof value === 'string' ? value : key;
    
    if (variables) {
      Object.keys(variables).forEach(varKey => {
        result = result.replace(`{{${varKey}}}`, String(variables[varKey]));
      });
    }
    
    return result;
  };

    return (
    <LanguageContext.Provider value={{ language, setLanguage, t, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
