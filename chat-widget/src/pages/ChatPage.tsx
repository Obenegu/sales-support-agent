import Chat from "../../components/Chat";
import { useState } from "react";

export default function ChatPage() {
    const [sessionId, setSessionId] = useState(() => {
        return localStorage.getItem("sessionId") || crypto.randomUUID();
    });

    const userId = "junior"; // You can make this dynamic

    // Save session for persistence
    localStorage.setItem("sessionId", sessionId);

    return (
        <Chat sessionId="junior" userId={userId} />
    );
}
