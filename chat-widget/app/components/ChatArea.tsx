"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  Trash2,
  ArrowDown,
} from "lucide-react";
import { sendMessage } from "../lib/api";

interface ChatMessage {
  id: number;
  content: string;
  role: "user" | "assistant";
  timestamp: number;
  intent?: string;
  toolUsed?: string;
  isError?: boolean;
}

interface Chat {
  id: string;
  title: string;
  timestamp: number;
  messages: ChatMessage[];
}

interface ChatAreaProps {
  chatId: string | null;
  chats: Chat[];
  onUpdateMessages: (chatId: string, messages: ChatMessage[]) => void;
  isMobile: boolean;
}

export default function ChatArea({
  chatId,
  chats,
  onUpdateMessages,
  isMobile,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const userId = "junior";
  const currentChat = chats.find((c) => c.id === chatId);

  useEffect(() => {
    if (chatId && currentChat) {
      if (currentChat.messages?.length > 0) {
        setMessages(currentChat.messages);
      } else {
        setMessages([]);
      }
    }
  }, [chatId, currentChat]);

  useEffect(() => {
    if (chatId) {
      onUpdateMessages(chatId, messages);
    }
  }, [messages]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleScroll = () => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 100);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now(),
      content: input.trim(),
      role: "user",
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        message: userMsg.content,
        userId,
        sessionId: chatId!,
        role: "user",
      };

      const response = await sendMessage(payload);

      const botMsg: ChatMessage = {
        id: Date.now() + 1,
        content:
          response.response ||
          response.Response ||
          "I'm sorry, I couldn't process that.",
        role: "assistant",
        timestamp: Date.now(),
        intent: response.intent || response.Intent,
        toolUsed: response.tool_used || response.ToolUsed,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        content: "Sorry, something went wrong. Please try again.",
        role: "assistant",
        timestamp: Date.now(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    if (chatId) onUpdateMessages(chatId, []);
  };

  const formatTime = (ts: number) => {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const renderMarkdown = (text: string) => {
    if (!text) return "";
    let html = text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(
        /```([\s\S]*?)```/g,
        '<pre class="code-block"><code>$1</code></pre>'
      )
      .replace(
        /`([^`]+)`/g,
        '<code class="inline-code">$1</code>'
      )
      .replace(/\n/g, "<br/>");
    return html;
  };

  return (
    <div
      className="flex flex-col h-full relative"
      style={{ background: "var(--bg-primary)" }}
    >
      {/* Messages Area */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-6 md:px-8"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full animate-fade-in">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: "var(--accent-light)" }}
            >
              <Sparkles size={32} style={{ color: "var(--accent)" }} />
            </div>
            <h2 className="text-2xl font-bold mb-2 text-white">
              How can I help you today?
            </h2>
            <p
              className="text-sm max-w-md text-center"
              style={{ color: "var(--text-secondary)" }}
            >
              Ask me anything about sales, support, products, or any questions
              you have. I'm here to assist!
            </p>
            <div className="flex flex-wrap gap-2 mt-8 justify-center">
              {[
                "What products do you offer?",
                "Help me track an order",
                "I need support assistance",
                "Show me sales analytics",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="px-4 py-2 rounded-xl text-sm transition-all duration-200 hover:scale-[1.02]"
                  style={{
                    background: "var(--bg-tertiary)",
                    color: "var(--text-secondary)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, index) => (
              <div
                key={msg.id || index}
                className="animate-message-pop message-hover"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div
                  className={`flex gap-3 ${
                    msg.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-1"
                    style={{
                      background:
                        msg.role === "user"
                          ? "var(--user-msg-bg)"
                          : "var(--accent-light)",
                    }}
                  >
                    {msg.role === "user" ? (
                      <User size={15} className="text-white" />
                    ) : (
                      <Bot size={15} style={{ color: "var(--accent)" }} />
                    )}
                  </div>

                  {/* Message Bubble */}
                  <div className="flex flex-col max-w-[80%] md:max-w-[75%]">
                    <div
                      className="px-4 py-3 rounded-2xl text-sm leading-relaxed"
                      style={{
                        background:
                          msg.role === "user"
                            ? "var(--user-msg-bg)"
                            : msg.isError
                            ? "rgba(239,68,68,0.15)"
                            : "var(--bot-msg-bg)",
                        color:
                          msg.role === "user"
                            ? "#fff"
                            : "var(--text-primary)",
                        border:
                          msg.role === "user"
                            ? "none"
                            : msg.isError
                            ? "1px solid rgba(239,68,68,0.3)"
                            : "1px solid var(--border-color)",
                      }}
                    >
                      {msg.role === "assistant" ? (
                        <div
                          className="prose prose-invert prose-sm max-w-none"
                          dangerouslySetInnerHTML={{
                            __html: renderMarkdown(msg.content),
                          }}
                        />
                      ) : (
                        <p>{msg.content}</p>
                      )}
                    </div>
                    <span
                      className="text-xs mt-1 px-1"
                      style={{
                        color: "var(--text-muted)",
                        alignSelf:
                          msg.role === "user"
                            ? "flex-end"
                            : "flex-start",
                      }}
                    >
                      {msg.intent && (
                        <span
                          className="mr-2 px-1.5 py-0.5 rounded text-[10px] font-medium"
                          style={{
                            background: "var(--accent-light)",
                            color: "var(--accent)",
                          }}
                        >
                          {msg.intent}
                        </span>
                      )}
                      {formatTime(msg.timestamp)}
                    </span>
                  </div>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex gap-3 animate-fade-in">
                <div
                  className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: "var(--accent-light)" }}
                >
                  <Bot size={15} style={{ color: "var(--accent)" }} />
                </div>
                <div
                  className="px-4 py-3 rounded-2xl flex items-center gap-1"
                  style={{
                    background: "var(--bot-msg-bg)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <span className="typing-dot" />
                  <span className="typing-dot" style={{ animationDelay: "0.2s" }} />
                  <span className="typing-dot" style={{ animationDelay: "0.4s" }} />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Scroll to bottom button */}
      {showScrollBtn && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-24 right-6 w-10 h-10 rounded-full flex items-center justify-center z-10 animate-fade-in"
          style={{
            background: "var(--bg-tertiary)",
            border: "1px solid var(--border-color)",
            color: "var(--text-secondary)",
          }}
        >
          <ArrowDown size={18} />
        </button>
      )}

      {/* Input Area */}
      <div
        className="px-4 py-4 md:px-8"
        style={{
          borderTop: "1px solid var(--border-color)",
          background: "var(--bg-primary)",
        }}
      >
        <div className="max-w-3xl mx-auto">
          {messages.length > 0 && (
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {messages.length} messages
              </p>
              <button
                onClick={clearChat}
                className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-lg transition-colors hover:bg-red-500/10"
                style={{ color: "var(--error)" }}
              >
                <Trash2 size={12} />
                Clear chat
              </button>
            </div>
          )}

          <div
            className="flex items-end gap-2 p-2 rounded-2xl transition-all duration-200 input-glow"
            style={{
              background: "var(--bg-input)",
              border: "1px solid var(--border-color)",
            }}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="flex-1 bg-transparent text-sm text-white placeholder-white/30 outline-none resize-none py-2.5 px-3 max-h-32"
              style={{ minHeight: "44px" }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
              style={{
                background:
                  input.trim() && !loading
                    ? "var(--user-msg-bg)"
                    : "transparent",
                color:
                  input.trim() && !loading
                    ? "#fff"
                    : "var(--text-muted)",
              }}
            >
              {loading ? (
                <Loader2
                  size={18}
                  className="animate-spin"
                  style={{ color: "var(--accent)" }}
                />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
          <p
            className="text-center text-xs mt-2"
            style={{ color: "var(--text-muted)" }}
          >
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
