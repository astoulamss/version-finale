import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const TOKEN_KEY = 'ydays_auth_token';
const REFRESH_TOKEN_KEY = 'ydays_refresh_token';

// Fallback en mémoire au cas où SecureStore plante (ex: sur Web)
let memoryToken: string | null = null;
let memoryRefreshToken: string | null = null;

const isWeb = Platform.OS === 'web';

/**
 * Sauvegarder le token JWT
 */
export const saveToken = async (token: string): Promise<void> => {
  memoryToken = token;
  try {
    if (!isWeb) {
      await SecureStore.setItemAsync(TOKEN_KEY, token);
    }
  } catch (error) {
    console.warn('Erreur SecureStore (sauvegarde), utilisation du fallback mémoire', error);
  }
};

/**
 * Récupérer le token JWT
 */
export const getToken = async (): Promise<string | null> => {
  try {
    if (!isWeb) {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      return token || memoryToken;
    }
    return memoryToken;
  } catch (error) {
    console.warn('Erreur SecureStore (récupération), utilisation du fallback mémoire', error);
    return memoryToken;
  }
};

/**
 * Supprimer le token JWT
 */
export const removeToken = async (): Promise<void> => {
  memoryToken = null;
  try {
    if (!isWeb) {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    }
  } catch (error) {
    console.warn('Erreur SecureStore (suppression), fallback vidé', error);
  }
};

/**
 * Sauvegarder le Refresh Token
 */
export const saveRefreshToken = async (token: string): Promise<void> => {
  memoryRefreshToken = token;
  try {
    if (!isWeb) {
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token);
    }
  } catch (error) {
    console.warn('Erreur SecureStore (sauvegarde refresh), fallback mémoire utilisé', error);
  }
};

/**
 * Récupérer le Refresh Token
 */
export const getRefreshToken = async (): Promise<string | null> => {
  try {
    if (!isWeb) {
      const token = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
      return token || memoryRefreshToken;
    }
    return memoryRefreshToken;
  } catch (error) {
    console.warn('Erreur SecureStore (récupération refresh), fallback mémoire utilisé', error);
    return memoryRefreshToken;
  }
};

/**
 * Supprimer le Refresh Token
 */
export const removeRefreshToken = async (): Promise<void> => {
  memoryRefreshToken = null;
  try {
    if (!isWeb) {
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    }
  } catch (error) {
    console.warn('Erreur SecureStore (suppression refresh), fallback vidé', error);
  }
};
