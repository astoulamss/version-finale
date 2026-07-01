import api from './api';

export const surveysService = {
  fetchMySurveys: async (): Promise<any[]> => {
    const response = await api.get('/api/surveys/');
    return response.data;
  },

  submitSurveyResponse: async (surveyId: number, answers: { question_id: number; answer?: string; score?: number }[]): Promise<any> => {
    const response = await api.post(`/api/surveys/${surveyId}/responses`, {
      answers
    });
    return response.data;
  }
};
