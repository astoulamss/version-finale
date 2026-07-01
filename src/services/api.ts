import axios from 'axios';
import { getToken, removeToken, saveToken } from '../utils/token.utils';
import { globalEvents } from '../lib/events';

import Constants from 'expo-constants';

const debuggerHost = Constants.expoConfig?.hostUri;
const ip = debuggerHost ? debuggerHost.split(':')[0] : '192.168.8.228';
export const API_BASE_URL = `http://${ip}:8000`;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // Augmenté à 120s pour les requêtes longues de l'IA (LLM)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour injecter le Token dans chaque requête
api.interceptors.request.use(
  async (config) => {
    const token = await getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Intercepteur pour gérer les erreurs globalement
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Si l'erreur est 401 (Non Autorisé) et que ce n'est pas déjà une tentative de retry ou refresh
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/api/auth/refresh') {

      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      let currentToken: string | null = null;
      try {
        currentToken = await getToken();
        if (!currentToken) {
          globalEvents.emit('session_expired');
          throw new Error("No token to refresh");
        }
        if (currentToken === "mock_token") {
          throw new Error("Offline Mock Token");
        }
        // Le endpoint /api/auth/refresh attend le token actuel en Bearer
        const res = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {}, {
          headers: {
            'Authorization': `Bearer ${currentToken}`
          }
        });

        const newToken = res.data.access_token;
        await saveToken(newToken);

        api.defaults.headers.common['Authorization'] = 'Bearer ' + newToken;
        originalRequest.headers['Authorization'] = 'Bearer ' + newToken;

        processQueue(null, newToken);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);

        // On ne supprime le token que s'il n'a pas été remplacé (ex: par un login concurrent)
        const tokenNow = await getToken();
        if (tokenNow === currentToken && currentToken !== "mock_token") {
          await removeToken();
          globalEvents.emit('session_expired');
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
