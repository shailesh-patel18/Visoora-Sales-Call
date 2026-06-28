"use client";

import React, { useState, useEffect } from "react";
import {
  Plus, Search, Building2, Mail, Phone, ShieldAlert, Sparkles, Play,
  Send, History, User, Clock, ArrowRight, AlertCircle, CheckCircle2, Bot
} from "lucide-react";
import { BACKEND_URL } from "../config";

interface Lead {
  id: string;
  name: string;
  company_name: string;
  website: string;
  email: string;
  phone: string;
  agent_id: string;
  research_brief?: {
    company_summary?: string;
    likely_pain_points?: string[];
    personalization_hooks?: string[];
    domain_mismatches?: string[];
  };
  research_confidence: number;
  needs_review: boolean;
}

interface Agent {
  id: string;
  name: string;
}

interface TimelineEvent {
  id: string;
  channel: string;
  direction: string;
  status: string;
  created_at: string;
  metadata?: any;
}

export default function CampaignsPage() {
  const [mounted, setMounted] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  
  // Selection details
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [decision, setDecision] = useState<any>(null);
  const [draft, setDraft] = useState<any>(null);
  
  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [website, setWebsite] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [assignedAgentId, setAssignedAgentId] = useState("");
  
  // Actions loading states
  const [isIngesting, setIsIngesting] = useState(false);
  const [isDeciding, setIsDeciding] = useState(false);
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [callSuccess, setCallSuccess] = useState<string | null>(null);

  const fetchLeads = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads`, {
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        setLeads(data);
        if (data.length > 0 && !selectedLeadId) {
          setSelectedLeadId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch leads:", err);
    }
  };

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/agents`, {
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
        if (data.length > 0) {
          setAssignedAgentId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch agents:", err);
    }
  };

  const fetchLeadDetails = async (id: string) => {
    const lead = leads.find((l) => l.id === id);
    if (!lead) return;
    setSelectedLead(lead);
    setDecision(null);
    setDraft(null);
    setCallSuccess(null);

    // Fetch timeline
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${id}/timeline`, {
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        setTimeline(data);
      }
    } catch (err) {
      console.error("Failed to fetch timeline:", err);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchLeads();
    fetchAgents();
  }, []);

  // Update lead details when leads list or selected ID shifts
  useEffect(() => {
    if (selectedLeadId && leads.length > 0) {
      fetchLeadDetails(selectedLeadId);
    }
  }, [selectedLeadId, leads]);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !company || !website || !email || !phone || !assignedAgentId) {
      alert("All fields are required.");
      return;
    }
    setIsIngesting(true);
    const payload = {
      agent_id: assignedAgentId,
      name,
      company_name: company,
      website,
      email,
      phone,
    };
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": "acme_tenant"
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const newLead = await res.json();
        setLeads([newLead, ...leads]);
        setSelectedLeadId(newLead.id);
        setShowAddModal(false);
        // Clear inputs
        setName("");
        setCompany("");
        setWebsite("");
        setEmail("");
        setPhone("");
      } else {
        const errData = await res.json();
        alert(`Validation error: ${JSON.stringify(errData.detail)}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to ingest lead.");
    }
    setIsIngesting(false);
  };

  const handleDecide = async () => {
    if (!selectedLeadId) return;
    setIsDeciding(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${selectedLeadId}/decide`, {
        method: "POST",
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        setDecision(data);
      }
    } catch (err) {
      console.error(err);
    }
    setIsDeciding(false);
  };

  const handleDraft = async () => {
    if (!selectedLeadId) return;
    setIsDrafting(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${selectedLeadId}/emails/draft`, {
        method: "POST",
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        const data = await res.json();
        setDraft(data);
      }
    } catch (err) {
      console.error(err);
    }
    setIsDrafting(false);
  };

  const handleSendEmail = async () => {
    if (!selectedLeadId) return;
    setIsSending(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${selectedLeadId}/emails/send`, {
        method: "POST",
        headers: { "X-Tenant-ID": "acme_tenant" }
      });
      if (res.ok) {
        alert("Email sent successfully!");
        fetchLeadDetails(selectedLeadId);
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail || "Failed to send email"}`);
      }
    } catch (err) {
      console.error(err);
    }
    setIsSending(false);
  };

  const handleCall = async () => {
    if (!selectedLead) return;
    setIsCalling(true);
    setCallSuccess(null);
    try {
      const res = await fetch(`${BACKEND_URL}/make-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: selectedLead.phone,
          name: selectedLead.name,
          company: selectedLead.company_name
        })
      });
      if (res.ok) {
        const data = await res.json();
        setCallSuccess(`Call initiated! SID: ${data.call_sid}`);
      } else {
        alert("Failed to initiate Twilio call.");
      }
    } catch (err) {
      console.error(err);
    }
    setIsCalling(false);
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Campaign & Leads Console</h1>
          <p className="text-sm mt-0.5 text-[hsl(var(--text-muted))]">
            Import leads, view RAG grounding briefs, and govern autonomous multi-channel strategy execution.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all"
          style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
        >
          <Plus className="w-3.5 h-3.5" /> Import New Lead
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leads Column (Left) */}
        <div className="lg:col-span-1 rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
          <h2 className="text-sm font-semibold text-white">Ingested Leads</h2>
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {leads.length === 0 ? (
              <p className="text-xs text-[hsl(var(--text-muted))]">No leads imported yet.</p>
            ) : (
              leads.map((l) => (
                <div
                  key={l.id}
                  onClick={() => setSelectedLeadId(l.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all hover:bg-white/[0.01] flex justify-between items-center ${
                    selectedLeadId === l.id ? "ring-1" : ""
                  }`}
                  style={{
                    background: selectedLeadId === l.id ? "hsl(var(--surface-2))" : "hsl(var(--surface-2))",
                    borderColor: selectedLeadId === l.id ? "hsl(var(--brand-primary))" : "hsl(var(--border-subtle))",
                  }}
                >
                  <div>
                    <h3 className="text-xs font-bold text-white">{l.name}</h3>
                    <p className="text-[10px] text-[hsl(var(--text-muted))] mt-0.5">{l.company_name}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span
                      className="text-[9px] font-bold px-2 py-0.5 rounded-full"
                      style={{
                        background: l.needs_review ? "hsla(0, 100%, 50%, 0.1)" : "hsla(142, 71%, 45%, 0.1)",
                        color: l.needs_review ? "#ef4444" : "#22c55e",
                      }}
                    >
                      {l.needs_review ? "Needs Review" : `Conf: ${l.research_confidence}`}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Lead Details Column (Right 2) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {selectedLead ? (
            <>
              {/* Profile details */}
              <div className="rounded-xl border p-6 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                <div className="flex justify-between items-center pb-3 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[hsla(var(--brand-primary),0.1)] flex items-center justify-center">
                      <User className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-white">{selectedLead.name}</h2>
                      <p className="text-[11px] text-[hsl(var(--text-muted))]">{selectedLead.company_name}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href={`mailto:${selectedLead.email}`}
                      className="p-2 rounded bg-[hsl(var(--surface-3))] text-[hsl(var(--text-secondary))] hover:text-white"
                      title={selectedLead.email}
                    >
                      <Mail className="w-4 h-4" />
                    </a>
                    <a
                      href={`tel:${selectedLead.phone}`}
                      className="p-2 rounded bg-[hsl(var(--surface-3))] text-[hsl(var(--text-secondary))] hover:text-white"
                      title={selectedLead.phone}
                    >
                      <Phone className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[10px] text-neutral-400 font-semibold uppercase">Website</span>
                    <p className="text-white font-medium mt-0.5">{selectedLead.website}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-neutral-400 font-semibold uppercase">Assigned Agent</span>
                    <p className="text-white font-medium mt-0.5">
                      {agents.find((a) => a.id === selectedLead.agent_id)?.name || "Unknown"}
                    </p>
                  </div>
                </div>

                {/* Research brief details */}
                {selectedLead.research_brief && (
                  <div className="rounded-lg p-4 mt-2" style={{ background: "hsl(var(--surface-2))" }}>
                    <div className="flex items-center gap-1.5 mb-2">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <h3 className="text-xs font-bold text-white">Automated Web Research summary</h3>
                    </div>
                    
                    <p className="text-xs text-[hsl(var(--text-secondary))] mb-3">
                      {selectedLead.research_brief.company_summary}
                    </p>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-[9px] font-bold text-neutral-400 uppercase">Likely Pain Points</span>
                        <ul className="list-disc pl-4 text-[11px] text-white mt-1 space-y-0.5">
                          {selectedLead.research_brief.likely_pain_points?.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-[9px] font-bold text-neutral-400 uppercase">Personalization hooks</span>
                        <ul className="list-disc pl-4 text-[11px] text-white mt-1 space-y-0.5">
                          {selectedLead.research_brief.personalization_hooks?.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {selectedLead.research_brief.domain_mismatches && selectedLead.research_brief.domain_mismatches.length > 0 && (
                      <div className="mt-3 flex items-start gap-1.5 text-[11px] text-amber-400 border border-amber-400/20 p-2.5 rounded bg-amber-400/5">
                        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold">Consistency Mismatches Warning</p>
                          <ul className="list-disc pl-4 mt-0.5">
                            {selectedLead.research_brief.domain_mismatches.map((m) => (
                              <li key={m}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Strategy Engine Actions */}
              <div className="rounded-xl border p-6 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Outreach strategy engine</h3>
                
                <div className="flex gap-3">
                  <button
                    onClick={handleDecide}
                    disabled={isDeciding}
                    className="flex-1 py-2.5 rounded-lg text-xs font-semibold text-white bg-[hsl(var(--surface-3))] hover:bg-[hsl(var(--surface-4))] transition-all flex items-center justify-center gap-1.5"
                  >
                    <Bot className="w-3.5 h-3.5 text-[hsl(var(--brand-primary))]" />
                    {isDeciding ? "Analyzing..." : "Analyze Next Step"}
                  </button>

                  <button
                    onClick={handleDraft}
                    disabled={isDrafting}
                    className="flex-1 py-2.5 rounded-lg text-xs font-semibold text-white bg-[hsl(var(--surface-3))] hover:bg-[hsl(var(--surface-4))] transition-all flex items-center justify-center gap-1.5"
                  >
                    <Mail className="w-3.5 h-3.5 text-blue-400" />
                    {isDrafting ? "Drafting..." : "Generate Email Draft"}
                  </button>
                </div>

                {decision && (
                  <div className="p-4 rounded-lg flex flex-col gap-2 bg-[hsla(var(--brand-primary),0.03)] border border-[hsla(var(--brand-primary),0.15)]">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] uppercase font-bold text-[hsl(var(--brand-primary))]">Recommended Action:</span>
                      <span className="text-xs font-bold text-white capitalize">{decision.action.replace(/_/g, " ")}</span>
                    </div>
                    <p className="text-xs text-[hsl(var(--text-secondary))]"><strong>Reasoning:</strong> {decision.reason}</p>
                    
                    {decision.should_send && (
                      <button
                        onClick={handleSendEmail}
                        disabled={isSending}
                        className="mt-2 py-2 rounded-lg text-xs font-semibold text-white bg-[hsl(var(--brand-primary))] flex items-center justify-center gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        {isSending ? "Sending Outbound Email..." : "Authorize Email Dispatch"}
                      </button>
                    )}
                  </div>
                )}

                {draft && (
                  <div className="p-4 rounded-lg bg-neutral-900 border text-xs space-y-3">
                    <p className="text-neutral-400 font-bold">Email Subject: <span className="text-white font-normal">{draft.subject}</span></p>
                    <div className="p-3 rounded bg-black/40 text-neutral-300 font-mono text-[11px] whitespace-pre-line leading-relaxed">
                      {draft.body}
                    </div>
                  </div>
                )}

                <div className="border-t pt-4 flex flex-col gap-3" style={{ borderColor: "hsl(var(--border-subtle))" }}>
                  <button
                    onClick={handleCall}
                    disabled={isCalling}
                    className="w-full py-2.5 rounded-lg text-xs font-bold text-white transition-all flex items-center justify-center gap-1.5"
                    style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
                  >
                    <Play className="w-3.5 h-3.5" />
                    {isCalling ? "Dialing Lead..." : "Initiate Outbound Voice Call Now"}
                  </button>
                  {callSuccess && (
                    <p className="text-center text-xs font-semibold text-emerald-400 mt-1">{callSuccess}</p>
                  )}
                </div>
              </div>

              {/* Timeline feed */}
              <div className="rounded-xl border p-6 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                <div className="flex items-center gap-2 mb-1">
                  <History className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Interaction timeline history</h3>
                </div>

                <div className="space-y-4">
                  {timeline.length === 0 ? (
                    <p className="text-xs text-[hsl(var(--text-muted))]">No interaction history registered for this lead.</p>
                  ) : (
                    timeline.map((event) => (
                      <div key={event.id} className="flex gap-3 relative pb-2">
                        <div className="w-6 h-6 rounded-full bg-[hsl(var(--surface-3))] flex items-center justify-center flex-shrink-0 text-xs">
                          {event.channel === "email" ? "✉️" : "📞"}
                        </div>
                        <div className="text-xs">
                          <p className="font-semibold text-white capitalize">
                            {event.direction} {event.channel} Outreach {event.status}
                          </p>
                          <p className="text-[10px] text-[hsl(var(--text-muted))]">
                            {new Date(event.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-xl border p-12 text-center" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
              <p className="text-xs text-[hsl(var(--text-muted))]">Select a lead to audit research summary and trigger outreach.</p>
            </div>
          )}
        </div>
      </div>

      {/* Import Lead Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-[480px] rounded-2xl border p-6 shadow-2xl" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <h2 className="text-lg font-bold text-white mb-4">Import Outbound Lead</h2>
            
            <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <span className="text-neutral-400">Full Name</span>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 rounded border outline-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-neutral-400">Company Name</span>
                  <input
                    type="text"
                    required
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full px-3 py-2 rounded border outline-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-neutral-400">Website URL (e.g. google.com)</span>
                <input
                  type="text"
                  required
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="w-full px-3 py-2 rounded border outline-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <span className="text-neutral-400">Email Address</span>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 rounded border outline-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-neutral-400">Phone (E.164 e.g. +9198244...)</span>
                  <input
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full px-3 py-2 rounded border outline-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-neutral-400">Assigned Agent (Sales Brain)</span>
                <select
                  value={assignedAgentId}
                  onChange={(e) => setAssignedAgentId(e.target.value)}
                  className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded py-2 px-3 outline-none"
                >
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 justify-end pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded border hover:bg-neutral-800 text-neutral-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isIngesting}
                  className="px-4 py-2 rounded text-white font-semibold transition-all"
                  style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
                >
                  {isIngesting ? "Researching & Ingesting..." : "Ingest Lead"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
