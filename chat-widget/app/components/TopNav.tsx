"use client";

import { Menu, Plus } from "lucide-react";

interface TopNavProps {
  onMenuClick: () => void;
  onNewChat: () => void;
  currentTitle: string;
}

export default function TopNav({ onMenuClick, onNewChat, currentTitle }: TopNavProps) {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-14 px-3 md:px-4 border-b border-[var(--border-color)] bg-[var(--bg-primary)] backdrop-blur-xl">
      <div className="flex items-center gap-2">
        <button
          onClick={onMenuClick}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors text-[var(--text-secondary)] hover:text-white"
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>
        <h1 className="text-sm md:text-base font-medium text-white truncate max-w-[200px] md:max-w-none">
          {currentTitle}
        </h1>
      </div>
      <button
        onClick={onNewChat}
        className="p-2 rounded-lg hover:bg-white/5 transition-colors text-[var(--text-secondary)] hover:text-white"
        aria-label="New chat"
      >
        <Plus size={20} />
      </button>
    </header>
  );
}
