"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Phone,
  PhoneCall,
  CalendarCheck,
  DollarSign,
  TrendingUp,
  Activity,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Radio,
  ShieldAlert,
  Sparkles,
  CheckCircle2,
  Award,
  ChevronDown,
  ChevronUp,
  Play,
  Building2,
  AlertTriangle,
} from "lucide-react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useCRMStore, type LiveCall, type ActivityEvent } from "../store";
import { useOnboardingStore } from "../onboarding/store";
import Link from "next/link";
import { BACKEND_URL, getWsUrl } from "../config";
import { getAuthHeaders } from "../auth/store";

// ====================================================
// MOCK DATA GENERATORS (replaced by API in production)
// ====================================================
function generateTrendData() {
  const data = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const calls = Math.floor(Math.random() * 35) + 8;
    const meetings = Math.floor(calls * (Math.random() * 0.25 + 0.05));
    data.push({
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      calls,
      meetings,
    });
  }
  return data;
}

function generateMockActivities(): ActivityEvent[] {
  const types: ActivityEvent["type"][] = [
    "call_completed", "deal_stage_changed", "booking_confirmed", "contact_created", "sms_sent"
  ];
  const descriptions = [
    "Call completed with Sarah Connor at Cyberdyne Systems (2m 34s)",
    "Deal 'Acme Enterprise' moved to Demo Booked",
    "Meeting confirmed: Tuesday at 2:00 PM with John Doe",
    "New contact created: Bruce Wayne — Wayne Enterprises",
    "SMS confirmation sent to +1 (555) 012-3456",
    "Call completed with Tony Stark at Stark Industries (4m 12s)",
    "Deal 'Shield Ops' moved to Qualified",
    "Meeting confirmed: Wednesday at 10:00 AM with Steve Rogers",
    "New contact created: Natasha Romanoff — SHIELD",
    "Call completed with Peter Parker at Daily Bugle (1m 45s)",
    "Deal 'Wayne Security' moved to Closed Won",
    "SMS confirmation sent to +44 7911 123456",
    "Call completed with Diana Prince at Themyscira Inc (3m 02s)",
    "Deal 'Stark AI Suite' moved to Stale",
    "New contact created: Clark Kent — Daily Planet",
    "Call completed with Barry Allen at STAR Labs (2m 18s)",
    "Meeting confirmed: Friday at 3:00 PM with Wanda Maximoff",
    "Deal 'STAR Labs Integration' moved to New Lead",
    "SMS confirmation sent to +91 98244 57565",
    "Call completed with Hal Jordan at Ferris Aircraft (5m 01s)",
  ];
  return descriptions.map((desc, i) => ({
    id: `act_${i}`,
    type: types[i % types.length],
    description: desc,
    timestamp: new Date(Date.now() - i * 420000).toISOString(),
    metadata: {},
  }));
}

function generateMockLiveCalls(): LiveCall[] {
  return [
    {
      stream_sid: "stream_abc123",
      phone: "+15017122661",
      name: "Sarah Connor",
      company: "Cyberdyne Systems",
      fsm_state: "QUALIFICATION",
      direction: "outbound",
      started_at: new Date(Date.now() - 95000).toISOString(),
    },
    {
      stream_sid: "stream_xyz789",
      phone: "+919824457565",
      name: "Incoming Caller",
      company: "Unknown",
      fsm_state: "INTENT_DETECTION",
      direction: "inbound",
      started_at: new Date(Date.now() - 23000).toISOString(),
    },
  ];
}

// ====================================================
// SUBCOMPONENTS
// ====================================================
function KPICard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  accentColor,
}: {
  title: string;
  value: string;
  change: number;
  changeLabel: string;
  icon: React.ElementType;
  accentColor: string;
}) {
  const positive = change >= 0;
  return (
    <div
      className="rounded-xl p-5 border transition-all hover:scale-[1.01]"
      style={{
        background: "hsl(var(--surface-1))",
        borderColor: "hsl(var(--border-subtle))",
      }}
    >
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ background: `${accentColor}15`, color: accentColor }}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className={`flex items-center gap-1 text-sm font-semibold ${positive ? "text-emerald-400" : "text-red-400"}`}>
          {positive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
          {Math.abs(change)}%
        </div>
      </div>
      <p className="text-xs font-bold uppercase tracking-wider mb-1.5" style={{ color: "hsl(var(--text-secondary))" }}>
        {title}
      </p>
      <p className="text-3xl font-extrabold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
        {value}
      </p>
      <p className="text-sm mt-1.5" style={{ color: "hsl(var(--text-muted))" }}>
        {changeLabel}
      </p>
    </div>
  );
}

function FSMBadge({ state }: { state: string }) {
  const colors: Record<string, string> = {
    INITIATION: "#f59e0b",
    GREETING: "#f59e0b",
    DISCOVERY: "#06b6d4",
    INTENT_DETECTION: "#8b5cf6",
    PITCH: "#3b82f6",
    QUALIFICATION: "#3b82f6",
    QUALIFY_LEAD: "#3b82f6",
    BOOKING: "#10b981",
    OBJECTION: "#ef4444",
    TRANSFER_TO_HUMAN: "#ec4899",
    SUCCESS_COMPLETE: "#22c55e",
    COMPLETE: "#6b7280",
    END_CALL_DISCONNECT: "#6b7280",
  };
  const color = colors[state] || "#6b7280";
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide uppercase"
      style={{ background: `${color}20`, color }}
    >
      <span className="w-1.5 h-1.5 rounded-full animate-pulse-live" style={{ background: color }} />
      {state.replace(/_/g, " ")}
    </span>
  );
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function activityIcon(type: ActivityEvent["type"]) {
  switch (type) {
    case "call_completed": return <Phone className="w-3.5 h-3.5" />;
    case "deal_stage_changed": return <TrendingUp className="w-3.5 h-3.5" />;
    case "booking_confirmed": return <CalendarCheck className="w-3.5 h-3.5" />;
    case "contact_created": return <Activity className="w-3.5 h-3.5" />;
    case "sms_sent": return <ArrowUpRight className="w-3.5 h-3.5" />;
    default: return <Activity className="w-3.5 h-3.5" />;
  }
}

function activityColor(type: ActivityEvent["type"]): string {
  switch (type) {
    case "call_completed": return "#3b82f6";
    case "deal_stage_changed": return "#8b5cf6";
    case "booking_confirmed": return "#10b981";
    case "contact_created": return "#f59e0b";
    case "sms_sent": return "#06b6d4";
    default: return "#6b7280";
  }
}

// ====================================================
// CUSTOM TOOLTIP FOR RECHARTS
// ====================================================
function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; dataKey: string }>; label?: string }) {
  if (!active || !payload) return null;
  return (
    <div
      className="rounded-lg px-3 py-2 text-sm border shadow-xl"
      style={{
        background: "hsl(var(--surface-2))",
        borderColor: "hsl(var(--border-subtle))",
      }}
    >
      <p className="font-semibold mb-1" style={{ color: "hsl(var(--text-primary))" }}>{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.dataKey === "calls" ? "#3b82f6" : "#10b981" }}>
          {entry.dataKey === "calls" ? "Calls" : "Meetings"}: {entry.value}
        </p>
      ))}
    </div>
  );
}

// ====================================================
// DASHBOARD PAGE
// ====================================================
export default function DashboardPage() {
  const { liveCalls, setLiveCalls, activities, setActivities } = useCRMStore();
  const { state: onboardingState, loadProgress } = useOnboardingStore();
  const [trendData] = useState(generateTrendData);
  const [mounted, setMounted] = useState(false);
  const [auditExpanded, setAuditExpanded] = useState(false);

  // Real API and WebSocket state management
  const [analytics, setAnalytics] = useState({
    total_calls: 0,
    total_duration_seconds: 0,
    success_rate_percent: 0,
    success_calls: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<"connected" | "connecting" | "disconnected">("connecting");

  // Fetch real REST data from backend analytics and logs endpoints
  const fetchDashboardData = useCallback(async () => {
    try {
      setError(null);
      
      const analyticsRes = await fetch(`${BACKEND_URL}/api/analytics/dashboard`, {
        headers: getAuthHeaders()
      });
      if (analyticsRes.ok) {
        const data = await analyticsRes.json();
        setAnalytics(data);
      } else {
        throw new Error(`Analytics API returned status ${analyticsRes.status}`);
      }

      const logsRes = await fetch(`${BACKEND_URL}/api/logs`, {
        headers: getAuthHeaders()
      });
      if (logsRes.ok) {
        const logs = await logsRes.json();
        // Convert logs to activity events dynamically
        const convertedActivities: ActivityEvent[] = logs.map((log: any, idx: number) => {
          const durMins = Math.floor(log.duration_seconds / 60);
          const durSecs = Math.round(log.duration_seconds % 60);
          const durationStr = durMins > 0 ? `${durMins}m ${durSecs}s` : `${durSecs}s`;
          return {
            id: log.id || `log_${idx}`,
            type: "call_completed" as const,
            description: `Call completed with ${log.name || "Prospect"} at ${log.company || "Unknown"} (${durationStr})`,
            timestamp: log.created_at || new Date().toISOString(),
          };
        });
        setActivities(convertedActivities);
      }
    } catch (err: any) {
      console.error("Dashboard fetch error:", err);
      setError(err.message || "Failed to load dashboard data");
      setActivities([]);
    } finally {
      setLoading(false);
    }
  }, [setActivities]);

  // Initial load
  useEffect(() => {
    setMounted(true);
    fetchDashboardData();
    loadProgress();
  }, [fetchDashboardData, loadProgress]);

  // Connect to live updates WebSocket (M2.3)
  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryCount = 0;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWs = () => {
      setWsStatus("connecting");
      const wsUrl = getWsUrl("/api/live-ws");
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("Live dashboard WebSocket connected.");
        setWsStatus("connected");
        retryCount = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event === "session_backfill") {
            const activeCalls = data.turns && data.turns.length > 0 ? [{
              stream_sid: data.stream_sid,
              phone: "Active Call",
              name: "Active Prospect",
              company: "Unknown",
              fsm_state: data.turns[data.turns.length - 1]?.state || "INITIATION",
              direction: "outbound" as const,
              started_at: data.turns[0]?.timestamp || new Date().toISOString(),
            }] : [];
            setLiveCalls(activeCalls);
          } else if (data.event === "session_started") {
            setLiveCalls((prev) => {
              if (prev.some((c) => c.stream_sid === data.stream_sid)) return prev;
              return [...prev, {
                stream_sid: data.stream_sid,
                phone: data.phone,
                name: data.name,
                company: data.company,
                fsm_state: data.fsm_state,
                direction: data.direction,
                started_at: data.started_at,
              }];
            });
          } else if (data.event === "live_transcript_turn") {
            setLiveCalls((prev) =>
              prev.map((c) =>
                c.stream_sid === data.stream_sid
                  ? { ...c, fsm_state: data.turn.state }
                  : c
              )
            );
          } else if (data.event === "session_completed") {
            // Remove from live calls list
            setLiveCalls((prev) => prev.filter((c) => c.stream_sid !== data.stream_sid));
            // Prepends to activities feed
            const dur = data.metrics?.stream_duration || 0;
            const mins = Math.floor(dur / 60);
            const secs = Math.round(dur % 60);
            const durStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
            setActivities((prev) => [
              {
                id: `completed_${data.stream_sid}`,
                type: "call_completed" as const,
                description: `Call completed with prospect (${durStr})`,
                timestamp: new Date().toISOString(),
              },
              ...prev,
            ]);
            // Refresh stats to include completed call
            fetchDashboardData();
          }
        } catch (err) {
          console.error("Error parsing live WS payload:", err);
        }
      };

      ws.onclose = (event) => {
        console.warn("Live dashboard WebSocket closed:", event);
        setWsStatus("disconnected");
        ws = null;

        // Exponential back-off capped at 3 retries
        if (retryCount < 3) {
          const delay = Math.pow(2, retryCount) * 1000;
          console.log(`Reconnecting live WS in ${delay}ms... (Attempt ${retryCount + 1}/3)`);
          reconnectTimeout = setTimeout(() => {
            retryCount++;
            connectWs();
          }, delay);
        } else {
          console.error("WebSocket connection lost permanently after 3 attempts.");
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
      };
    };

    connectWs();

    return () => {
      if (ws) {
        ws.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [setLiveCalls, setActivities, fetchDashboardData]);

  if (!mounted || loading) {
    return (
      <div className="flex items-center justify-center h-[500px]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin" style={{ borderColor: "hsl(var(--brand-primary))", borderTopColor: "transparent" }} />
          <p className="text-sm font-semibold animate-pulse" style={{ color: "hsl(var(--text-muted))" }}>Loading command center metrics...</p>
        </div>
      </div>
    );
  }

  // Calculate AI Readiness Score & Completeness
  const profileComplete = !!(onboardingState.step3?.agentName && onboardingState.step3?.voice && onboardingState.step3?.timezone);
  const productComplete = !!(onboardingState.step3?.productName && onboardingState.step3?.productPrice && onboardingState.step3?.productFeatures);
  const playbookComplete = !!(onboardingState.step5?.playbookGreeting && onboardingState.step5?.playbookBookingLink);
  const faqComplete = (onboardingState.step3?.kbFaqs?.length || 0) >= 2;
  const objectionsComplete = (onboardingState.step3?.objectionsList?.length || 0) >= 2;

  let score = 0;
  if (profileComplete) score += 20;
  if (productComplete) score += 25;
  if (playbookComplete) score += 20;
  if (faqComplete) score += 15;
  if (objectionsComplete) score += 20;

  const totalCalls = trendData.reduce((s, d) => s + d.calls, 0);
  const totalMeetings = trendData.reduce((s, d) => s + d.meetings, 0);
  const connectionRate = totalCalls > 0 ? Math.round((totalMeetings / totalCalls) * 100) : 0;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Command Center
          </h1>
          <p className="text-base mt-1" style={{ color: "hsl(var(--text-muted))" }}>
            Real-time overview of your AI sales operations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium" style={{ background: "hsla(142, 71%, 45%, 0.1)", color: "hsl(var(--success))" }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse-live" style={{ background: "hsl(var(--success))" }} />
            System Online
          </div>
        </div>
      </div>

      {/* Pre-Flight AI Readiness Audit Widget */}
      <div
        className="rounded-xl border transition-all relative overflow-hidden"
        style={{
          background: "hsl(var(--surface-1))",
          borderColor: score === 100 ? "hsla(142, 71%, 45%, 0.25)" : "hsla(38, 92%, 50%, 0.25)",
        }}
      >
        <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
              style={{
                background: score === 100 ? "hsla(142, 71%, 45%, 0.15)" : "hsla(38, 92%, 50%, 0.15)",
                color: score === 100 ? "hsl(var(--success))" : "hsl(var(--warning))",
              }}
            >
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold tracking-tight flex items-center gap-2" style={{ color: "hsl(var(--text-primary))" }}>
                Pre-Flight AI Readiness Audit
                <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-white/10" style={{ color: score === 100 ? "hsl(var(--success))" : "hsl(var(--warning))" }}>
                  {score}% Ready
                </span>
              </h3>
              <p className="text-sm mt-1" style={{ color: "hsl(var(--text-muted))" }}>
                {score === 100 
                  ? "Your AI Employee is fully trained and ready for dial execution campaigns."
                  : "AI training is currently incomplete. Review instructions before running dial operations."
                }
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAuditExpanded(!auditExpanded)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold border transition-all"
              style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
            >
              {auditExpanded ? (
                <>Collapse Audit <ChevronUp className="w-3.5 h-3.5" /></>
              ) : (
                <>Audit AI Knowledge <ChevronDown className="w-3.5 h-3.5" /></>
              )}
            </button>
            <Link
              href="/onboarding"
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-white transition-all bg-[hsl(var(--brand-primary))] hover:opacity-90"
            >
              <Play className="w-3.5 h-3.5" /> Launch Sandbox Test
            </Link>
          </div>
        </div>

        {/* Audit Details Panel (Expandable) */}
        {auditExpanded && (
          <div className="border-t p-5 grid grid-cols-1 md:grid-cols-5 gap-6" style={{ borderColor: "hsl(var(--border-subtle))", background: "rgba(255,255,255,0.01)" }}>
            
            {/* 1. Who is calling */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">1. Who is calling?</span>
              <div className="p-3.5 rounded-lg border text-sm flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white">{onboardingState.step3?.agentName || "Alex"}</span>
                  <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">Profile</span>
                </div>
                <p className="text-xs text-neutral-300 mt-1">Voice: {onboardingState.step3?.voice || " Rachel"}</p>
                <p className="text-xs text-neutral-300">Tone: {onboardingState.step3?.tone || " consultative"}</p>
                <p className="text-xs text-neutral-300 font-mono">Hours: {onboardingState.step3?.callingHoursStart || "08:00"}-{onboardingState.step3?.callingHoursEnd || "17:00"}</p>
                <Link href="/agents" className="text-xs text-[hsl(var(--brand-accent))] font-bold mt-2 hover:underline">Edit Agent ➔</Link>
              </div>
            </div>

            {/* 2. What it is selling */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">2. What is it selling?</span>
              <div className="p-3.5 rounded-lg border text-sm flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                <span className="font-semibold text-white truncate">{onboardingState.step3?.productName || "No Product"}</span>
                <p className="text-xs text-neutral-300 mt-1">Price: {onboardingState.step3?.productPrice || " N/A"}</p>
                <p className="text-xs text-neutral-300 line-clamp-2">Features: {onboardingState.step3?.productFeatures || "None"}</p>
                <Link href="/agents" className="text-xs text-[hsl(var(--brand-accent))] font-bold mt-2 hover:underline">Edit Product ➔</Link>
              </div>
            </div>

            {/* 3. What it knows */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">3. What does it know?</span>
              <div className="p-3.5 rounded-lg border text-sm flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                <span className="font-semibold text-white">Wiki & FAQ grounded</span>
                <p className="text-xs text-neutral-300 mt-1">FAQs loaded: {onboardingState.step3?.kbFaqs?.length || 0}</p>
                <p className="text-xs text-neutral-300 line-clamp-2">Wiki: {onboardingState.step3?.kbDescription || "None"}</p>
                <Link href="/knowledge" className="text-xs text-[hsl(var(--brand-accent))] font-bold mt-2 hover:underline">Edit Wiki & FAQs ➔</Link>
              </div>
            </div>

            {/* 4. How it handles resistance */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">4. How it handles resistance?</span>
              <div className="p-3.5 rounded-lg border text-sm flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                <span className="font-semibold text-white">Objection Matrix</span>
                <p className="text-xs text-neutral-300 mt-1">Rebuttals Mapped: {onboardingState.step3?.objectionsList?.length || 0}</p>
                <p className="text-xs text-neutral-300">Stumped Queue: 3 items</p>
                <Link href="/objections" className="text-xs text-[hsl(var(--brand-accent))] font-bold mt-2 hover:underline">Edit Rebuttals ➔</Link>
              </div>
            </div>

            {/* 5. Playbook goal */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-400">5. Campaign Playbook Goal</span>
              <div className="p-3.5 rounded-lg border text-sm flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                <span className="font-semibold text-white truncate">{onboardingState.step5?.campaignGoal || "None"}</span>
                <p className="text-xs text-neutral-300 mt-1">Schedule Link: {onboardingState.step5?.playbookBookingLink ? "Configured" : "Missing"}</p>
                <p className="text-xs text-neutral-300 line-clamp-2">Opening script hook configured.</p>
                <Link href="/playbooks" className="text-xs text-[hsl(var(--brand-accent))] font-bold mt-2 hover:underline">Edit Playbook ➔</Link>
              </div>
            </div>

          </div>
        )}
      </div>


      {/* Error Alert Banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl border" style={{ background: "hsla(347, 87%, 60%, 0.08)", borderColor: "hsla(347, 87%, 60%, 0.25)" }}>
          <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: "hsl(var(--destructive))" }} />
          <div className="flex-1 text-sm font-semibold" style={{ color: "hsl(var(--destructive))" }}>
            Server Connection Error: {error}
          </div>
          <button onClick={fetchDashboardData} className="px-3 py-1.5 rounded-lg text-xs font-bold bg-neutral-800 hover:bg-neutral-700 transition-colors">
            Retry Connection
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Calls Today" value={analytics.total_calls.toString()} change={12} changeLabel="vs yesterday" icon={PhoneCall} accentColor="#3b82f6" />
        <KPICard title="Connection Rate" value={`${analytics.success_rate_percent}%`} change={3} changeLabel="vs last week" icon={TrendingUp} accentColor="#10b981" />
        <KPICard title="Meetings Booked" value={analytics.success_calls.toString()} change={-5} changeLabel="vs yesterday" icon={CalendarCheck} accentColor="#8b5cf6" />
        <KPICard title="Pipeline Added" value={`$${((analytics.success_calls * 3500) / 1000).toFixed(1)}K`} change={18} changeLabel="this week" icon={DollarSign} accentColor="#f59e0b" />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart — spans 2 cols */}
        <div
          className="lg:col-span-2 rounded-xl border p-5"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold" style={{ color: "hsl(var(--text-primary))" }}>
              Calls & Meetings — Last 30 Days
            </h2>
          </div>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(240, 4%, 16%)" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "hsl(240, 4%, 46%)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  interval={4}
                />
                <YAxis
                  tick={{ fill: "hsl(240, 4%, 46%)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="calls" fill="#3b82f6" radius={[4, 4, 0, 0]} opacity={0.7} barSize={14} />
                <Line
                  type="monotone"
                  dataKey="meetings"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ r: 0 }}
                  activeDot={{ r: 4, fill: "#10b981" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live Calls Widget */}
        <div
          className="rounded-xl border p-5"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <div className="flex items-center gap-2 mb-4">
            <Radio className={`w-4 h-4 ${wsStatus === "connected" && liveCalls.length > 0 ? "text-red-400 animate-pulse-live" : "text-neutral-500"}`} />
            <h2 className="text-base font-bold" style={{ color: "hsl(var(--text-primary))" }}>
              Live Calls
            </h2>
            <span
              className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full"
              style={{
                background: wsStatus === "connected" ? "hsla(142, 71%, 45%, 0.15)" : "hsla(38, 92%, 50%, 0.15)",
                color: wsStatus === "connected" ? "hsl(var(--success))" : "hsl(var(--warning))"
              }}
            >
              {wsStatus === "connected" ? `${liveCalls.length} active` : wsStatus === "connecting" ? "Reconnecting..." : "Connection Lost"}
            </span>
          </div>
          <div className="space-y-3">
            {liveCalls.length === 0 && (
              <p className="text-sm py-8 text-center" style={{ color: "hsl(var(--text-muted))" }}>
                No active calls right now
              </p>
            )}
            {liveCalls.map((call) => (
              <div
                key={call.stream_sid}
                className="rounded-lg p-3 border"
                style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                    {call.name}
                  </span>
                  <span
                    className="text-[11px] px-1.5 py-0.5 rounded font-semibold uppercase"
                    style={{
                      background: call.direction === "inbound" ? "hsla(168, 85%, 57%, 0.1)" : "hsla(262, 83%, 68%, 0.1)",
                      color: call.direction === "inbound" ? "hsl(var(--brand-primary))" : "hsl(var(--brand-accent))",
                    }}
                  >
                    {call.direction}
                  </span>
                </div>
                <p className="text-xs mb-2" style={{ color: "hsl(var(--text-muted))" }}>
                  {call.company} · {call.phone}
                </p>
                <div className="flex items-center justify-between">
                  <FSMBadge state={call.fsm_state} />
                  <span className="text-xs flex items-center gap-1" style={{ color: "hsl(var(--text-muted))" }}>
                    <Clock className="w-3 h-3" />
                    {relativeTime(call.started_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Activity Feed */}
      <div
        className="rounded-xl border p-5"
        style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
      >
        <h2 className="text-base font-bold mb-4" style={{ color: "hsl(var(--text-primary))" }}>
          Activity Feed
        </h2>
        <div className="space-y-1 max-h-[400px] overflow-y-auto">
          {activities.slice(0, 20).map((event) => {
            const color = activityColor(event.type);
            return (
              <div
                key={event.id}
                className="flex items-start gap-3 py-2.5 px-2 rounded-lg transition-colors hover:bg-white/[0.02]"
              >
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{ background: `${color}15`, color }}
                >
                  {activityIcon(event.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-relaxed" style={{ color: "hsl(var(--text-primary))" }}>
                    {event.description}
                  </p>
                </div>
                <span className="text-xs flex-shrink-0" style={{ color: "hsl(var(--text-muted))" }}>
                  {relativeTime(event.timestamp)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
