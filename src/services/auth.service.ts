import api from './api';
import { saveToken, removeToken } from '../utils/token.utils';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: any; // On affinera le type plus tard
}

const authService = {
  /**
   * Se connecter à l'API
   */
  login: async (email: string, mots_de_passe: string): Promise<LoginResponse> => {
    try {
      const response = await api.post<LoginResponse>('/api/auth/login', {
        email,
        mots_de_passe,
      });

      // Sauvegarder le token si la connexion réussit
      if (response.data.access_token) {
        await saveToken(response.data.access_token);
      }

      return response.data;
    } catch (error: any) {
      // Propagation de l'erreur pour pouvoir l'afficher dans l'interface
      if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('Erreur de connexion au serveur');
    }
  },

  /**
   * Se déconnecter de l'application
   */
  logout: async (): Promise<void> => {
    try {
      await api.post('/api/auth/logout');
    } catch (e) {
      console.warn("Erreur réseau lors de la déconnexion backend", e);
    }
    await removeToken();
  },

  /**
   * Changer le mot de passe de l'utilisateur courant
   */
  changePassword: async (old_password: string, new_password: string): Promise<void> => {
    try {
      await api.put('/api/users/me/change-password', {
        old_password,
        new_password
      });
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('Erreur lors du changement de mot de passe');
    }
  },
};

export default authService;
