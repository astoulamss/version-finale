import api from './api';

export interface CreateContractPayload {
  user_id: number;
  contract_type: string;
  start_date: string;
  end_date?: string | null;
  position: string;
  salary: string;
}

export interface CreateFormationPayload {
  title: string;
  description: string;
  start_date: string;
  end_date: string;
}

export interface UploadDocumentPayload {
  title: string;
  document_type: string;
  file_path: string;
  user_id?: number;
}

/**
 * Créer un nouveau contrat pour un employé
 */
export const createContract = async (payload: CreateContractPayload): Promise<any> => {
  const response = await api.post('/api/contracts/', payload);
  return response.data;
};

/**
 * Créer une nouvelle formation (catalogue)
 */
export const createFormation = async (payload: CreateFormationPayload): Promise<any> => {
  const response = await api.post('/api/formations/', payload);
  return response.data;
};

/**
 * Télécharger (uploader) un document RH pour un employé
 */
export const uploadDocument = async (payload: UploadDocumentPayload): Promise<any> => {
  const response = await api.post('/api/documents/', payload);
  return response.data;
};

export const uploadRealDocument = async (formData: FormData): Promise<any> => {
  const response = await api.post('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    transformRequest: (data, headers) => {
      // Definitive fix for React Native FormData boundary issues with Axios
      return data;
    },
  });
  return response.data;
};

/**
 * Récupérer tous les employés (Annuaire)
 */
export const fetchAllEmployees = async (): Promise<any[]> => {
  const response = await api.get('/api/employees/');
  return response.data;
};

/**
 * Récupérer tous les départements
 */
export const fetchDepartments = async (): Promise<any[]> => {
  const response = await api.get('/api/employees/departments');
  return response.data;
};

/**
 * Récupérer tous les postes
 */
export const fetchPositions = async (): Promise<any[]> => {
  const response = await api.get('/api/employees/positions');
  return response.data;
};

/**
 * Récupérer tous les managers (pour les sélecteurs)
 */
export const fetchManagers = async (): Promise<any[]> => {
  const response = await api.get('/api/employees/managers');
  return response.data;
};

/**
 * Créer un nouveau département
 */
export const createDepartment = async (payload: { name: string, description?: string }): Promise<any> => {
  const response = await api.post('/api/employees/departments', payload);
  return response.data;
};

/**
 * Mettre à jour un département
 */
export const updateDepartment = async (id: number, payload: { name?: string, description?: string, manager_id?: number | null }): Promise<any> => {
  const response = await api.patch(`/api/employees/departments/${id}`, payload);
  return response.data;
};

/**
 * Supprimer un département
 */
export const deleteDepartment = async (id: number): Promise<any> => {
  const response = await api.delete(`/api/employees/departments/${id}`);
  return response.data;
};

/**
 * Créer un nouveau poste
 */
export const createPosition = async (payload: { title: string, description?: string }): Promise<any> => {
  const response = await api.post('/api/employees/positions', payload);
  return response.data;
};

/**
 * Mettre à jour un poste
 */
export const updatePosition = async (id: number, payload: { title?: string, description?: string }): Promise<any> => {
  const response = await api.patch(`/api/employees/positions/${id}`, payload);
  return response.data;
};

/**
 * Supprimer un poste
 */
export const deletePosition = async (id: number): Promise<any> => {
  const response = await api.delete(`/api/employees/positions/${id}`);
  return response.data;
};

/**
 * Créer un nouveau profil employé pour un utilisateur existant
 */
export const createEmployee = async (payload: any): Promise<any> => {
  const response = await api.post('/api/employees/', payload);
  return response.data;
};

/**
 * Récupérer tous les utilisateurs
 */
export const fetchUsers = async (): Promise<any[]> => {
  const response = await api.get('/api/users/');
  return response.data;
};
