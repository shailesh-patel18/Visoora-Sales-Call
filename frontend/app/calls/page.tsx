"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  ChevronRight,
  Search,
  AlertCircle,
  RefreshCw,
  Inbox,
} from "lucide-react";
import { BACKEND_URL } from "../config";

// ====================================================
// TYPES
// ====================================================
interface CallEntry {
  id: string;
  phone_number: string;
  duration_seconds: number;
  final_state: string;
  recording_url: string | null;
  created_at: string;
  tenant_id?: string;
  // Legacy / enriched fields (from local fallback)
  direction?: "inbound" | "outbound";
  status?: string;
  outcome?: string;
}

function mapState(state: string): { label: string; color: string; bg: string } {
  const s = (state || "").toUpperCase();
  if (s === "SUCCESS_COMPLETE" || s === "BOOKING" || s === "COMPLETE")
    return { label: "Completed", color: "#22c55e", bg: "hsla(142,71%,45%,0.12)" };
  if (s === "NO_ANSWER" || s === "END_CALL_DISCONNECT")
    return { label: "No Answer", color: "#ef4444", bg: "hsla(0,84%,60%,0.12)" };
  if (s === "QUALIFICATION")
    return { label: "Qualified", color: "#6366f1", bg: "hsla(238,84%,66%,0.12)" };
  if (s === "INITIATION" || s === "GREETING" || s === "in_progress")
    return { label: "In Progress", color: "#f59e0b", bg: "hsla(38,92%,50%,0.12)" };
  return { label: state.replace(/_/g, " "), color: "hsl(var(--text-muted))", bg: "hsl(var(--surface-3))" };
}

function formatDuration(s: number): string {
  if (!s || s === 0) return "—";
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
// SKELETON ROW
// ====================================================
function SkeletonRow() {
  return (
    <div
      className="flex items-center gap-4 rounded-xl p-4 border animate-pulse"
      style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
    >
      <div className="w-10 h-10 rounded-full flex-shrink-0" style={{ background: "hsl(var(--surface-3))" }} />
      <div className="flex-1 space-y-2">
        <div className="h-3 rounded w-1/4" style={{ background: "hsl(var(--surface-3))" }} />
        <div className="h-2.5 rounded w-2/5" style={{ background: "hsl(var(--surface-3))" }} />
      </div>
      <div className="h-3 rounded w-16 flex-shrink-0" style={{ background: "hsl(var(--surface-3))" }} />
    </div>
  );
}

// ====================================================
// CALLS INDEX PAGE
// ====================================================
export default function CallsPage() {
  const [calls, setCalls] = useState<CallEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchCalls = useCallback(async (q: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: "50", offset: "0" });
      if (q) params.set("search", q);
      const res = await fetch(`${BACKEND_URL}/api/analytics/calls?${params}`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      setCalls(data.calls ?? []);
      setTotal(data.total ?? 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load call history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    fetchCalls("");
  }, [fetchCalls]);

  // Debounced search — sends request 400ms after user stops typing
  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchCalls(value), 400);
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Call History
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            {loading ? "Loading…" : `${total} call${total !== 1 ? "s" : ""} total`}
          </p>
        </div>
        {error && (
          <button
            onClick={() => fetchCalls(search)}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border transition-colors"
            style={{
              borderColor: "hsl(var(--border-subtle))",
              color: "hsl(var(--brand-primary))",
              background: "hsl(var(--surface-2))",
            }}
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "hsl(var(--text-muted))" }} />
        <input
          type="text"
          id="calls-search"
          placeholder="Search by phone number or outcome…"
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm border outline-none"
          style={{
            background: "hsl(var(--surface-2))",
            borderColor: "hsl(var(--border-subtle))",
            color: "hsl(var(--text-primary))",
          }}
        />
      </div>

      {/* Error State */}
      {error && !loading && (
        <div
          className="flex items-center gap-3 rounded-xl p-4 border"
          style={{ background: "hsla(0,84%,60%,0.08)", borderColor: "hsla(0,84%,60%,0.2)" }}
        >
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
          <div>
            <p className="text-sm font-medium" style={{ color: "hsl(var(--text-primary))" }}>
              Could not load call history
            </p>
            <p className="text-xs mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
              {error} — click Retry to try again, or check backend connectivity.
            </p>
          </div>
        </div>
      )}

      {/* Skeleton loading */}
      {loading && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && calls.length === 0 && (
        <div
          className="flex flex-col items-center justify-center rounded-xl border py-16 gap-3"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <Inbox className="w-10 h-10" style={{ color: "hsl(var(--text-muted))" }} />
          <p className="text-sm font-medium" style={{ color: "hsl(var(--text-secondary))" }}>
            {search ? "No calls match your search" : "No call records yet"}
          </p>
          <p className="text-xs" style={{ color: "hsl(var(--text-muted))" }}>
            {search ? "Try a different phone number or clear the search." : "Call logs will appear here after your first outbound call."}
          </p>
        </div>
      )}

      {/* Call list */}
      {!loading && !error && calls.length > 0 && (
        <div className="space-y-2">
          {calls.map((call) => {
            const direction = call.direction ?? "outbound";
            const badge = mapState(call.final_state ?? call.status ?? "");
            return (
              <Link
                key={call.id}
                href={`/calls/${call.id}`}
                className="flex items-center gap-4 rounded-xl p-4 border transition-all hover:scale-[1.005] hover:shadow-lg"
                style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
              >
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{
                    background: direction === "inbound" ? "hsla(168, 85%, 57%, 0.1)" : "hsla(262, 83%, 68%, 0.1)",
                    color: direction === "inbound" ? "hsl(var(--brand-primary))" : "hsl(var(--brand-accent))",
                  }}
                >
                  {direction === "inbound"
                    ? <PhoneIncoming className="w-4 h-4" />
                    : <PhoneOutgoing className="w-4 h-4" />}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] font-medium truncate" style={{ color: "hsl(var(--text-primary))" }}>
                      {call.phone_number}
                    </p>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide flex-shrink-0"
                      style={{ background: badge.bg, color: badge.color }}
                    >
                      {badge.label}
                    </span>
                  </div>
                  <p className="text-[11px] mt-0.5 truncate" style={{ color: "hsl(var(--text-muted))" }}>
                    {call.outcome ?? call.final_state?.replace(/_/g, " ")}
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
            );
          })}
        </div>
      )}
    </div>
  );
}
