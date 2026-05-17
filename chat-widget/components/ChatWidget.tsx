import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

interface Message {
  content: string;
  userId: "string";
  role: "user";
}

interface FetchChatHistoryResponse {
  agentResponse: string;
  businessId: number;
  userMessage: string;
}

interface AgentReply {
  response: string;
  tool_used: string;
  intent: string;
  role: string;
}

const ChatWidget = () => {
  const [messages, setMessages] = useState<(Message | AgentReply)[]>([]);
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const userId = "string"

  const apiUrl = "https://localhost:7106/api/Chat"; // Your .NET endpoint

  // fetch from backend DB on load
  useEffect(() => {
    fetch(`${apiUrl}/${userId}`)
      .then(res => res.json())
      .then(history => 
      {
        console.log("Chat history loaded:", history);
        setMessages(history)
      }
      )
      .catch(() => {});
  }, []);



  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { content: input, userId: "string", role: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
    //   const token = localStorage.getItem("jwt_token");
      const res = await axios.post(
        apiUrl,
        { message: input },
      );

      console.log("API Response:", res.data);

    const agentReply: AgentReply = {
      response: res.data.response,
      intent: res.data.intent,
      tool_used: res.data.tool_used,
      role: res.data.role,
    };



      setMessages((prev) => [...prev, agentReply]);

      console.log("Agent Reply:", agentReply);

    } catch (err) {
      console.error(err);
      const errorMsg: AgentReply = {
        response: "Oops! Something went wrong. Try again.",
        tool_used: "Error",
        intent: "Error",
        role: "assistant",
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-widget">
      <div className="chat-messages">
        {messages.map((msg, idx) => {
          const isUser = "userId" in msg;
          const content = isUser 
            ? msg.content : (msg as AgentReply).response;

          return (
            <div
              key={idx}
              className={`chat-message ${isUser ? "user" : "assistant"}`}
            >
              {content}
            </div>
          );
        })}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default ChatWidget;