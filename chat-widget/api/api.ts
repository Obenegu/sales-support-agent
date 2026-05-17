import axios from "axios";

const API_URL = "https://localhost:7106/api/Chat"; // <-- update backend URL if needed

export const sendMessage = async (payload: any) => {
    const res = await axios.post(API_URL, payload);
    return res.data;
};

export const getChatHistory = async (sessionId: string) => {
    const res = await axios.get(`${API_URL}/${sessionId}`);
    console.log("API getChatHistory response:", res.data);
    return res.data;
};
