import api from './api';

export interface ChatMessageRequest {
  message: string;
}

export const chatbotService = {
  createConversation: async (title?: string) => {
    const response = await api.post('/api/chatbot/conversations', { title });
    return response.data;
  },

  sendMessage: async (conversationId: number, message: string) => {
    const response = await api.post(`/api/chatbot/conversations/${conversationId}/messages`, { message });
    return response.data;
  },

  getConversations: async () => {
    const response = await api.get('/api/chatbot/conversations');
    return response.data;
  },

  getConversationDetails: async (conversationId: number) => {
    const response = await api.get(`/api/chatbot/conversations/${conversationId}`);
    return response.data;
  },

  deleteConversation: async (conversationId: number) => {
    const response = await api.delete(`/api/chatbot/conversations/${conversationId}`);
    return response.data;
  },

  closeConversation: async (conversationId: number) => {
    const response = await api.delete(`/api/chatbot/conversations/${conversationId}/close`);
    return response.data;
  }
};
