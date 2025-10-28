import axios from 'axios';

// Get the API URL based on environment
const getApiUrl = () => {
  // If NEXT_PUBLIC_API_URL is explicitly set, use it (for production)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Check if we're in production (hosted environment)
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    // If hostname is localhost or a local IP, use local backend
    if (host === 'localhost' || host === '127.0.0.1' || host.startsWith('192.168.') || host.startsWith('10.0.')) {
      return `http://${host}:8000`;
    }
    // Otherwise, use the production Lambda URL
    return 'https://tl4hbolniutrcuwr5cv4hyqvzq0zaevo.lambda-url.us-west-1.on.aws';
  }
  
  // Default fallback for server-side rendering
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ReceiptItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

export interface ReceiptData {
  items: ReceiptItem[];
  subtotal: number;
  tax: number;
  tip: number;
  total: number;
  image_url?: string;
  session_id?: string;
}

export interface SessionCreate {
  host_name: string;
  receipt_data: ReceiptData;
  receipt_image_url?: string;
  session_id?: string;
  host_payment_handle?: string;
  number_of_guests?: number;
}

export interface SessionResponse {
  id: string;
  host_name: string;
  host_payment_handle?: string;
  receipt_image_url?: string;
  receipt_items: ReceiptItem[];
  item_splits?: Record<string, any>;
  claimed_items?: Record<string, any>;
  number_of_guests: number;
  tax_amount: number;
  tip_amount: number;
  subtotal: number;
  total: number;
  qr_code_url: string;
  created_at: string;
  status: string;
}

export interface UserJoin {
  name: string;
}

export interface UserSelectItems {
  item_ids: string[];
  payment_method?: string;
  payment_handle?: string;
}

export interface UserResponse {
  id: number;
  name: string;
  selected_items: string[];
  subtotal: number;
  tax: number;
  tip: number;
  total: number;
  paid: boolean;
  payment_method?: string;
  host_payment_handle?: string;
}

export const receiptAPI = {
  upload: async (file: File): Promise<ReceiptData> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // Use axios directly (not the 'api' instance) to avoid Content-Type conflicts
    // The browser will automatically set the correct multipart/form-data with boundary
    const response = await axios.post(
      `${API_BASE_URL}/api/receipt/upload`,
      formData
    );
    return response.data;
  },
};

export const sessionAPI = {
  create: async (data: SessionCreate): Promise<SessionResponse> => {
    const response = await api.post('/api/session/create', data);
    return response.data;
  },
  get: async (sessionId: string): Promise<SessionResponse> => {
    const response = await api.get(`/api/session/${sessionId}`);
    return response.data;
  },
  join: async (sessionId: string, data: UserJoin) => {
    const response = await api.post(`/api/session/${sessionId}/join`, data);
    return response.data;
  },
  selectItems: async (
    sessionId: string,
    userId: number,
    data: UserSelectItems
  ): Promise<UserResponse> => {
    const response = await api.post(
      `/api/session/${sessionId}/user/${userId}/select`,
      data
    );
    return response.data;
  },
  markPaid: async (sessionId: string, userId: number) => {
    const response = await api.post(
      `/api/session/${sessionId}/user/${userId}/pay`,
      { paid: true }
    );
    return response.data;
  },
  getStatus: async (sessionId: string) => {
    const response = await api.get(`/api/session/${sessionId}/status`);
    return response.data;
  }
};

export default api;
