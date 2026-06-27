"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Loader2, Sparkles, ArrowDown } from "lucide-react";
import { sendMessage } from "../lib/api";
import type { ChatMessage } from "../page";

interface ChatAreaProps {
  chatId: string | null;
  messages: ChatMessage[];
  onAppendMessage: (chatId: string, message: ChatMessage) => void;
  onUpdateMessages: (chatId: string, messages: ChatMessage[]) => void;
  isMobile: boolean;
}

export default function ChatArea({
  chatId,
  messages,
  onAppendMessage,
  onUpdateMessages,
  isMobile,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const userId = "junior";

  // Auto-scroll to bottom
  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  }, []);

  useEffect(() => {
    const timer = requestAnimationFrame(() => {
      scrollToBottom(messages.length === 0 ? "auto" : "smooth");
    });
    return () => cancelAnimationFrame(timer);
  }, [messages.length, scrollToBottom]);

  // Show/hide scroll button
  const handleScroll = useCallback(() => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 150);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [input]);

  const handleSend = async () => {
    if (!input.trim() || loading || !chatId) return;

    const userMsg: ChatMessage = {
      id: Date.now(),
      content: input.trim(),
      role: 1,
      timestamp: Date.now(),
    };

    onAppendMessage(chatId, userMsg);

    requestAnimationFrame(() => {
      setInput("");
      if (textareaRef.current) textareaRef.current.style.height = "auto";
    });

    setLoading(true);

    try {
      const payload = {
        message: userMsg.content,
        userId,
        sessionId: chatId,
        role: 1,
      };

      const response = await sendMessage(payload);

      const botMsg: ChatMessage = {
        id: Date.now() + 1,
        content:
          response?.response ??
          response?.Response ??
          "I'm sorry, I couldn't process that.",
        role: 0,
        timestamp: Date.now(),
        intent: response?.intent ?? response?.Intent,
        toolUsed: response?.tool_used ?? response?.ToolUsed,
      };

      onAppendMessage(chatId, botMsg);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        content: "Sorry, something went wrong. Please try again.",
        role: 0,
        timestamp: Date.now(),
        isError: true,
      };
      onAppendMessage(chatId, errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderMarkdown = (text: string) => {
    if (!text) return "";
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(
        /```([\s\S]*?)```/g,
        '<pre class="code-block"><code>$1</code></pre>'
      )
      .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      .replace(/\n/g, "<br/>");
    return html;
  };

  const suggestions = [
    "What products do you offer?",
    "Help me track an order",
    "I need support assistance",
    "Show me sales analytics",
  ];

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages Area */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-3xl mx-auto px-4 py-6 md:px-6 lg:px-8">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] animate-fade-in">
              <div className="w-16 h-16 md:w-20 md:h-20 rounded-2xl flex items-center justify-center mb-6 bg-[var(--accent-light)]">
                <Sparkles size={32} className="text-[var(--accent)]" />
              </div>
              <h2 className="text-2xl md:text-3xl font-semibold mb-3 text-white text-center">
                How can I help you today?
              </h2>
              <p className="text-sm md:text-base max-w-md text-center text-[var(--text-secondary)] mb-8">
                Ask me anything about sales, support, products, or services
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion);
                      textareaRef.current?.focus();
                    }}
                    className="px-4 py-3 rounded-xl text-sm text-left transition-all duration-200 hover:bg-[var(--bg-tertiary)] bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:border-[var(--accent)]/30"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6 md:space-y-8 mt-8">
              {messages.map((msg, index) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 md:gap-4 group ${
                    msg.role === 1 ? "flex-row-reverse" : "flex-row"
                  }`}
                  style={{
                    animationDelay:
                      index < messages.length - 2
                        ? "0s"
                        : `${(messages.length - index - 1) * 0.08}s`,
                  }}
                >
                  {/* Avatar */}
                  <div
                    className={`w-8 h-8 md:w-9 md:h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                      msg.role === 1
                        ? "bg-[var(--accent)] text-white"
                        : "bg-[var(--accent-light)] text-[var(--accent)]"
                    }`}
                  >
                    {msg.role === 1 ? (
                      <User size={18} />
                    ) : (
                      <Bot size={18} />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className="flex-1 min-w-0 space-y-1">
                    <div
                      className={`text-xs font-medium ${
                        msg.role === 1
                          ? "text-right text-[var(--text-secondary)]"
                          : "text-left text-[var(--text-secondary)]"
                      }`}
                    >
                      {msg.role === 1 ? "You" : "Genuka AI"}
                    </div>
                    <div
                      className={`text-sm md:text-base leading-relaxed ${
                        msg.role === 1
                          ? "text-[var(--text-primary)]"
                          : msg.isError
                          ? "text-red-400"
                          : "text-[var(--text-primary)]"
                      }`}
                    >
                      {msg.role === 0 ? (
                        <div
                          className="prose prose-invert prose-sm md:prose-base max-w-none"
                          dangerouslySetInnerHTML={{
                            __html: renderMarkdown(msg.content),
                          }}
                        />
                      ) : (
                        <p className={msg.role === 1 ? "text-right" : ""}>
                          {msg.content}
                        </p>
                      )}
                    </div>
                    {msg.intent && (
                      <div
                        className={`flex ${
                          msg.role === 1 ? "justify-end" : "justify-start"
                        }`}
                      >
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-[var(--accent-light)] text-[var(--accent)] mt-1">
                          {msg.intent}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {loading && (
                <div className="flex gap-3 md:gap-4 animate-fade-in">
                  <div className="w-8 h-8 md:w-9 md:h-9 rounded-full flex items-center justify-center flex-shrink-0 bg-[var(--accent-light)] text-[var(--accent)]">
                    <Bot size={18} />
                  </div>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="text-xs font-medium text-left text-[var(--text-secondary)]">
                      Genuka AI
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollBtn && (
        <button
          onClick={() => scrollToBottom()}
          className="fixed bottom-28 md:bottom-32 left-1/2 -translate-x-1/2 w-10 h-10 rounded-full flex items-center justify-center z-10 animate-fade-in bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-white hover:border-[var(--accent)] transition-colors shadow-xl"
        >
          <ArrowDown size={18} />
        </button>
      )}

      {/* Input Area */}
      <div className="sticky bottom-0 border-t border-[var(--border-color)] bg-gradient-to-t from-[var(--bg-primary)] to-transparent backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-4 py-4 md:px-6 lg:px-8">
          <div className="flex items-end gap-2 md:gap-3 p-2 md:p-3 rounded-2xl md:rounded-3xl bg-[var(--bg-secondary)] border border-[var(--border-color)] focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_rgba(99,102,241,0.15)] transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Genuka AI..."
              rows={1}
              disabled={loading || !chatId}
              className="flex-1 bg-transparent text-sm md:text-base text-white placeholder-white/40 outline-none resize-none py-2 px-2 min-h-[24px] max-h-[200px] disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || !chatId}
              className="w-8 h-8 md:w-9 md:h-9 rounded-lg md:rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed enabled:hover:scale-105 enabled:active:scale-95"
              style={{
                background:
                  input.trim() && !loading && chatId
                    ? "var(--accent)"
                    : "transparent",
                color:
                  input.trim() && !loading && chatId ? "#fff" : "var(--text-muted)",
              }}
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
          <p className="text-center text-[10px] md:text-[11px] mt-2 text-[var(--text-muted)]">
            Genuka AI can make mistakes. Check important info.
          </p>
        </div>
      </div>
    </div>
  );
}
