"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  ChevronRight,
  Search,
} from "lucide-react";

// ====================================================
// MOCK CALLS
// ====================================================
interface CallEntry {
  id: string;
  name: string;
  company: string;
  phone: string;
  direction: "inbound" | "outbound";
  status: "completed" | "no_answer" | "in_progress";
  duration_seconds: number;
  outcome: string;
  created_at: string;
}

function generateMockCalls(): CallEntry[] {
  const entries: CallEntry[] = [
    { id: "call_1", name: "Sarah Connor", company: "Cyberdyne Systems", phone: "+15017122661", direction: "outbound", status: "completed", duration_seconds: 154, outcome: "Demo booked", created_at: new Date(Date.now() - 3600000).toISOString() },
    { id: "call_2", name: "Tony Stark", company: "Stark Industries", phone: "+14155552671", direction: "outbound", status: "completed", duration_seconds: 246, outcome: "Interested — follow up", created_at: new Date(Date.now() - 7200000).toISOString() },
    { id: "call_3", name: "Incoming Caller", company: "Unknown", phone: "+919824457565", direction: "inbound", status: "completed", duration_seconds: 62, outcome: "Support request", created_at: new Date(Date.now() - 10800000).toISOString() },
    { id: "call_4", name: "Bruce Wayne", company: "Wayne Enterprises", phone: "+12125551234", direction: "outbound", status: "no_answer", duration_seconds: 0, outcome: "No answer", created_at: new Date(Date.now() - 14400000).toISOString() },
    { id: "call_5", name: "Diana Prince", company: "Themyscira Inc", phone: "+15551234567", direction: "outbound", status: "completed", duration_seconds: 189, outcome: "Callback requested", created_at: new Date(Date.now() - 18000000).toISOString() },
    { id: "call_6", name: "Steve Rogers", company: "Shield Corp", phone: "+15559876543", direction: "inbound", status: "completed", duration_seconds: 320, outcome: "Deal qualified", created_at: new Date(Date.now() - 21600000).toISOString() },
    { id: "call_7", name: "Natasha Romanoff", company: "Red Room LLC", phone: "+15553334444", direction: "outbound", status: "completed", duration_seconds: 95, outcome: "Not interested", created_at: new Date(Date.now() - 25200000).toISOString() },
    { id: "call_8", name: "Clark Kent", company: "Daily Planet", phone: "+15557778888", direction: "outbound", status: "completed", duration_seconds: 173, outcome: "Demo booked", created_at: new Date(Date.now() - 28800000).toISOString() },
  ];
  return entries;
}

function formatDuration(s: number): string {
  if (s === 0) return "—";
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}m ${sec}s`;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return `${Math.floor(diff / 60000)}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// ====================================================
// CALLS INDEX PAGE
// ====================================================
export default function CallsPage() {
  const [calls, setCalls] = useState<CallEntry[]>([]);
  const [search, setSearch] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setCalls(generateMockCalls());
  }, []);

  if (!mounted) return null;

  const filtered = calls.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.company.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>Call History</h1>
        <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>{calls.length} calls total</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
        <input
          type="text"
          placeholder="Search calls..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none"
          style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
        />
      </div>

      <div className="space-y-2">
        {filtered.map((call) => (
          <Link
            key={call.id}
            href={`/calls/${call.id}`}
            className="flex items-center gap-4 rounded-xl p-4 border transition-all hover:scale-[1.005] hover:shadow-lg"
            style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              style={{
                background: call.direction === "inbound" ? "hsla(168, 85%, 57%, 0.1)" : "hsla(262, 83%, 68%, 0.1)",
                color: call.direction === "inbound" ? "hsl(var(--brand-primary))" : "hsl(var(--brand-accent))",
              }}
            >
              {call.direction === "inbound" ? <PhoneIncoming className="w-4 h-4" /> : <PhoneOutgoing className="w-4 h-4" />}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-[13px] font-medium truncate" style={{ color: "hsl(var(--text-primary))" }}>{call.name}</p>
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                  style={{
                    background: call.status === "completed" ? "hsla(142,71%,45%,0.1)" : call.status === "no_answer" ? "hsla(0,84%,60%,0.1)" : "hsla(38,92%,50%,0.1)",
                    color: call.status === "completed" ? "#22c55e" : call.status === "no_answer" ? "#ef4444" : "#f59e0b",
                  }}
                >
                  {call.status.replace("_", " ")}
                </span>
              </div>
              <p className="text-[11px] mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
                {call.company} · {call.outcome}
              </p>
            </div>

            <div className="flex items-center gap-4 flex-shrink-0">
              <span className="text-[12px] flex items-center gap-1" style={{ color: "hsl(var(--text-muted))" }}>
                <Clock className="w-3 h-3" /> {formatDuration(call.duration_seconds)}
              </span>
              <span className="text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>
                {relativeTime(call.created_at)}
              </span>
              <ChevronRight className="w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
