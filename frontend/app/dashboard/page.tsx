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
        <div className={`flex items-center gap-1 text-xs font-medium ${positive ? "text-emerald-400" : "text-red-400"}`}>
          {positive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {Math.abs(change)}%
        </div>
      </div>
      <p className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
        {value}
      </p>
      <p className="text-xs mt-1" style={{ color: "hsl(var(--text-muted))" }}>
        {changeLabel}
      </p>
    </div>
  );
}

function FSMBadge({ state }: { state: string }) {
  const colors: Record<string, string> = {
    INITIATION: "#f59e0b",
    GREETING: "#f59e0b",
    INTENT_DETECTION: "#8b5cf6",
    QUALIFICATION: "#3b82f6",
    QUALIFY_LEAD: "#3b82f6",
    BOOKING: "#10b981",
    OBJECTION: "#ef4444",
    TRANSFER_TO_HUMAN: "#ec4899",
    COMPLETE: "#6b7280",
  };
  const color = colors[state] || "#6b7280";
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase"
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
      className="rounded-lg px-3 py-2 text-xs border shadow-xl"
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
  const [trendData] = useState(generateTrendData);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setLiveCalls(generateMockLiveCalls());
    setActivities(generateMockActivities());
  }, [setLiveCalls, setActivities]);

  // Simulate live call polling every 2s
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveCalls(
        generateMockLiveCalls().map((c) => ({
          ...c,
          fsm_state: ["QUALIFICATION", "BOOKING", "OBJECTION", "GREETING", "INTENT_DETECTION"][
            Math.floor(Math.random() * 5)
          ],
        }))
      );
    }, 2000);
    return () => clearInterval(interval);
  }, [setLiveCalls]);

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: "hsl(var(--brand-primary))", borderTopColor: "transparent" }} />
      </div>
    );
  }

  const totalCalls = trendData.reduce((s, d) => s + d.calls, 0);
  const totalMeetings = trendData.reduce((s, d) => s + d.meetings, 0);
  const connectionRate = totalCalls > 0 ? Math.round((totalMeetings / totalCalls) * 100) : 0;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Command Center
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            Real-time overview of your AI sales operations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium" style={{ background: "hsla(142, 71%, 45%, 0.1)", color: "hsl(var(--success))" }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse-live" style={{ background: "hsl(var(--success))" }} />
            System Online
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Calls Today" value="47" change={12} changeLabel="vs yesterday" icon={PhoneCall} accentColor="#3b82f6" />
        <KPICard title="Connection Rate" value={`${connectionRate}%`} change={3} changeLabel="vs last week" icon={TrendingUp} accentColor="#10b981" />
        <KPICard title="Meetings Booked" value="8" change={-5} changeLabel="vs yesterday" icon={CalendarCheck} accentColor="#8b5cf6" />
        <KPICard title="Pipeline Added" value="$24.5K" change={18} changeLabel="this week" icon={DollarSign} accentColor="#f59e0b" />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart — spans 2 cols */}
        <div
          className="lg:col-span-2 rounded-xl border p-5"
          style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
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
            <Radio className="w-4 h-4 text-red-400 animate-pulse-live" />
            <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
              Live Calls
            </h2>
            <span
              className="ml-auto text-[11px] font-bold px-2 py-0.5 rounded-full"
              style={{ background: "hsla(0, 84%, 60%, 0.15)", color: "#ef4444" }}
            >
              {liveCalls.length} active
            </span>
          </div>
          <div className="space-y-3">
            {liveCalls.length === 0 && (
              <p className="text-xs py-8 text-center" style={{ color: "hsl(var(--text-muted))" }}>
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
                  <span className="text-[13px] font-medium" style={{ color: "hsl(var(--text-primary))" }}>
                    {call.name}
                  </span>
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded font-medium uppercase"
                    style={{
                      background: call.direction === "inbound" ? "hsla(168, 85%, 57%, 0.1)" : "hsla(262, 83%, 68%, 0.1)",
                      color: call.direction === "inbound" ? "hsl(var(--brand-primary))" : "hsl(var(--brand-accent))",
                    }}
                  >
                    {call.direction}
                  </span>
                </div>
                <p className="text-[11px] mb-2" style={{ color: "hsl(var(--text-muted))" }}>
                  {call.company} · {call.phone}
                </p>
                <div className="flex items-center justify-between">
                  <FSMBadge state={call.fsm_state} />
                  <span className="text-[10px] flex items-center gap-1" style={{ color: "hsl(var(--text-muted))" }}>
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
        <h2 className="text-sm font-semibold mb-4" style={{ color: "hsl(var(--text-primary))" }}>
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
                  <p className="text-[13px] leading-relaxed" style={{ color: "hsl(var(--text-primary))" }}>
                    {event.description}
                  </p>
                </div>
                <span className="text-[11px] flex-shrink-0" style={{ color: "hsl(var(--text-muted))" }}>
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
