"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  MessageSquarePlus,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
  Sparkles,
  FileUp,
} from "lucide-react";
import type { Chat } from "../page";

interface SidebarProps {
  chats: Chat[];
  loading?: boolean;
  currentChat: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  onRenameChat: (id: string, title: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({
  chats,
  loading,
  currentChat,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
  isOpen,
  onClose,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const startRename = (chat: Chat) => {
    setEditingId(chat.id);
    setEditTitle(chat.title);
  };

  const saveRename = (id: string) => {
    const trimmed = editTitle.trim();
    if (trimmed) onRenameChat(id, trimmed);
    setEditingId(null);
  };

  // Group chats by date
  const groupedChats = useMemo(() => {
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();
    const lastWeek = Date.now() - 7 * 86400000;

    return chats.reduce<Record<string, Chat[]>>((acc, chat) => {
      const chatDate = new Date(chat.timestamp).toDateString();
      let label: string;
      if (chatDate === today) label = "Today";
      else if (chatDate === yesterday) label = "Yesterday";
      else if (chat.timestamp > lastWeek) label = "Previous 7 Days";
      else label = "Older";

      if (!acc[label]) acc[label] = [];
      acc[label].push(chat);
      return acc;
    }, {});
  }, [chats]);

  return (
    <>
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-[260px] md:w-[280px] flex flex-col bg-[var(--bg-sidebar)] border-r border-[var(--border-color)] transform transition-transform duration-300 ease-out ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-14 px-3 border-b border-[var(--border-color)] shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br from-indigo-600 to-indigo-500">
              <Sparkles size={14} className="text-white" />
            </div>
            <span className="text-sm font-semibold text-white">Genuka AI</span>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-2 shrink-0 space-y-1">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-white transition-all duration-200 hover:bg-white/5 border border-[var(--border-color)] hover:border-[var(--accent)]/50"
          >
            <MessageSquarePlus size={16} />
            <span>New chat</span>
          </button>
          <Link
            href="/upload"
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-white transition-all duration-200 hover:bg-white/5 border border-[var(--border-color)] hover:border-[var(--accent)]/50"
            onClick={onClose}
          >
            <FileUp size={16} />
            <span>Upload documents</span>
          </Link>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto px-2 pb-4 min-h-0">
          {loading ? (
            <div className="px-1 pt-2 space-y-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="skeleton skeleton-sidebar"
                  style={{ animationDelay: `${i * 0.1}s`, width: `${70 + Math.random() * 25}%` }}
                />
              ))}
            </div>
          ) : chats.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <MessageSquare
                size={28}
                className="text-[var(--text-muted)] mb-2 opacity-30"
              />
              <p className="text-xs text-[var(--text-muted)]">No chats yet</p>
            </div>
          ) : (
            Object.entries(groupedChats).map(([label, groupChats]) => (
              <div key={label} className="mb-4">
                <p className="px-2 py-1.5 text-[11px] font-semibold text-[var(--text-muted)]">
                  {label}
                </p>
                {groupChats.map((chat) => (
                  <div
                    key={chat.id}
                    className="relative group"
                    onMouseEnter={() => setHoveredId(chat.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  >
                    {editingId === chat.id ? (
                      <div className="flex items-center gap-1 px-2 py-1.5 mx-1 rounded-lg bg-[var(--bg-tertiary)]">
                        <input
                          autoFocus
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") saveRename(chat.id);
                            if (e.key === "Escape") setEditingId(null);
                          }}
                          className="flex-1 bg-transparent text-xs text-white outline-none px-1 min-w-0"
                        />
                        <button
                          onClick={() => saveRename(chat.id)}
                          className="p-1 rounded hover:bg-white/10 text-green-400 shrink-0"
                        >
                          <Check size={12} />
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="p-1 rounded hover:bg-white/10 text-red-400 shrink-0"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => {
                          onSelectChat(chat.id);
                          onClose();
                        }}
                        className={`w-full flex items-center gap-2 px-2 py-2 mx-1 rounded-lg text-left transition-all duration-150 group/item relative ${
                          currentChat === chat.id
                            ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
                            : "text-[var(--text-secondary)] hover:bg-white/5"
                        }`}
                      >
                        <MessageSquare
                          size={14}
                          className={`flex-shrink-0 ${
                            currentChat === chat.id
                              ? "text-[var(--accent)]"
                              : "text-[var(--text-muted)]"
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs truncate font-medium block">
                            {chat.title || "New Chat"}
                          </span>
                          <span className="text-[10px] text-[var(--text-muted)] block">
                            {chat.messageCount ?? chat.messages?.length
                              ? `${chat.messageCount ?? chat.messages.length} messages`
                              : "No messages"}
                          </span>
                        </div>
                        {hoveredId === chat.id && (
                          <div className="flex items-center gap-0.5 shrink-0">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                startRename(chat);
                              }}
                              className="p-1 rounded hover:bg-white/10 text-[var(--text-muted)] hover:text-white"
                            >
                              <Edit2 size={12} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteChat(chat.id);
                              }}
                              className="p-1 rounded hover:bg-white/10 text-[var(--text-muted)] hover:text-red-400"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        )}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-[var(--border-color)] shrink-0">
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors">
            <div className="w-7 h-7 rounded-full flex items-center justify-center bg-[var(--accent-light)] shrink-0 text-[var(--accent)] text-xs font-bold">
              J
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">Junior</p>
              <p className="text-[10px] text-[var(--text-muted)]">Admin</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
