import axios from "axios";

// Use relative path — Next.js rewrites proxy server-side to backend:5132
// This avoids CORS: browser → Next.js → backend (all server-to-server)
const API_URL = "/api";

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

// ── Chat API ──────────────────────────────────────────────

export const sendMessage = async (payload: {
  message: string;
  userId: string;
  sessionId: string;
  role: string;
}) => {
  const res = await api.post("/Chat", payload);
  return res.data;
};

export const getChatHistory = async (sessionId: string, userId: string) => {
  const res = await api.get(`/Chat/${sessionId}?userId=${encodeURIComponent(userId)}`);
  return res.data;
};

// ── Session API ───────────────────────────────────────────

export interface SessionDto {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
  messageCount: number;
}

export const getSessions = async (userId: string): Promise<SessionDto[]> => {
  const res = await api.get(`/Session?userId=${encodeURIComponent(userId)}`);
  return res.data;
};

export const createSession = async (userId: string, title?: string): Promise<SessionDto> => {
  const res = await api.post("/Session", { userId, title });
  return res.data;
};

export const updateSession = async (id: string, title: string): Promise<SessionDto> => {
  const res = await api.put(`/Session/${id}`, { title });
  return res.data;
};

export const deleteSession = async (id: string): Promise<void> => {
  await api.delete(`/Session/${id}`);
};

// ── Health check ──────────────────────────────────────────

export const healthCheck = async () => {
  const res = await axios.get("/");
  return res.data;
};

export default api;
