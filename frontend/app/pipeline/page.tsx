"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  GripVertical,
  DollarSign,
  Plus,
  X,
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  User,
} from "lucide-react";
import { useCRMStore, type Deal, type PipelineStage } from "../store";

// ====================================================
// MOCK DATA
// ====================================================
function generateMockPipeline(): PipelineStage[] {
  const stages: PipelineStage[] = [
    { id: "s1", name: "New Lead", position: 0, probability_pct: 10, is_terminal: false, deals: [] },
    { id: "s2", name: "Qualified", position: 1, probability_pct: 25, is_terminal: false, deals: [] },
    { id: "s3", name: "Demo Booked", position: 2, probability_pct: 50, is_terminal: false, deals: [] },
    { id: "s4", name: "Proposal", position: 3, probability_pct: 75, is_terminal: false, deals: [] },
    { id: "s5", name: "Won", position: 4, probability_pct: 100, is_terminal: true, deals: [] },
    { id: "s6", name: "Lost", position: 5, probability_pct: 0, is_terminal: true, deals: [] },
  ];

  const mockDeals: Deal[] = [
    { id: "d1", tenant_id: "acme", contact_id: "c1", contact_name: "Sarah Connor", company_name: "Cyberdyne", stage_id: "s1", stage_name: "New Lead", title: "Cyberdyne AI Suite", value_usd: 12000, currency: "USD", ai_sentiment: "positive", ai_next_action: "Schedule demo", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
    { id: "d2", tenant_id: "acme", contact_id: "c2", contact_name: "Tony Stark", company_name: "Stark Industries", stage_id: "s2", stage_name: "Qualified", title: "Stark Enterprise Plan", value_usd: 45000, currency: "USD", ai_sentiment: "positive", ai_next_action: "Send proposal", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
    { id: "d3", tenant_id: "acme", contact_id: "c3", contact_name: "Bruce Wayne", company_name: "Wayne Enterprises", stage_id: "s3", stage_name: "Demo Booked", title: "Wayne Security Suite", value_usd: 85000, currency: "USD", ai_sentiment: "neutral", ai_next_action: "Conduct demo", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
    { id: "d4", tenant_id: "acme", contact_id: "c4", contact_name: "Diana Prince", company_name: "Themyscira Inc", stage_id: "s1", stage_name: "New Lead", title: "Themyscira Integration", value_usd: 8000, currency: "USD", ai_sentiment: "unknown", ai_next_action: "Qualify lead", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
    { id: "d5", tenant_id: "acme", contact_id: "c5", contact_name: "Peter Parker", company_name: "Daily Bugle", stage_id: "s4", stage_name: "Proposal", title: "Bugle Media Package", value_usd: 22000, currency: "USD", ai_sentiment: "negative", ai_next_action: "Handle objection", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
    { id: "d6", tenant_id: "acme", contact_id: "c6", contact_name: "Steve Rogers", company_name: "Shield Corp", stage_id: "s5", stage_name: "Won", title: "Shield Federal Contract", value_usd: 120000, currency: "USD", ai_sentiment: "positive", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
    { id: "d7", tenant_id: "acme", contact_id: "c7", contact_name: "Clark Kent", company_name: "Daily Planet", stage_id: "s2", stage_name: "Qualified", title: "Planet CRM Upgrade", value_usd: 15000, currency: "USD", ai_sentiment: "neutral", ai_next_action: "Book call", last_activity_date: new Date().toISOString(), created_at: new Date().toISOString() },
  ];

  mockDeals.forEach((deal) => {
    const stage = stages.find((s) => s.id === deal.stage_id);
    if (stage) stage.deals.push(deal);
  });

  return stages;
}

// ====================================================
// SUB COMPONENTS
// ====================================================
function SentimentIcon({ sentiment }: { sentiment: Deal["ai_sentiment"] }) {
  switch (sentiment) {
    case "positive": return <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />;
    case "negative": return <TrendingDown className="w-3.5 h-3.5 text-red-400" />;
    case "neutral": return <Minus className="w-3.5 h-3.5 text-amber-400" />;
    default: return <Minus className="w-3.5 h-3.5" style={{ color: "hsl(var(--text-muted))" }} />;
  }
}

function formatCurrency(value: number): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}K`;
  return `$${value}`;
}

const stageColors: Record<string, string> = {
  "New Lead": "#3b82f6",
  "Qualified": "#8b5cf6",
  "Demo Booked": "#10b981",
  "Proposal": "#f59e0b",
  "Won": "#22c55e",
  "Lost": "#ef4444",
};

// ====================================================
// DEAL CARD
// ====================================================
function DealCard({ deal, onDragStart }: { deal: Deal; onDragStart: (e: React.DragEvent, dealId: string, stageId: string) => void }) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, deal.id, deal.stage_id)}
      className="rounded-lg p-3 border cursor-grab active:cursor-grabbing transition-all hover:scale-[1.01] hover:shadow-lg"
      style={{
        background: "hsl(var(--surface-2))",
        borderColor: "hsl(var(--border-subtle))",
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <p className="text-[13px] font-medium leading-tight" style={{ color: "hsl(var(--text-primary))" }}>
          {deal.title}
        </p>
        <SentimentIcon sentiment={deal.ai_sentiment} />
      </div>
      <div className="flex items-center gap-1.5 mb-2">
        <User className="w-3 h-3" style={{ color: "hsl(var(--text-muted))" }} />
        <span className="text-[11px]" style={{ color: "hsl(var(--text-secondary))" }}>
          {deal.contact_name}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-bold" style={{ color: "hsl(var(--brand-primary))" }}>
          {formatCurrency(deal.value_usd)}
        </span>
        {deal.ai_next_action && (
          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "hsl(var(--surface-3))", color: "hsl(var(--text-muted))" }}>
            {deal.ai_next_action}
          </span>
        )}
      </div>
    </div>
  );
}

// ====================================================
// KANBAN COLUMN
// ====================================================
function KanbanColumn({
  stage,
  onDragStart,
  onDragOver,
  onDrop,
}: {
  stage: PipelineStage;
  onDragStart: (e: React.DragEvent, dealId: string, stageId: string) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, stageId: string) => void;
}) {
  const color = stageColors[stage.name] || "#6b7280";
  const totalValue = stage.deals.reduce((s, d) => s + d.value_usd, 0);

  return (
    <div
      className="flex flex-col min-w-[280px] max-w-[320px] flex-shrink-0 rounded-xl border"
      style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, stage.id)}
    >
      {/* Column Header */}
      <div className="px-4 py-3 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full" style={{ background: color }} />
          <h3 className="text-[13px] font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
            {stage.name}
          </h3>
          <span
            className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full"
            style={{ background: `${color}15`, color }}
          >
            {stage.deals.length}
          </span>
        </div>
        <p className="text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>
          {formatCurrency(totalValue)} total
        </p>
      </div>

      {/* Cards */}
      <div className="flex-1 p-3 space-y-2 overflow-y-auto max-h-[calc(100vh-260px)]">
        {stage.deals.map((deal) => (
          <DealCard key={deal.id} deal={deal} onDragStart={onDragStart} />
        ))}
        {stage.deals.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>No deals</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ====================================================
// PIPELINE PAGE
// ====================================================
export default function PipelinePage() {
  const { stages, setStages, moveDeal } = useCRMStore();
  const [mounted, setMounted] = useState(false);
  const [dragInfo, setDragInfo] = useState<{ dealId: string; fromStageId: string } | null>(null);

  useEffect(() => {
    setMounted(true);
    if (stages.length === 0) setStages(generateMockPipeline());
  }, [stages.length, setStages]);

  const handleDragStart = useCallback(
    (e: React.DragEvent, dealId: string, stageId: string) => {
      setDragInfo({ dealId, fromStageId: stageId });
      e.dataTransfer.effectAllowed = "move";
    },
    []
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, toStageId: string) => {
      e.preventDefault();
      if (dragInfo && dragInfo.fromStageId !== toStageId) {
        moveDeal(dragInfo.dealId, dragInfo.fromStageId, toStageId);
      }
      setDragInfo(null);
    },
    [dragInfo, moveDeal]
  );

  if (!mounted) return null;

  const totalPipeline = stages.reduce(
    (sum, s) => sum + s.deals.reduce((ds, d) => ds + d.value_usd, 0),
    0
  );

  return (
    <div className="p-6 lg:p-8 max-w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Pipeline
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            {formatCurrency(totalPipeline)} total pipeline value ·{" "}
            {stages.reduce((s, st) => s + st.deals.length, 0)} deals
          </p>
        </div>
        <button
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white"
          style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
        >
          <Plus className="w-3.5 h-3.5" /> Add Deal
        </button>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.map((stage) => (
          <KanbanColumn
            key={stage.id}
            stage={stage}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          />
        ))}
      </div>
    </div>
  );
}
