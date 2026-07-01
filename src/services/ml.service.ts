import api from './api';

interface TeamRiskItem {
  employee_id: number;
  turnover_risk: number | null;
  burnout_risk: number | null;
}

// Reproduit le seuillage de classify_risk() côté backend (api/ml_predict.py),
// appliqué ici à un score déjà exprimé sur une échelle 0-100.
function classifyRisk(score: number | null | undefined): 'High' | 'Medium' | 'Low' {
  if (score == null) return 'Low';
  if (score >= 75) return 'High';
  if (score >= 55) return 'Medium';
  return 'Low';
}

// /api/ml/predict/turnover|burnout/team n'existent pas côté backend.
// La donnée réelle par employé de l'équipe vient de /api/manager/risks.
const fetchTeamRisks = async (): Promise<TeamRiskItem[]> => {
  const response = await api.get('/api/manager/risks');
  return response.data;
};

export const mlService = {
  fetchTurnoverPredictions: async () => {
    const risks = await fetchTeamRisks();
    return {
      // Le rôle Manager reçoit turnover_risk=null (donnée masquée côté backend) :
      // on retombe alors sur burnout_risk pour ne pas afficher "En attente d'IA" à tort.
      predictions: risks.map(r => ({
        employee_id: r.employee_id,
        risk_level: classifyRisk(r.turnover_risk ?? r.burnout_risk),
      })),
    };
  },

  fetchBurnoutPredictions: async () => {
    const risks = await fetchTeamRisks();
    return {
      predictions: risks.map(r => ({
        employee_id: r.employee_id,
        risk_level: classifyRisk(r.burnout_risk),
      })),
    };
  }
};
