"use client";

import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import MobileHeader from "./components/MobileHeader";

interface Chat {
  id: string;
  title: string;
  timestamp: number;
  messages: ChatMessage[];
}

interface ChatMessage {
  id: number;
  content: string;
  role: "user" | "assistant";
  timestamp: number;
  intent?: string;
  toolUsed?: string;
  isError?: boolean;
}

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentChat, setCurrentChat] = useState<string | null>(null);
  const [chats, setChats] = useState<Chat[]>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("genuka_chats");
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setSidebarOpen(false);
      else setSidebarOpen(true);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    localStorage.setItem("genuka_chats", JSON.stringify(chats));
  }, [chats]);

  const createNewChat = () => {
    const newChat: Chat = {
      id: crypto.randomUUID(),
      title: "New Chat",
      timestamp: Date.now(),
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChat(newChat.id);
    if (isMobile) setSidebarOpen(false);
  };

  const deleteChat = (id: string) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (currentChat === id) setCurrentChat(null);
  };

  const renameChat = (id: string, newTitle: string) => {
    setChats((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c))
    );
  };

  const updateChatMessages = (chatId: string, messages: ChatMessage[]) => {
    setChats((prev) =>
      prev.map((c) => {
        if (c.id !== chatId) return c;
        const firstUserMsg = messages.find((m) => m.role === "user");
        const title = firstUserMsg
          ? firstUserMsg.content.slice(0, 30) +
            (firstUserMsg.content.length > 30 ? "..." : "")
          : c.title;
        return { ...c, messages, title, timestamp: Date.now() };
      })
    );
  };

  useEffect(() => {
    if (chats.length === 0 && typeof window !== "undefined") {
      createNewChat();
    }
  }, []);

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ background: "var(--bg-primary)" }}
    >
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-30 sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar
        chats={chats}
        currentChat={currentChat}
        onSelectChat={setCurrentChat}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        isOpen={sidebarOpen}
        isMobile={isMobile}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <MobileHeader
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
        />
        <ChatArea
          chatId={currentChat}
          chats={chats}
          onUpdateMessages={updateChatMessages}
          isMobile={isMobile}
        />
      </div>
    </div>
  );
}
