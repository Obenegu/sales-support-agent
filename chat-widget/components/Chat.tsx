import { useEffect, useState } from "react";
import { sendMessage, getChatHistory } from "../api/api";

interface ChatMessage {
    id: number;
    content: string;
    role: number;
    createdAt: string;
}

export default function Chat({ sessionId, userId }: { sessionId: string; userId: string }) {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);

    // Load previous messages for this session
    useEffect(() => {
        const loadHistory = async () => {
            const data = await getChatHistory(sessionId);
            setMessages(data);
            console.log("Sessiosn ID in Chat component:", sessionId);
        };

        loadHistory();
    }, [sessionId]);

    const sendChat = async () => {
        if (!input.trim()) return;

        setLoading(true);

        const payload = {
            message: input,
            userId,
            sessionId,
            role: 1
        };

        console.log("Sending payload:", payload);

        const userMsg: ChatMessage = {
            id: Date.now(),
            content: input,
            role: 1,
            createdAt: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMsg]);
        setInput("");

        const response = await sendMessage(payload);

        const botMsg: ChatMessage = {
            id: Date.now() + 1,
            content: response.response,
            role: 0,
            createdAt: new Date().toISOString(),
        };

        setMessages(prev => [...prev, botMsg]);
        setLoading(false);
    };

    return (
        <div className="w-full h-screen flex flex-col p-6 bg-gray-100">
            <div className="grow overflow-y-auto bg-white p-4 rounded shadow">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`my-2 p-3 rounded-xl max-w-[70%] ${
                            msg.role == 1
                                ? "ml-auto bg-blue-500 text-white"
                                : "mr-auto bg-gray-200"
                        }`}
                    >
                        {msg.content}
                    </div>
                ))}
                {loading && (
                    <div className="mr-auto bg-gray-200 p-3 rounded-xl max-w-[70%]">
                        Typing...
                    </div>
                )}
            </div>

            <div className="flex mt-4">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="grow p-3 border rounded-xl"
                    placeholder="Type message..."
                />
                <button
                    onClick={sendChat}
                    className="ml-2 px-6 py-3 text-black rounded-xl"
                >
                    Send
                </button>
            </div>
        </div>
    );
}
