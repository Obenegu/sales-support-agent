"use client";

import { Menu, X, Sparkles } from "lucide-react";

interface MobileHeaderProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

export default function MobileHeader({
  onMenuClick,
  sidebarOpen,
}: MobileHeaderProps) {
  return (
    <div
      className="md:hidden flex items-center gap-3 px-4"
      style={{
        height: "var(--header-height)",
        borderBottom: "1px solid var(--border-color)",
        background: "var(--bg-primary)",
      }}
    >
      <button
        onClick={onMenuClick}
        className="w-10 h-10 rounded-xl flex items-center justify-center transition-colors"
        style={{ background: "var(--bg-tertiary)" }}
      >
        {sidebarOpen ? (
          <X size={20} style={{ color: "var(--text-secondary)" }} />
        ) : (
          <Menu size={20} style={{ color: "var(--text-secondary)" }} />
        )}
      </button>
      <div className="flex items-center gap-2">
        <Sparkles size={18} style={{ color: "var(--accent)" }} />
        <span className="text-sm font-semibold text-white">Genuka AI</span>
      </div>
    </div>
  );
}
