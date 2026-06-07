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
  Calendar,
  MessageSquare,
} from "lucide-react";
import Link from "next/link";
import { BACKEND_URL } from "../../config";

// ====================================================
// MOCK DATA FOR CALL DETAIL
// ====================================================
function getMockCallDetail(id: string) {
  return {
    id,
    name: "Sarah Connor",
    company: "Cyberdyne Systems",
    phone: "+15017122661",
    status: "completed",
    duration_seconds: 154,
    recording_url: "/recordings/recording_latest.wav",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    fsm_states: ["INITIATION", "GREETING", "QUALIFICATION", "BOOKING", "COMPLETE"],
    transcript: [
      { speaker: "AI" as const, text: "Hi Sarah, this is Alex from CloudScale. How are you doing today?", timestamp: "00:02" },
      { speaker: "Prospect" as const, text: "Hi Alex, I'm doing well. What's this about?", timestamp: "00:08" },
      { speaker: "AI" as const, text: "We help fast-growing teams automate their outbound calling. Are you currently using any solution for that?", timestamp: "00:14" },
      { speaker: "Prospect" as const, text: "We've been looking at a few options but haven't committed to anything yet.", timestamp: "00:23" },
      { speaker: "AI" as const, text: "That's great timing. Our platform has increased booking rates by 40% for similar teams. Would you be open to a quick 15-minute demo?", timestamp: "00:32" },
      { speaker: "Prospect" as const, text: "Sure, that sounds interesting. What times work?", timestamp: "00:41" },
      { speaker: "AI" as const, text: "I have Tuesday at 10 AM or Wednesday at 2 PM available. Which works better for you?", timestamp: "00:47" },
      { speaker: "Prospect" as const, text: "Tuesday at 10 works perfectly.", timestamp: "00:53" },
      { speaker: "AI" as const, text: "Excellent! I'll send you a calendar invite right away. Thanks for your time, Sarah!", timestamp: "00:58" },
      { speaker: "Prospect" as const, text: "Thank you, Alex. Talk soon!", timestamp: "01:04" },
    ],
    ai_summary: {
      key_facts: [
        "Lead is evaluating multiple outbound solutions",
        "No current committed platform",
        "Team is fast-growing",
        "Interested in automation capabilities",
      ],
      objections: ["None raised during this call"],
      sentiment: "Positive — engaged and receptive",
      next_action: "Send calendar invite for Tuesday 10 AM demo",
      outcome: "Demo booked successfully",
    },
  };
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
          onClick={togglePlay}
          className="w-12 h-12 rounded-full flex items-center justify-center transition-all"
          style={{
            background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          {isPlaying ? <Pause className="w-5 h-5 text-white" /> : <Play className="w-5 h-5 text-white translate-x-[1px]" />}
        </button>
        <div className="flex-1">
          {/* Waveform placeholder bar */}
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
            {/* Visual waveform bars */}
            <div className="absolute inset-0 flex items-center justify-around px-1">
              {Array.from({ length: 60 }).map((_, i) => {
                const height = 10 + Math.sin(i * 0.8) * 10 + Math.random() * 8;
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
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    setMounted(true);
    params.then((p) => setCallId(p.id));
  }, [params]);

  const call = useMemo(() => getMockCallDetail(callId || "call_1"), [callId]);

  const filteredTranscript = useMemo(() => {
    if (!searchQuery) return call.transcript;
    return call.transcript.filter((t) =>
      t.text.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [call.transcript, searchQuery]);

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto space-y-6">
      {/* Back nav */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm transition-colors"
        style={{ color: "hsl(var(--text-secondary))" }}
      >
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Call with {call.name}
          </h1>
          <p className="text-sm mt-0.5 flex items-center gap-2" style={{ color: "hsl(var(--text-muted))" }}>
            <Clock className="w-3.5 h-3.5" />
            {Math.floor(call.duration_seconds / 60)}m {call.duration_seconds % 60}s ·{" "}
            {call.company} · {call.phone}
          </p>
        </div>
        <span
          className="px-3 py-1 rounded-full text-xs font-semibold uppercase"
          style={{ background: "hsla(142, 71%, 45%, 0.1)", color: "#22c55e" }}
        >
          {call.status}
        </span>
      </div>

      {/* Audio Player */}
      <AudioPlayer src={call.recording_url || ""} />

      {/* FSM State Timeline */}
      <div
        className="rounded-xl p-5 border"
        style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
      >
        <h2 className="text-sm font-semibold mb-4" style={{ color: "hsl(var(--text-primary))" }}>
          Call Flow
        </h2>
        <div className="flex items-center gap-0 overflow-x-auto">
          {call.fsm_states.map((state, i) => (
            <React.Fragment key={state}>
              <div className="flex flex-col items-center flex-shrink-0">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold"
                  style={{
                    background: i === call.fsm_states.length - 1
                      ? "hsla(142, 71%, 45%, 0.15)"
                      : "hsl(var(--surface-3))",
                    color: i === call.fsm_states.length - 1 ? "#22c55e" : "hsl(var(--text-secondary))",
                  }}
                >
                  {i + 1}
                </div>
                <span className="text-[10px] mt-1.5 font-medium whitespace-nowrap" style={{ color: "hsl(var(--text-muted))" }}>
                  {state.replace(/_/g, " ")}
                </span>
              </div>
              {i < call.fsm_states.length - 1 && (
                <div className="flex-1 min-w-[30px] h-[2px] mx-1" style={{ background: "hsl(var(--surface-3))" }} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

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
                type="text"
                placeholder="Search..."
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
                  <span className="text-[10px] mt-1 block" style={{ color: "hsl(var(--text-muted))" }}>
                    {turn.timestamp}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Summary — 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          <div
            className="rounded-xl border p-5"
            style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
          >
            <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
              AI Summary
            </h2>
            <div className="space-y-3">
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
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                  Sentiment
                </p>
                <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>
                  {call.ai_summary.sentiment}
                </span>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                  Next Action
                </p>
                <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>
                  {call.ai_summary.next_action}
                </span>
              </div>
            </div>
          </div>

          <div
            className="rounded-xl border p-5"
            style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
          >
            <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
              Key Facts
            </h2>
            <ul className="space-y-2">
              {call.ai_summary.key_facts.map((fact, i) => (
                <li key={i} className="flex items-start gap-2">
                  <TrendingUp className="w-3.5 h-3.5 mt-0.5 text-emerald-400 flex-shrink-0" />
                  <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>{fact}</span>
                </li>
              ))}
            </ul>
          </div>

          <div
            className="rounded-xl border p-5"
            style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
          >
            <h2 className="text-sm font-semibold mb-3" style={{ color: "hsl(var(--text-primary))" }}>
              Objections
            </h2>
            <ul className="space-y-2">
              {call.ai_summary.objections.map((obj, i) => (
                <li key={i} className="flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 text-amber-400 flex-shrink-0" />
                  <span className="text-[13px]" style={{ color: "hsl(var(--text-secondary))" }}>{obj}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
