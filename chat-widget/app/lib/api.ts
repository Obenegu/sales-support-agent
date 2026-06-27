import axios from "axios";

// const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";        
const API_URL = "https://localhost:7106/api";
// const API_URL = "/api";     

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("Unauthorized - redirect to login");
    }
    return Promise.reject(error);
  }
);

// Chat API
export const sendMessage = async (payload: {
  message: string;
  userId: string;
  sessionId: string;
  role: number; // 0 for assistant, 1 for user
}) => {
  const res = await api.post("/chat", payload);
  return res.data;
};

export const getChatHistory = async (sessionId: string) => {
  const res = await api.get(`/chat/${sessionId}`);
  return res.data;
};
export const getChatSessions = async (userId: string) => {
  const res = await api.get(`/chat/sessions/${userId}`);
  return res.data;
};

// Health check
export const healthCheck = async () => {
  const res = await axios.get("/");
  return res.data;
};

export default api;
