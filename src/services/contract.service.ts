import api from './api';
import type { Contract } from '../types';

export interface ContractCreate {
  contract_type: string;
  start_date: string;
  end_date?: string;
  position: string;
  salary?: string;
}

export const contractService = {
  // Récupérer le contrat de l'employé connecté
  getMyContract: async (): Promise<Contract> => {
    const response = await api.get('/api/contracts/my-contract');
    return response.data;
  },

  // Récupérer tous les contrats (RH uniquement)
  getAllContracts: async (): Promise<Contract[]> => {
    const response = await api.get('/api/contracts/');
    return response.data;
  },

  // Récupérer le contrat d'un employé spécifique (RH uniquement)
  getEmployeeContract: async (userId: number): Promise<Contract> => {
    const response = await api.get(`/api/contracts/employee/${userId}`);
    return response.data;
  },

  // Créer un contrat pour un employé (RH uniquement)
  createContract: async (userId: number, data: ContractCreate): Promise<Contract> => {
    const response = await api.post(`/api/contracts/employee/${userId}`, data);
    return response.data;
  },

  // Mettre à jour un contrat (RH uniquement)
  updateContract: async (contractId: number, data: ContractCreate): Promise<Contract> => {
    const response = await api.put(`/api/contracts/${contractId}`, data);
    return response.data;
  },

  // Supprimer un contrat (RH uniquement)
  deleteContract: async (contractId: number): Promise<{message: string}> => {
    const response = await api.delete(`/api/contracts/${contractId}`);
    return response.data;
  },

  // Générer le document (PDF) pour un contrat
  generateDocument: async (contractId: number): Promise<{message: string, document_id: number}> => {
    const response = await api.post(`/api/contracts/${contractId}/generate-document`);
    return response.data;
  }
};
