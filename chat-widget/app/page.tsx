"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import TopNav from "./components/TopNav";
import { v4 as uuidv4 } from "uuid";
import {
  getSessions,
  createSession,
  updateSession,
  deleteSession,
} from "./lib/api";

export interface ChatMessage {
  id: number;
  content: string;
  role: 0 | 1; // 0 = assistant, 1 = user
  timestamp: number;
  intent?: string;
  toolUsed?: string;
  isError?: boolean;
}

export interface Chat {
  id: string;
  title: string;
  timestamp: number;
  messageCount?: number;
  messages: ChatMessage[];
}

const userId = "junior";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const initialized = useRef(false);

  // ── Load sessions from backend ──────────────────────────
  const loadSessions = useCallback(async () => {
    try {
      const sessions = await getSessions(userId);
      const mapped: Chat[] = sessions.map((s) => ({
        id: s.id,
        title: s.title,
        timestamp: new Date(s.createdAt).getTime(),
        messageCount: s.messageCount,
        messages: [],
      }));
      setChats(mapped);
      if (mapped.length > 0) {
        setCurrentChatId(mapped[0].id);
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
      setChats([]);
    } finally {
      setSessionsLoaded(true);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // ── Mobile detection ────────────────────────────────────
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // ── Create first chat if none ───────────────────────────
  useEffect(() => {
    if (sessionsLoaded && !initialized.current && chats.length === 0) {
      initialized.current = true;
      handleNewChat();
    }
  }, [sessionsLoaded]);

  // ── CRUD (API-backed) ───────────────────────────────────
  const handleNewChat = useCallback(async () => {
    try {
      const session = await createSession(userId, "New Chat");
      const newChat: Chat = {
        id: session.id,
        title: session.title,
        timestamp: new Date(session.createdAt).getTime(),
        messageCount: 0,
        messages: [],
      };
      setChats((prev) => [newChat, ...prev]);
      setCurrentChatId(newChat.id);
      setSidebarOpen(false);
    } catch (err) {
      console.error("Failed to create session:", err);
      // Fallback: client-side only
      const fallbackId = uuidv4();
      setChats((prev) => [
        { id: fallbackId, title: "New Chat", timestamp: Date.now(), messageCount: 0, messages: [] },
        ...prev,
      ]);
      setCurrentChatId(fallbackId);
    }
  }, []);

  const handleDeleteChat = useCallback(async (id: string) => {
    try {
      await deleteSession(id);
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
    setChats((prev) => prev.filter((c) => c.id !== id));
    setCurrentChatId((prev) => (prev === id ? null : prev));
  }, []);

  const handleRenameChat = useCallback(async (id: string, newTitle: string) => {
    setChats((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c))
    );
    try {
      await updateSession(id, newTitle);
    } catch (err) {
      console.error("Failed to rename session:", err);
    }
  }, []);

  // ── Message sync ────────────────────────────────────────
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
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 min-w-0 relative">
        <TopNav
          onMenuClick={() => setSidebarOpen(true)}
          onNewChat={handleNewChat}
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
