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
  Trash2,
  AlertCircle,
  ChevronDown
} from "lucide-react";
import { useCRMStore, type Deal, type PipelineStage } from "../store";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

// ====================================================
// MOCK DATA FALLBACK
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
function DealCard({
  deal,
  onDragStart,
  onDelete
}: {
  deal: Deal;
  onDragStart: (e: React.DragEvent, dealId: string, stageId: string) => void;
  onDelete: (dealId: string) => void;
}) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, deal.id, deal.stage_id)}
      className="group rounded-lg p-3 border cursor-grab active:cursor-grabbing transition-all hover:scale-[1.01] hover:shadow-lg relative"
      style={{
        background: "hsl(var(--surface-2))",
        borderColor: "hsl(var(--border-subtle))",
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <p className="text-[13px] font-medium leading-tight pr-6" style={{ color: "hsl(var(--text-primary))" }}>
          {deal.title}
        </p>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <SentimentIcon sentiment={deal.ai_sentiment} />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(deal.id);
            }}
            className="p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10"
            style={{ color: "#ef4444" }}
            title="Delete Deal"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      <div className="flex items-center gap-1.5 mb-2">
        <User className="w-3 h-3" style={{ color: "hsl(var(--text-muted))" }} />
        <span className="text-[11px]" style={{ color: "hsl(var(--text-secondary))" }}>
          {deal.contact_name || "No Contact"}
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
  onDeleteDeal
}: {
  stage: PipelineStage;
  onDragStart: (e: React.DragEvent, dealId: string, stageId: string) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, stageId: string) => void;
  onDeleteDeal: (dealId: string) => void;
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
          <DealCard key={deal.id} deal={deal} onDragStart={onDragStart} onDelete={onDeleteDeal} />
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
  const { stages, setStages, moveDeal, addDeal, removeDeal, contacts, setContacts } = useCRMStore();
  const [mounted, setMounted] = useState(false);
  const [dragInfo, setDragInfo] = useState<{ dealId: string; fromStageId: string } | null>(null);

  // Modal & Form States
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [selectedContactId, setSelectedContactId] = useState("");
  const [selectedStageId, setSelectedStageId] = useState("");
  const [newDealValue, setNewDealValue] = useState("5000");
  const [newSentiment, setNewSentiment] = useState<"positive" | "neutral" | "negative" | "unknown">("unknown");
  const [newNextAction, setNewNextAction] = useState("");

  const fetchContactsAndPipeline = async () => {
    try {
      // 1. Fetch contacts first to get the name/company detail mapping
      const contactsRes = await fetch(`${BACKEND_URL}/api/v1/crm/contacts`, {
        headers: getAuthHeaders()
      });
      let contactsList = [];
      if (contactsRes.ok) {
        contactsList = await contactsRes.json();
        setContacts(contactsList);
      }

      // 2. Fetch pipeline stage deals
      const pipelineRes = await fetch(`${BACKEND_URL}/api/v1/crm/pipeline`, {
        headers: getAuthHeaders()
      });
      if (pipelineRes.ok) {
        const data = await pipelineRes.json();
        const mapped = data.map((s: any) => ({
          id: String(s.stage_id),
          name: s.stage_name,
          position: s.position,
          probability_pct: s.probability_pct ?? 50,
          is_terminal: s.is_terminal ?? false,
          deals: (s.deals || []).map((d: any) => {
            const contact = contactsList.find((c: any) => c.id === d.contact_id);
            return {
              id: String(d.id),
              tenant_id: d.tenant_id,
              contact_id: String(d.contact_id || ""),
              contact_name: contact ? contact.full_name : "Unknown Contact",
              company_name: contact ? contact.company_name : "Unknown Company",
              stage_id: String(d.stage_id),
              stage_name: s.stage_name,
              title: d.title,
              value_usd: d.value_usd,
              currency: d.currency || "USD",
              close_date: d.close_date,
              ai_sentiment: d.ai_sentiment || "unknown",
              ai_next_action: d.ai_next_action,
              last_activity_date: d.updated_at || d.created_at,
              created_at: d.created_at,
            };
          }),
        }));
        setStages(mapped);
      }
    } catch (err) {
      console.warn("Failed to load pipeline dynamically:", err);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchContactsAndPipeline();
  }, [setStages, setContacts]);

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
    async (e: React.DragEvent, toStageId: string) => {
      e.preventDefault();
      if (dragInfo && dragInfo.fromStageId !== toStageId) {
        moveDeal(dragInfo.dealId, dragInfo.fromStageId, toStageId);
        
        try {
          const res = await fetch(`${BACKEND_URL}/api/v1/crm/deals/${dragInfo.dealId}`, {
            method: "PUT",
            headers: {
              ...getAuthHeaders(),
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              stage_id: toStageId
            })
          });
          if (!res.ok) {
            console.error("Failed to persist deal stage change to backend");
          }
        } catch (err) {
          console.warn("Failed to communicate deal stage change to backend:", err);
        }
      }
      setDragInfo(null);
    },
    [dragInfo, moveDeal]
  );

  const openAddDealModal = () => {
    if (contacts.length > 0) {
      setSelectedContactId(contacts[0].id);
    } else {
      setSelectedContactId("");
    }
    if (stages.length > 0) {
      setSelectedStageId(stages[0].id);
    } else {
      setSelectedStageId("");
    }
    setShowAddModal(true);
  };

  const handleAddDealSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !selectedContactId || !selectedStageId) {
      alert("Deal Title, Associated Contact, and Stage are required.");
      return;
    }

    const stage = stages.find((s) => s.id === selectedStageId);
    const contact = contacts.find((c) => c.id === selectedContactId);

    const payload = {
      tenant_id: "acme_tenant",
      contact_id: selectedContactId,
      stage_id: selectedStageId,
      title: newTitle.trim(),
      value_usd: parseFloat(newDealValue) || 0,
      currency: "USD",
      ai_sentiment: newSentiment,
      ai_next_action: newNextAction.trim() || undefined,
    };

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/crm/deals`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const savedDeal = await res.json();
        addDeal({
          ...savedDeal,
          contact_name: contact ? contact.full_name : "Unknown",
          company_name: contact ? contact.company_name : "Independent",
          stage_name: stage ? stage.name : "New Lead"
        });
      } else {
        console.error("Backend failed to save deal");
      }
    } catch (err) {
      console.warn("Failed to contact backend:", err);
    }

    // Reset
    setNewTitle("");
    setNewDealValue("5000");
    setNewNextAction("");
    setNewSentiment("unknown");
    setShowAddModal(false);
  };

  const handleDeleteDeal = async (id: string) => {
    if (!confirm("Are you sure you want to delete this deal?")) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/crm/deals/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      if (res.ok) {
        removeDeal(id);
      } else {
        console.error("Failed to delete deal on backend");
      }
    } catch (err) {
      console.warn("Failed to reach backend:", err);
    }
  };

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
          onClick={openAddDealModal}
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
            onDeleteDeal={handleDeleteDeal}
          />
        ))}
      </div>

      {/* Add Deal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div
            className="w-full max-w-md rounded-xl border p-6 space-y-4 shadow-2xl relative"
            style={{
              background: "hsl(var(--surface-1))",
              borderColor: "hsl(var(--border-subtle))",
            }}
          >
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute right-4 top-4 p-1.5 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: "hsl(var(--text-muted))" }}
            >
              <X className="w-4 h-4" />
            </button>

            <div>
              <h2 className="text-lg font-bold" style={{ color: "hsl(var(--text-primary))" }}>Add Pipeline Deal</h2>
              <p className="text-xs" style={{ color: "hsl(var(--text-muted))" }}>Log a new active deal and associate it with a contact.</p>
            </div>

            {contacts.length === 0 ? (
              <div
                className="flex items-start gap-2.5 p-3 rounded-lg border text-xs"
                style={{
                  background: "hsla(38, 92%, 50%, 0.05)",
                  borderColor: "hsla(38, 92%, 50%, 0.2)",
                  color: "#f59e0b"
                }}
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <div>
                  <p className="font-semibold">No contacts available</p>
                  <p className="mt-0.5">Please add a Contact in the Contacts directory before creating a pipeline deal.</p>
                </div>
              </div>
            ) : (
              <form onSubmit={handleAddDealSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Deal Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Wayne Security Suite Upgrade"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors"
                    style={{
                      background: "hsl(var(--surface-2))",
                      borderColor: "hsl(var(--border-subtle))",
                      color: "hsl(var(--text-primary))",
                    }}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Associated Contact *</label>
                  <div className="relative">
                    <select
                      value={selectedContactId}
                      onChange={(e) => setSelectedContactId(e.target.value)}
                      className="w-full pl-3 pr-8 py-2 rounded-lg text-sm border outline-none transition-colors cursor-pointer appearance-none"
                      style={{
                        background: "hsl(var(--surface-2))",
                        borderColor: "hsl(var(--border-subtle))",
                        color: "hsl(var(--text-primary))",
                      }}
                    >
                      {contacts.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.full_name} ({c.company_name || "Independent"})
                        </option>
                      ))}
                    </select>
                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-xs flex items-center" style={{ color: "hsl(var(--text-muted))" }}>
                      <ChevronDown className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Pipeline Stage *</label>
                  <div className="relative">
                    <select
                      value={selectedStageId}
                      onChange={(e) => setSelectedStageId(e.target.value)}
                      className="w-full pl-3 pr-8 py-2 rounded-lg text-sm border outline-none transition-colors cursor-pointer appearance-none"
                      style={{
                        background: "hsl(var(--surface-2))",
                        borderColor: "hsl(var(--border-subtle))",
                        color: "hsl(var(--text-primary))",
                      }}
                    >
                      {stages.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-xs flex items-center" style={{ color: "hsl(var(--text-muted))" }}>
                      <ChevronDown className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Value USD ($)</label>
                    <input
                      type="number"
                      min="0"
                      value={newDealValue}
                      onChange={(e) => setNewDealValue(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors text-center"
                      style={{
                        background: "hsl(var(--surface-2))",
                        borderColor: "hsl(var(--border-subtle))",
                        color: "hsl(var(--text-primary))",
                      }}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>AI Sentiment</label>
                    <div className="relative">
                      <select
                        value={newSentiment}
                        onChange={(e) => setNewSentiment(e.target.value as any)}
                        className="w-full pl-3 pr-8 py-2 rounded-lg text-sm border outline-none transition-colors cursor-pointer appearance-none capitalize text-center"
                        style={{
                          background: "hsl(var(--surface-2))",
                          borderColor: "hsl(var(--border-subtle))",
                          color: "hsl(var(--text-primary))",
                        }}
                      >
                        <option value="unknown">Unknown</option>
                        <option value="positive">Positive</option>
                        <option value="neutral">Neutral</option>
                        <option value="negative">Negative</option>
                      </select>
                      <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-xs flex items-center" style={{ color: "hsl(var(--text-muted))" }}>
                        <ChevronDown className="w-3.5 h-3.5" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>Next Action Summary</label>
                  <input
                    type="text"
                    placeholder="e.g. Schedule calendar meeting"
                    value={newNextAction}
                    onChange={(e) => setNewNextAction(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg text-sm border outline-none transition-colors"
                    style={{
                      background: "hsl(var(--surface-2))",
                      borderColor: "hsl(var(--border-subtle))",
                      color: "hsl(var(--text-primary))",
                    }}
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-lg text-xs font-semibold border transition-colors"
                    style={{
                      borderColor: "hsl(var(--border-default))",
                      color: "hsl(var(--text-secondary))",
                      background: "transparent",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-white transition-colors"
                    style={{
                      background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
                    }}
                  >
                    Save Deal
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
