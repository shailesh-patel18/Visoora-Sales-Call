"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  Play,
  Pause,
  Search,
  ArrowLeft,
  Clock,
  User,
  Bot,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { BACKEND_URL } from "../../config";

// ====================================================
// TYPES
// ====================================================
interface TranscriptTurn {
  speaker: "AI" | "Prospect" | "agent" | "agent_filler" | "prospect";
  text: string;
  timestamp?: string;
}

interface CallDetail {
  id: string;
  phone_number?: string;
  // Legacy enrichment fields (optional, for backward-compat with local fallback)
  name?: string;
  company?: string;
  status?: string;
  duration_seconds: number;
  recording_url?: string | null;
  created_at: string;
  final_state?: string;
  fsm_states?: string[];
  transcript?: TranscriptTurn[] | string;
  ai_summary?: {
    key_facts?: string[];
    objections?: string[];
    sentiment?: string;
    next_action?: string;
    outcome?: string;
  };
}

function normaliseSpeaker(s: string): "AI" | "Prospect" {
  const lower = (s || "").toLowerCase();
  if (lower.startsWith("agent") || lower === "ai") return "AI";
  return "Prospect";
}

function normaliseTranscript(raw: TranscriptTurn[] | string | undefined): Array<{ speaker: "AI" | "Prospect"; text: string; timestamp: string }> {
  if (!raw) return [];
  if (typeof raw === "string") {
    try {
      raw = JSON.parse(raw);
    } catch {
      // If it's a plain text blob, wrap it as a single Prospect turn
      return [{ speaker: "Prospect", text: raw, timestamp: "" }];
    }
  }
  if (!Array.isArray(raw)) return [];
  return raw.map((t, i) => ({
    speaker: normaliseSpeaker(t.speaker as string),
    text: t.text || "",
    timestamp: t.timestamp ?? `00:${String(i * 3).padStart(2, "0")}`,
  }));
}

function mapStateLabel(state: string): string {
  return (state || "Unknown").replace(/_/g, " ");
}

// ====================================================
// AUDIO PLAYER
// ====================================================
function AudioPlayer({ src }: { src: string }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) audioRef.current.pause();
    else audioRef.current.play().catch(() => {});
    setIsPlaying(!isPlaying);
  };

  const formatTime = (t: number) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const absoluteSrc = src.startsWith("/recordings") ? `${BACKEND_URL}${src}` : src;

  return (
    <div
      className="rounded-xl p-4 border"
      style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}
    >
      <audio
        ref={audioRef}
        src={absoluteSrc}
        onTimeUpdate={() => audioRef.current && setCurrentTime(audioRef.current.currentTime)}
        onLoadedMetadata={() => audioRef.current && setDuration(audioRef.current.duration)}
        onEnded={() => setIsPlaying(false)}
      />
      <div className="flex items-center gap-4">
        <button
          id="audio-play-btn"
          onClick={togglePlay}
          className="w-12 h-12 rounded-full flex items-center justify-center transition-all"
          style={{
            background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          {isPlaying ? <Pause className="w-5 h-5 text-white" /> : <Play className="w-5 h-5 text-white translate-x-[1px]" />}
        </button>
        <div className="flex-1">
          <div className="relative h-10 rounded-lg overflow-hidden" style={{ background: "hsl(var(--surface-3))" }}>
            <div
              className="absolute inset-y-0 left-0 rounded-lg opacity-30"
              style={{
                width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`,
                background: "linear-gradient(90deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            />
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={(e) => {
                const v = parseFloat(e.target.value);
                if (audioRef.current) { audioRef.current.currentTime = v; setCurrentTime(v); }
              }}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="absolute inset-0 flex items-center justify-around px-1">
              {Array.from({ length: 60 }).map((_, i) => {
                const height = 10 + Math.sin(i * 0.8) * 10 + (i % 3) * 2;
                const played = duration > 0 && (i / 60) <= (currentTime / duration);
                return (
                  <div
                    key={i}
                    className="w-[2px] rounded-full transition-colors"
                    style={{
                      height: `${height}px`,
                      background: played ? "hsl(var(--brand-primary))" : "hsl(var(--surface-3))",
                      opacity: played ? 1 : 0.4,
                    }}
                  />
                );
              })}
            </div>
          </div>
          <div className="flex justify-between mt-1.5 text-[11px] font-mono" style={{ color: "hsl(var(--text-muted))" }}>
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ====================================================
// CALL DETAIL PAGE
// ====================================================
export default function CallDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const [callId, setCallId] = useState<string>("");
  const [mounted, setMounted] = useState(false);
  const [call, setCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Resolve dynamic route param
  useEffect(() => {
    setMounted(true);
    params.then((p) => setCallId(p.id));
  }, [params]);

  // Fetch call detail when callId is resolved
  useEffect(() => {
    if (!callId) return;
    let cancelled = false;

    async function loadCall() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${BACKEND_URL}/api/analytics/calls/${encodeURIComponent(callId)}`, {
          credentials: "include",
        });
        if (!res.ok) {
          if (res.status === 404) throw new Error("Call record not found");
          throw new Error(`Server responded ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) setCall(data.call ?? data);
      } catch (err: unknown) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load call detail");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadCall();
    return () => { cancelled = true; };
  }, [callId]);

  const transcript = useMemo(() => normaliseTranscript(call?.transcript), [call]);

  const filteredTranscript = useMemo(() => {
    if (!searchQuery) return transcript;
    return transcript.filter((t) =>
      t.text.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [transcript, searchQuery]);

  const fsmStates = useMemo(() => {
    if (call?.fsm_states && call.fsm_states.length > 0) return call.fsm_states;
    if (call?.final_state) return [call.final_state];
    return [];
  }, [call]);

  if (!mounted) return null;

  // Loading state
  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-[1200px] mx-auto flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2
            className="w-8 h-8 animate-spin"
            style={{ color: "hsl(var(--brand-primary))" }}
          />
          <p className="text-sm" style={{ color: "hsl(var(--text-muted))" }}>
            Loading call record…
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6 lg:p-8 max-w-[1200px] mx-auto space-y-6">
        <Link
          href="/calls"
          className="inline-flex items-center gap-1.5 text-sm transition-colors"
          style={{ color: "hsl(var(--text-secondary))" }}
        >
          <ArrowLeft className="w-4 h-4" /> Back to Call History
        </Link>
        <div
          className="rounded-xl border p-8 flex flex-col items-center gap-4 text-center"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <AlertCircle className="w-10 h-10 text-red-400" />
          <div>
            <p className="text-base font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
              Could not load call
            </p>
            <p className="text-sm mt-1" style={{ color: "hsl(var(--text-muted))" }}>
              {error}
            </p>
          </div>
          <button
            id="call-detail-retry-btn"
            onClick={() => {
              setError(null);
              setLoading(true);
              // Retrigger by toggling callId momentarily
              const id = callId;
              setCallId("");
              setTimeout(() => setCallId(id), 10);
            }}
            className="inline-flex items-center gap-1.5 text-sm px-4 py-2 rounded-lg border transition-colors"
            style={{
              borderColor: "hsl(var(--border-subtle))",
              color: "hsl(var(--brand-primary))",
              background: "hsl(var(--surface-2))",
            }}
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      </div>
    );
  }

  if (!call) return null;

  const displayName = call.name ?? call.phone_number ?? "Unknown";
  const displayStatus = call.final_state ?? call.status ?? "Unknown";

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto space-y-6">
      {/* Back nav */}
      <Link
        href="/calls"
        className="inline-flex items-center gap-1.5 text-sm transition-colors"
        style={{ color: "hsl(var(--text-secondary))" }}
      >
        <ArrowLeft className="w-4 h-4" /> Back to Call History
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Call with {displayName}
          </h1>
          <p className="text-sm mt-0.5 flex items-center gap-2" style={{ color: "hsl(var(--text-muted))" }}>
            <Clock className="w-3.5 h-3.5" />
            {Math.floor((call.duration_seconds || 0) / 60)}m{" "}
            {(call.duration_seconds || 0) % 60}s
            {call.company && ` · ${call.company}`}
            {call.phone_number && ` · ${call.phone_number}`}
          </p>
        </div>
        <span
          className="px-3 py-1 rounded-full text-xs font-semibold uppercase"
          style={{ background: "hsla(142, 71%, 45%, 0.1)", color: "#22c55e" }}
        >
          {mapStateLabel(displayStatus)}
        </span>
      </div>

      {/* Audio Player */}
      {call.recording_url && <AudioPlayer src={call.recording_url} />}

      {/* FSM State Timeline */}
      {fsmStates.length > 0 && (
        <div
          className="rounded-xl p-5 border"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <h2 className="text-sm font-semibold mb-4" style={{ color: "hsl(var(--text-primary))" }}>
            Call Flow
          </h2>
          <div className="flex items-center gap-0 overflow-x-auto">
            {fsmStates.map((state, i) => (
              <React.Fragment key={state}>
                <div className="flex flex-col items-center flex-shrink-0">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold"
                    style={{
                      background: i === fsmStates.length - 1
                        ? "hsla(142, 71%, 45%, 0.15)"
                        : "hsl(var(--surface-3))",
                      color: i === fsmStates.length - 1 ? "#22c55e" : "hsl(var(--text-secondary))",
                    }}
                  >
                    {i + 1}
                  </div>
                  <span className="text-[10px] mt-1.5 font-medium whitespace-nowrap" style={{ color: "hsl(var(--text-muted))" }}>
                    {state.replace(/_/g, " ")}
                  </span>
                </div>
                {i < fsmStates.length - 1 && (
                  <div className="flex-1 min-w-[30px] h-[2px] mx-1" style={{ background: "hsl(var(--surface-3))" }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Transcript — 3 cols */}
        <div
          className="lg:col-span-3 rounded-xl border p-5"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
              Transcript
            </h2>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{ color: "hsl(var(--text-muted))" }} />
              <input
                id="transcript-search"
                type="text"
                placeholder="Search…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 rounded-lg text-[12px] border outline-none w-[160px]"
                style={{
                  background: "hsl(var(--surface-2))",
                  borderColor: "hsl(var(--border-subtle))",
                  color: "hsl(var(--text-primary))",
                }}
              />
            </div>
          </div>

          {transcript.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2">
              <p className="text-sm" style={{ color: "hsl(var(--text-muted))" }}>
                No transcript available for this call.
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {filteredTranscript.map((turn, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${turn.speaker === "AI" ? "" : "flex-row-reverse"}`}
                >
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{
                      background: turn.speaker === "AI" ? "hsla(168, 85%, 57%, 0.12)" : "hsla(262, 83%, 68%, 0.12)",
                      color: turn.speaker === "AI" ? "hsl(var(--brand-primary))" : "hsl(var(--brand-accent))",
                    }}
                  >
                    {turn.speaker === "AI" ? <Bot className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
                  </div>
                  <div
                    className={`rounded-lg p-3 max-w-[80%] ${turn.speaker === "AI" ? "" : "text-right"}`}
                    style={{ background: "hsl(var(--surface-2))" }}
                  >
                    <p className="text-[13px] leading-relaxed" style={{ color: "hsl(var(--text-primary))" }}>
                      {turn.text}
                    </p>
                    {turn.timestamp && (
                      <span className="text-[10px] mt-1 block" style={{ color: "hsl(var(--text-muted))" }}>
                        {turn.timestamp}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI Summary — 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          {call.ai_summary ? (
            <>
              <div
                className="rounded-xl border p-5"
                style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
              >
                <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
                  AI Summary
                </h2>
                <div className="space-y-3">
                  {call.ai_summary.outcome && (
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                        Outcome
                      </p>
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span className="text-[13px] font-medium" style={{ color: "hsl(var(--text-primary))" }}>
                          {call.ai_summary.outcome}
                        </span>
                      </div>
                    </div>
                  )}
                  {call.ai_summary.sentiment && (
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                        Sentiment
                      </p>
                      <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>
                        {call.ai_summary.sentiment}
                      </span>
                    </div>
                  )}
                  {call.ai_summary.next_action && (
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                        Next Action
                      </p>
                      <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>
                        {call.ai_summary.next_action}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {(call.ai_summary.key_facts?.length ?? 0) > 0 && (
                <div
                  className="rounded-xl border p-5"
                  style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
                >
                  <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
                    Key Facts
                  </h2>
                  <ul className="space-y-2">
                    {(call.ai_summary.key_facts ?? []).map((fact, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <TrendingUp className="w-3.5 h-3.5 mt-0.5 text-emerald-400 flex-shrink-0" />
                        <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {(call.ai_summary.objections?.length ?? 0) > 0 && (
                <div
                  className="rounded-xl border p-5"
                  style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
                >
                  <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
                    Objections
                  </h2>
                  <ul className="space-y-2">
                    {(call.ai_summary.objections ?? []).map((obj, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 mt-0.5 text-amber-400 flex-shrink-0" />
                        <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            /* Raw call metadata when no AI summary is available */
            <div
              className="rounded-xl border p-5"
              style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
            >
              <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
                Call Details
              </h2>
              <dl className="space-y-2.5">
                {[
                  ["Phone", call.phone_number],
                  ["Outcome", mapStateLabel(call.final_state ?? "")],
                  ["Duration", call.duration_seconds
                    ? `${Math.floor(call.duration_seconds / 60)}m ${call.duration_seconds % 60}s`
                    : "—"],
                  ["Date", new Date(call.created_at).toLocaleString()],
                ].map(([label, value]) => value && (
                  <div key={label as string} className="flex justify-between">
                    <dt className="text-[12px]" style={{ color: "hsl(var(--text-muted))" }}>{label}</dt>
                    <dd className="text-[12px] font-medium" style={{ color: "hsl(var(--text-primary))" }}>{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
