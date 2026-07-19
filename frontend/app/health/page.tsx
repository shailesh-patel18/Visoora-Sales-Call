"use client";

import React, { useEffect, useState } from "react";
import { Activity, Database, Server, Mail, ShieldAlert, Cpu, MessageSquare } from "lucide-react";
import { BACKEND_URL } from "../config";

interface SubsystemStatus {
  status: "ok" | "degraded" | "down" | "unconfigured";
  latency_ms?: number;
  message?: string;
}

interface HealthResponse {
  status: "ok" | "degraded" | "down";
  subsystems: {
    database: SubsystemStatus;
    ai_provider: SubsystemStatus;
    queue: SubsystemStatus;
    email: SubsystemStatus;
    twilio: SubsystemStatus;
  };
  uptime_seconds?: number;
}

export default function HealthDashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/health`);
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.error(err);
      setHealth({
        status: "down",
        subsystems: {
          database: { status: "down", message: "Network Error" },
          ai_provider: { status: "down", message: "Network Error" },
          queue: { status: "down", message: "Network Error" },
          email: { status: "down", message: "Network Error" },
          twilio: { status: "down", message: "Network Error" }
        }
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Activity className="w-8 h-8 text-[hsl(var(--brand-primary))] animate-pulse" />
      </div>
    );
  }

  const overallColor = health?.status === "ok" 
    ? "text-emerald-400 border-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.1)]" 
    : health?.status === "degraded" 
      ? "text-amber-400 border-amber-500/50 shadow-[0_0_30px_rgba(245,158,11,0.1)]"
      : "text-rose-400 border-rose-500/50 shadow-[0_0_30px_rgba(244,63,94,0.1)]";

  const StatusCard = ({ title, icon: Icon, status }: { title: string, icon: any, status: SubsystemStatus }) => {
    let color = "text-gray-400 border-white/5 bg-white/5";
    let badgeColor = "bg-gray-500/20 text-gray-400";
    
    if (status.status === "ok") {
      color = "border-emerald-500/20 bg-emerald-500/5 hover:border-emerald-500/50";
      badgeColor = "bg-emerald-500/20 text-emerald-400";
    } else if (status.status === "degraded") {
      color = "border-amber-500/20 bg-amber-500/5 hover:border-amber-500/50";
      badgeColor = "bg-amber-500/20 text-amber-400";
    } else if (status.status === "down") {
      color = "border-rose-500/20 bg-rose-500/5 hover:border-rose-500/50";
      badgeColor = "bg-rose-500/20 text-rose-400";
    }

    return (
      <div className={`p-6 rounded-2xl border transition-all duration-300 ${color}`}>
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3 text-white">
            <div className={`p-2 rounded-lg ${badgeColor}`}>
              <Icon className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg">{title}</h3>
          </div>
          <div className={`text-xs font-bold px-2 py-1 rounded uppercase tracking-wider ${badgeColor}`}>
            {status.status}
          </div>
        </div>
        <div className="space-y-1">
          {status.latency_ms !== undefined && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Latency</span>
              <span className="text-gray-300 font-mono">{status.latency_ms}ms</span>
            </div>
          )}
          {status.message && (
            <div className="flex justify-between text-sm mt-2">
              <span className="text-gray-400 truncate">{status.message}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold mb-2">System Health</h1>
          <p className="text-gray-400">Real-time monitoring of Visoora subsystems and integrations.</p>
        </div>
        <div className={`px-6 py-3 border rounded-xl flex items-center gap-3 ${overallColor} bg-black/40 backdrop-blur-md`}>
          <Activity className="w-6 h-6" />
          <span className="font-bold uppercase tracking-wider">{health?.status}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatusCard 
          title="Supabase Database" 
          icon={Database} 
          status={health?.subsystems.database || {status: "down"}} 
        />
        <StatusCard 
          title="OpenAI / Anthropic" 
          icon={Cpu} 
          status={health?.subsystems.ai_provider || {status: "down"}} 
        />
        <StatusCard 
          title="Redis / Celery Queue" 
          icon={Server} 
          status={health?.subsystems.queue || {status: "down"}} 
        />
        <StatusCard 
          title="SMTP Deliverability" 
          icon={Mail} 
          status={health?.subsystems.email || {status: "down"}} 
        />
        <StatusCard 
          title="Twilio Voice API" 
          icon={MessageSquare} 
          status={health?.subsystems.twilio || {status: "down"}} 
        />
      </div>
    </div>
  );
}
