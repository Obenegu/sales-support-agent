"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Sparkles,
  FileCheck,
  Database,
  ArrowUpToLine,
} from "lucide-react";

const ALLOWED_TYPES = [".pdf", ".html", ".htm", ".txt"];
const MAX_SIZE_MB = 20;

type Phase = "idle" | "uploading" | "ingesting" | "done" | "error";

interface ProgressState {
  phase: Phase;
  percent: number;          // 0–100
  message: string;
  details: string;
}

const phaseLabels: Record<Phase, { icon: React.ReactNode; label: string }> = {
  idle: { icon: <UploadCloud size={14} />, label: "Upload & Ingest" },
  uploading: { icon: <ArrowUpToLine size={14} className="animate-pulse" />, label: "Uploading…" },
  ingesting: { icon: <Database size={14} className="animate-pulse" />, label: "Ingesting…" },
  done: { icon: <FileCheck size={14} />, label: "Complete" },
  error: { icon: <XCircle size={14} />, label: "Failed" },
};

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState<ProgressState>({
    phase: "idle",
    percent: 0,
    message: "",
    details: "",
  });
  const xhrRef = useRef<XMLHttpRequest | null>(null);

  // Auto-dismiss done state after 6 seconds
  useEffect(() => {
    if (progress.phase === "done") {
      const t = setTimeout(() => {
        setProgress({ phase: "idle", percent: 0, message: "", details: "" });
        setFile(null);
      }, 6000);
      return () => clearTimeout(t);
    }
  }, [progress.phase]);

  const validateFile = (f: File): string | null => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_TYPES.includes(ext))
      return `Unsupported file type (${ext}). Allowed: PDF, HTML, TXT`;
    if (f.size > MAX_SIZE_MB * 1024 * 1024)
      return `File too large (max ${MAX_SIZE_MB}MB)`;
    return null;
  };

  const handleFile = useCallback((f: File) => {
    const err = validateFile(f);
    if (err) {
      setProgress({ phase: "error", percent: 0, message: err, details: "" });
      setFile(null);
      return;
    }
    setFile(f);
    setProgress({ phase: "idle", percent: 0, message: "", details: "" });
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const handleSubmit = () => {
    if (!file) return;
    xhrRef.current?.abort();

    const form = new FormData();
    form.append("file", file);
    form.append("businessId", "1");

    const xhr = new XMLHttpRequest();
    xhrRef.current = xhr;

    // ── Phase 1: Upload (0 → 50%) ──
    setProgress({
      phase: "uploading",
      percent: 0,
      message: "Sending file to server…",
      details: `0 / ${(file.size / 1024).toFixed(0)} KB`,
    });

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const uploadPct = Math.round((e.loaded / e.total) * 50); // 0→50% for upload
        setProgress({
          phase: "uploading",
          percent: uploadPct,
          message: "Sending file to server…",
          details: `${(e.loaded / 1024).toFixed(0)} / ${(e.total / 1024).toFixed(0)} KB`,
        });
      }
    });

    xhr.addEventListener("load", () => {
      // ── Phase 2: Ingestion (50 → 100%) ──
      setProgress({
        phase: "ingesting",
        percent: 50,
        message: "Ingesting — chunking, embedding, indexing…",
        details: "This may take a moment for large documents.",
      });

      // Simulate smooth progression while the orchestrator works
      // The real total time depends on file size → chunk count → embedding batch
      let ingestPct = 50;
      const interval = setInterval(() => {
        ingestPct += 3;
        if (ingestPct >= 95) {
          ingestPct = 95;
          clearInterval(interval);
        }
        setProgress({
          phase: "ingesting",
          percent: ingestPct,
          message: "Ingesting — chunking, embedding, indexing…",
          details: `${ingestPct - 50}% processed`,
        });
      }, 300);

      try {
        const data = JSON.parse(xhr.responseText);

        if (xhr.status >= 200 && xhr.status < 300) {
          clearInterval(interval);
          setProgress({
            phase: "done",
            percent: 100,
            message: `"${data.fileName || file.name}" ingested successfully.`,
            details: data.chunks
              ? `${data.chunks} chunks indexed`
              : "Document is now searchable.",
          });
        } else {
          clearInterval(interval);
          setProgress({
            phase: "error",
            percent: 100,
            message: data?.error || data?.title || "Upload failed.",
            details: data?.details || `Status ${xhr.status}`,
          });
        }
      } catch {
        clearInterval(interval);
        setProgress({
          phase: "error",
          percent: 100,
          message: "Invalid response from server.",
          details: "Check the server logs.",
        });
      }
    });

    xhr.addEventListener("error", () => {
      setProgress({
        phase: "error",
        percent: 0,
        message: "Network error — could not reach server.",
        details: "Verify the backend is running.",
      });
    });

    xhr.addEventListener("abort", () => {
      setProgress({ phase: "idle", percent: 0, message: "", details: "" });
    });

    xhr.open("POST", "/api/Documents/upload");
    xhr.send(form);
  };

  const handleCancel = () => {
    xhrRef.current?.abort();
    setProgress({ phase: "idle", percent: 0, message: "", details: "" });
  };

  const isActive = progress.phase === "uploading" || progress.phase === "ingesting";
  const barColor =
    progress.phase === "done"
      ? "bg-emerald-500"
      : progress.phase === "error"
      ? "bg-red-500"
      : "bg-[var(--accent)]";

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col">
      {/* Header */}
      <header className="h-14 border-b border-[var(--border-color)] flex items-center px-4 gap-3 shrink-0">
        <button
          onClick={() => router.push("/")}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors text-[var(--text-secondary)] hover:text-white"
        >
          <ArrowLeft size={18} />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br from-indigo-600 to-indigo-500">
            <Sparkles size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-white">
            Upload Documents
          </span>
        </div>
      </header>

      {/* Body */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-lg">
          {/* Drop zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`relative flex flex-col items-center justify-center gap-3 p-10 rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer
              ${
                dragOver
                  ? "border-[var(--accent)] bg-[var(--accent)]/5"
                  : "border-[var(--border-color)] hover:border-[var(--text-muted)] bg-[var(--bg-secondary)]"
              }
              ${file && !isActive ? "pb-6" : "py-14"}`}
            onClick={() => {
              if (!isActive) document.getElementById("file-input")?.click();
            }}
          >
            <input
              id="file-input"
              type="file"
              accept=".pdf,.html,.htm,.txt"
              className="hidden"
              disabled={isActive}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />

            {file ? (
              <div className="flex items-center gap-3 w-full">
                <div className="w-10 h-10 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center shrink-0">
                  <FileText size={20} className="text-[var(--accent)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium truncate">
                    {file.name}
                  </p>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                {!isActive && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      setProgress({ phase: "idle", percent: 0, message: "", details: "" });
                    }}
                    className="p-1.5 rounded-lg hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-400 transition-colors"
                  >
                    <XCircle size={18} />
                  </button>
                )}
              </div>
            ) : (
              <>
                <UploadCloud size={40} className="text-[var(--text-muted)]" />
                <p className="text-sm text-[var(--text-secondary)] text-center">
                  Drag & drop a file here, or{" "}
                  <span className="text-[var(--accent)] font-medium">
                    click to browse
                  </span>
                </p>
              </>
            )}
          </div>

          {/* Supported formats hint */}
          <p className="text-[11px] text-[var(--text-muted)] text-center mt-3">
            Supported: PDF, HTML, TXT — up to {MAX_SIZE_MB}MB
          </p>

          {/* ── Progress Bar ─────────────────────────────────────────── */}
          {isActive && (
            <div className="mt-5 animate-fade-in">
              {/* Bar track */}
              <div className="relative h-3 rounded-full bg-[var(--bg-secondary)] border border-[var(--border-color)] overflow-hidden">
                <div
                  className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out ${barColor} ${
                    progress.phase === "ingesting" ? "animate-pulse" : ""
                  }`}
                  style={{
                    width: `${progress.percent}%`,
                    backgroundImage:
                      progress.phase === "uploading"
                        ? `linear-gradient(90deg, var(--accent), #818cf8)`
                        : undefined,
                  }}
                />
                {/* Shimmer on top */}
                {(progress.phase === "uploading" || progress.phase === "ingesting") && (
                  <div
                    className="absolute inset-y-0 w-[30%] rounded-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"
                  />
                )}
              </div>

              {/* Phase + detail text */}
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-[var(--text-secondary)]">
                  {progress.message}
                </p>
                <p className="text-[11px] text-[var(--text-muted)] tabular-nums">
                  {progress.percent}%
                </p>
              </div>
              {progress.details && (
                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                  {progress.details}
                </p>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div className="mt-6">
            {isActive ? (
              <button
                onClick={handleCancel}
                className="w-full py-2.5 rounded-xl text-sm font-medium border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-all"
              >
                Cancel
              </button>
            ) : progress.phase === "done" ? (
              <div className="flex items-center gap-3 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 animate-fade-in">
                <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-emerald-400 font-medium">
                    {progress.message}
                  </p>
                  {progress.details && (
                    <p className="text-[11px] text-emerald-500/70 mt-0.5">
                      {progress.details}
                    </p>
                  )}
                </div>
              </div>
            ) : progress.phase === "error" ? (
              <div className="flex items-start gap-3 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 animate-fade-in">
                <XCircle size={18} className="text-red-400 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-red-400 font-medium">
                    {progress.message}
                  </p>
                  {progress.details && (
                    <p className="text-[11px] text-red-500/70 mt-0.5">
                      {progress.details}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!file}
                className={`w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl text-sm font-semibold transition-all duration-200
                  ${
                    file
                      ? "bg-[var(--accent)] text-white hover:bg-[var(--accent)]/90 active:scale-[0.98]"
                      : "bg-[var(--bg-secondary)] text-[var(--text-muted)] border border-[var(--border-color)] cursor-not-allowed"
                  }`}
              >
                <UploadCloud size={16} />
                Upload & Ingest
              </button>
            )}
          </div>

          {/* Step indicator (visible while uploading/ingesting) */}
          {isActive && (
            <div className="flex items-center gap-2 mt-4 px-1">
              {(["uploading", "ingesting", "done"] as Phase[]).map((step, i) => {
                const stepIdx = {
                  uploading: 0,
                  ingesting: 1,
                  done: 2,
                  error: -1,
                  idle: -1,
                };
                const current = stepIdx[progress.phase] ?? -1;
                const filled = current > i;
                const active = current === i;

                return (
                  <div key={step} className="flex items-center gap-2 flex-1">
                    <div className="flex items-center gap-1.5">
                      <div
                        className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-300
                          ${
                            filled
                              ? "bg-emerald-500 text-white"
                              : active
                              ? "bg-[var(--accent)] text-white"
                              : "bg-[var(--bg-secondary)] border border-[var(--border-color)] text-[var(--text-muted)]"
                          }`}
                      >
                        {filled ? "✓" : i + 1}
                      </div>
                      <span
                        className={`text-[11px] ${
                          active
                            ? "text-white font-medium"
                            : "text-[var(--text-muted)]"
                        }`}
                      >
                        {i === 0 ? "Upload" : i === 1 ? "Ingest" : "Done"}
                      </span>
                    </div>
                    {i < 2 && (
                      <div className="flex-1 h-px bg-[var(--border-color)]" />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
