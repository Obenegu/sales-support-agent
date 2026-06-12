"use client";

import { useState } from "react";
import {
  MessageSquarePlus,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
  Sparkles,
  User,
} from "lucide-react";

interface Chat {
  id: string;
  title: string;
  timestamp: number;
  messages: { role: string; content: string }[];
}

interface SidebarProps {
  chats: Chat[];
  currentChat: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  onRenameChat: (id: string, title: string) => void;
  isOpen: boolean;
  isMobile: boolean;
  onClose: () => void;
}

export default function Sidebar({
  chats,
  currentChat,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
  isOpen,
  isMobile,
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
    if (editTitle.trim()) onRenameChat(id, editTitle.trim());
    setEditingId(null);
  };

  const sidebarWidth = isMobile
    ? isOpen
      ? "280px"
      : "0px"
    : isOpen
    ? "280px"
    : "0px";

  // Group chats by date
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  const groupedChats = chats.reduce<Record<string, Chat[]>>((acc, chat) => {
    const chatDate = new Date(chat.timestamp).toDateString();
    let label: string;
    if (chatDate === today) label = "Today";
    else if (chatDate === yesterday) label = "Yesterday";
    else
      label = new Date(chat.timestamp).toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      });

    if (!acc[label]) acc[label] = [];
    acc[label].push(chat);
    return acc;
  }, {});

  return (
    <aside
      className="sidebar-transition flex flex-col h-full relative z-40"
      style={{
        width: sidebarWidth,
        minWidth: sidebarWidth,
        background: "var(--bg-sidebar)",
        borderRight: "1px solid var(--border-color)",
      }}
    >
      {/* Logo / Brand */}
      <div
        className="flex items-center gap-3 px-5 py-4"
        style={{
          height: "var(--header-height)",
          borderBottom: "1px solid var(--border-color)",
        }}
      >
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: "var(--user-msg-bg)" }}
        >
          <Sparkles size={18} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-sm font-semibold text-white truncate">Genuka AI</h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Sales & Support
          </p>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-3 py-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98]"
          style={{ background: "var(--user-msg-bg)" }}
        >
          <MessageSquarePlus size={18} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {Object.entries(groupedChats).map(([label, groupChats]) => (
          <div key={label} className="mb-3">
            <p
              className="px-3 py-2 text-xs font-medium uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
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
                  <div
                    className="flex items-center gap-1 px-2 py-1.5 mx-1 rounded-lg"
                    style={{ background: "var(--bg-tertiary)" }}
                  >
                    <input
                      autoFocus
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) =>
                        e.key === "Enter" && saveRename(chat.id)
                      }
                      className="flex-1 bg-transparent text-sm text-white outline-none px-1"
                    />
                    <button
                      onClick={() => saveRename(chat.id)}
                      className="p-1 rounded hover:bg-white/10"
                      style={{ color: "var(--success)" }}
                    >
                      <Check size={14} />
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="p-1 rounded hover:bg-white/10"
                      style={{ color: "var(--error)" }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      onSelectChat(chat.id);
                      if (isMobile) onClose();
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2.5 mx-1 rounded-xl text-left transition-all duration-200"
                    style={{
                      background:
                        currentChat === chat.id
                          ? "var(--bg-tertiary)"
                          : "transparent",
                      color:
                        currentChat === chat.id
                          ? "var(--text-primary)"
                          : "var(--text-secondary)",
                      border:
                        currentChat === chat.id
                          ? "1px solid rgba(99,102,241,0.2)"
                          : "1px solid transparent",
                    }}
                  >
                    <MessageSquare
                      size={16}
                      style={{
                        color:
                          currentChat === chat.id
                            ? "var(--accent)"
                            : "var(--text-muted)",
                      }}
                      className="flex-shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate font-medium">
                        {chat.title || "New Chat"}
                      </p>
                      <p
                        className="text-xs truncate"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {chat.messages?.length
                          ? `${chat.messages.length} messages`
                          : "No messages"}
                      </p>
                    </div>
                    {hoveredId === chat.id && (
                      <div className="flex items-center gap-0.5 animate-fade-in">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startRename(chat);
                          }}
                          className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                          style={{ color: "var(--text-muted)" }}
                        >
                          <Edit2 size={13} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteChat(chat.id);
                          }}
                          className="p-1.5 rounded-lg hover:bg-red-500/20 transition-colors"
                          style={{ color: "var(--error)" }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    )}
                  </button>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div
        className="px-4 py-3 flex items-center gap-3"
        style={{ borderTop: "1px solid var(--border-color)" }}
      >
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center"
          style={{ background: "var(--accent-light)" }}
        >
          <User size={14} style={{ color: "var(--accent)" }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">Junior</p>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Admin
          </p>
        </div>
      </div>
    </aside>
  );
}
