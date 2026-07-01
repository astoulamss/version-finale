import api from './api';

export interface PerformanceReviewCreate {
  employee_id: number;
  review_date: string; // YYYY-MM-DD
  performance_rating: number; // 1 to 5
  comments?: string;
}

export const interviewsService = {
  fetchInterviews: async () => {
    const response = await api.get('/api/performance-reviews/');
    return response.data;
  },

  createInterview: async (data: PerformanceReviewCreate) => {
    const response = await api.post('/api/performance-reviews/', data);
    return response.data;
  }
};
