import api from './api';

export const mlService = {
  fetchTurnoverPredictions: async () => {
    const response = await api.get('/api/ml/predict/turnover/team');
    return response.data;
  },

  fetchBurnoutPredictions: async () => {
    const response = await api.get('/api/ml/predict/burnout/team');
    return response.data;
  }
};
