import api from "./api";

export interface RecipientOption {
  id: number;
  name: string;
  type: 'DEPARTMENT' | 'EMPLOYEE';
}

export interface RecipientsListResponse {
  departments: RecipientOption[];
  employees: RecipientOption[];
}

export interface AnnouncementCreate {
  title: string;
  content: string;
  recipient_type: 'GLOBAL' | 'DEPARTMENT' | 'EMPLOYEE';
  recipient_id?: number;
}

export interface AnnouncementResponse {
  id: number;
  title: string;
  content: string;
  sender_name: string;
  recipient_type: 'GLOBAL' | 'DEPARTMENT' | 'EMPLOYEE';
  recipient_id?: number;
  recipient_name: string;
  status: 'SENT' | 'DELIVERED' | 'READ' | 'FAILED';
  created_at: string;
}

export const announcementService = {
  getRecipients: async (): Promise<RecipientsListResponse> => {
    const response = await api.get("/api/announcements/recipients");
    return response.data;
  },

  sendAnnouncement: async (data: AnnouncementCreate): Promise<AnnouncementResponse> => {
    const response = await api.post("/api/announcements", data);
    return response.data;
  },

  getHistory: async (): Promise<AnnouncementResponse[]> => {
    const response = await api.get("/api/announcements");
    return response.data;
  }
};
