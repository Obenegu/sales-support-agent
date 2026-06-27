"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import TopNav from "./components/TopNav";
import { v4 as uuidv4 } from "uuid";
import { getChatSessions } from "./lib/api";

export interface ChatMessage {
  id: number;
  content: string;
  role: 0 | 1;
  timestamp: number;
  intent?: string;
  toolUsed?: string;
  isError?: boolean;
}

export interface Chat {
  id: string;
  title: string;
  timestamp: number;
  messages: ChatMessage[];
}

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const initialized = useRef(false);

   const userId = "junior";


const chatSessions = async (id: string) => {
  id = userId
  try{
    const sessionsList = await getChatSessions(id);
    console.log("List of chat Sessions", sessionsList);

  } catch(err) {
    console.error("Session Error", err)
  }
}

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("genuka_chats");
      if (saved) {
        const parsed = JSON.parse(saved) as Chat[];
        setChats(parsed);
        if (parsed.length > 0) {
          setCurrentChatId(parsed[0].id);
        }
      }
    } catch {
      setChats([]);
    }
  }, []);

  // Save to localStorage
  useEffect(() => {
    if (chats.length > 0) {
      localStorage.setItem("genuka_chats", JSON.stringify(chats));
    }
  }, [chats]);

  // Mobile detection
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Create first chat if none exists
  useEffect(() => {
    if (!initialized.current && chats.length === 0) {
      initialized.current = true;
      const newChat: Chat = {
        id: uuidv4(),
        title: "New Chat",
        timestamp: Date.now(),
        messages: [],
      };
      setChats([newChat]);
      setCurrentChatId(newChat.id);
    }
  }, [chats.length]);

  const createNewChat = useCallback(() => {
    const newChat: Chat = {
      id: uuidv4(),
      title: "New Chat",
      timestamp: Date.now(),
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setSidebarOpen(false);
  }, []);

  const deleteChat = useCallback((id: string) => {
    setChats((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      return filtered;
    });
    setCurrentChatId((prev) => (prev === id ? null : prev));
  }, []);

  const renameChat = useCallback((id: string, newTitle: string) => {
    setChats((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c))
    );
  }, []);

  const appendMessage = useCallback((chatId: string, message: ChatMessage) => {
    setChats((prev) =>
      prev.map((c) => {
        if (c.id !== chatId) return c;
        const newMessages = [...c.messages, message];
        const firstUserMsg = newMessages.find((m) => m.role === 1);
        const title = firstUserMsg
          ? firstUserMsg.content.slice(0, 40) +
            (firstUserMsg.content.length > 40 ? "..." : "")
          : c.title;
        return { ...c, messages: newMessages, title, timestamp: Date.now() };
      })
    );
  }, []);

  const updateMessages = useCallback((chatId: string, messages: ChatMessage[]) => {
    setChats((prev) =>
      prev.map((c) => {
        if (c.id !== chatId) return c;
        const firstUserMsg = messages.find((m) => m.role === 1);
        const title = firstUserMsg
          ? firstUserMsg.content.slice(0, 40) +
            (firstUserMsg.content.length > 40 ? "..." : "")
          : c.title;
        return { ...c, messages, title, timestamp: Date.now() };
      })
    );
  }, []);

  const currentChat = chats.find((c) => c.id === currentChatId) || null;
  const messages = currentChat?.messages || [];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--bg-primary)]">
      {/* Sidebar overlay for mobile/desktop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar
        chats={chats}
        currentChat={currentChatId}
        onSelectChat={(id) => {
          setCurrentChatId(id);
          setSidebarOpen(false);
        }}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 min-w-0 relative">
        <TopNav
          onMenuClick={() => setSidebarOpen(true)}
          onNewChat={createNewChat}
          currentTitle={currentChat?.title || "New Chat"}
        />
        <ChatArea
          chatId={currentChatId}
          messages={messages}
          onAppendMessage={appendMessage}
          onUpdateMessages={updateMessages}
          isMobile={isMobile}
        />
      </div>
    </div>
  );
}
