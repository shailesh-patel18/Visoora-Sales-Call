"use client";

import React, { useState, useEffect } from "react";
import {
  Plus,
  Search,
  Building2,
  Mail,
  Phone,
  ShieldAlert,
  Sparkles,
  Play,
  Send,
  History,
  User,
  Clock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Bot,
  AlertTriangle,
  RefreshCw,
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
  const [reasoningText, setReasoningText] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [website, setWebsite] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [assignedAgentId, setAssignedAgentId] = useState("");

  // Loading states
  const [isIngesting, setIsIngesting] = useState(false);
  const [isDeciding, setIsDeciding] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [callSuccess, setCallSuccess] = useState<string | null>(null);

  const fetchLeads = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads`, {
        headers: { "X-Tenant-ID": "acme_tenant" },
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
        headers: { "X-Tenant-ID": "acme_tenant" },
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
    setReasoningText(null);
    setCallSuccess(null);

    // Fetch timeline
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${id}/timeline`, {
        headers: { "X-Tenant-ID": "acme_tenant" },
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
          "X-Tenant-ID": "acme_tenant",
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const newLead = await res.json();
        setLeads([newLead, ...leads]);
        setSelectedLeadId(newLead.id);
        setShowAddModal(false);
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

  // Run AI Decision reasoning
  const handleAnalyze = async () => {
    if (!selectedLeadId) return;
    setIsDeciding(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${selectedLeadId}/decide`, {
        method: "POST",
        headers: { "X-Tenant-ID": "acme_tenant" },
      });
      if (res.ok) {
        const data = await res.json();
        setDecision(data);
        setReasoningText(data.reason);
      }
    } catch (err) {
      console.error(err);
    }
    setIsDeciding(false);
  };

  // Execute AI action autonomously
  const handleExecute = async () => {
    if (!selectedLeadId) return;
    setIsExecuting(true);
    try {
      // 1. Analyze and decide
      const decideRes = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${selectedLeadId}/decide`, {
        method: "POST",
        headers: { "X-Tenant-ID": "acme_tenant" },
      });
      if (!decideRes.ok) throw new Error("AI analysis failed.");
      const nextDecision = await decideRes.json();
      setDecision(nextDecision);
      setReasoningText(nextDecision.reason);

      if (nextDecision.action === "send_email" || nextDecision.should_send) {
        // Send email automatically
        const sendRes = await fetch(`${BACKEND_URL}/api/v1/sales-employee/leads/${selectedLeadId}/emails/send`, {
          method: "POST",
          headers: { "X-Tenant-ID": "acme_tenant" },
        });
        if (sendRes.ok) {
          alert("AI outbound email sent successfully!");
          fetchLeadDetails(selectedLeadId);
        } else {
          const err = await sendRes.json();
          alert(`Email dispatch failed: ${err.detail}`);
        }
      } else if (nextDecision.action === "call") {
        // AI recommends phone call next
        handleCall();
      } else {
        alert(`AI next action: ${nextDecision.action}. Reasoning: ${nextDecision.reason}`);
      }
    } catch (err: any) {
      console.error(err);
      alert(`Strategy execution error: ${err.message}`);
    }
    setIsExecuting(false);
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
          company: selectedLead.company_name,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCallSuccess(`Call initiated! SID: ${data.call_sid}`);
        // Refresh timeline
        setTimeout(() => fetchLeadDetails(selectedLead.id), 2000);
      } else {
        alert("Failed to initiate outbound call.");
      }
    } catch (err) {
      console.error(err);
    }
    setIsCalling(false);
  };

  // Simulating events via helper webhooks for QA verification
  const triggerQAEvent = async (eventType: string) => {
    if (!selectedLeadId) return;
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/v1/sales-employee/webhooks/mailbox/test-event?lead_id=${selectedLeadId}&event_type=${eventType}`,
        {
          method: "POST",
          headers: { "X-Tenant-ID": "acme_tenant" },
        }
      );
      if (res.ok) {
        alert(`Simulated inbound ${eventType} registered!`);
        fetchLeadDetails(selectedLeadId);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">AI outreach Command center</h1>
          <p className="text-sm mt-0.5 text-neutral-400">
            Import leads, view company briefs, audit strategy recommendations, and manage the intelligent follow-up lifecycle.
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
        {/* Leads List */}
        <div className="lg:col-span-1 rounded-xl border border-neutral-800 p-5 bg-neutral-950 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-1.5">
            <UsersIcon className="w-4 h-4 text-neutral-400" /> Ingested Leads
          </h2>
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {leads.length === 0 ? (
              <p className="text-xs text-neutral-500">No leads imported yet.</p>
            ) : (
              leads.map((l) => (
                <div
                  key={l.id}
                  onClick={() => setSelectedLeadId(l.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all hover:bg-white/[0.01] flex justify-between items-center ${
                    selectedLeadId === l.id ? "border-[hsl(var(--brand-primary))] bg-neutral-900" : "border-neutral-800 bg-neutral-900/40"
                  }`}
                >
                  <div>
                    <h3 className="text-xs font-bold text-white">{l.name}</h3>
                    <p className="text-[10px] text-neutral-400 mt-0.5">{l.company_name}</p>
                  </div>
                  <span
                    className="text-[9px] font-bold px-2 py-0.5 rounded-full"
                    style={{
                      background: l.needs_review ? "rgba(239, 68, 68, 0.1)" : "rgba(34, 197, 94, 0.1)",
                      color: l.needs_review ? "#ef4444" : "#22c55e",
                    }}
                  >
                    {l.needs_review ? "Needs Review" : `Conf: ${l.research_confidence}`}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Lead View and AI Panel */}
        <div className="lg:col-span-2 space-y-6">
          {selectedLead ? (
            <>
              {/* Profile Details & Research Brief */}
              <div className="rounded-xl border border-neutral-800 p-6 bg-neutral-950 flex flex-col gap-4">
                <div className="flex justify-between items-center pb-3 border-b border-neutral-800">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                      <User className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-white">{selectedLead.name}</h2>
                      <p className="text-[11px] text-neutral-400">{selectedLead.company_name}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <a
                      href={`mailto:${selectedLead.email}`}
                      className="p-2 rounded bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-white"
                      title={selectedLead.email}
                    >
                      <Mail className="w-4 h-4" />
                    </a>
                    <a
                      href={`tel:${selectedLead.phone}`}
                      className="p-2 rounded bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-white"
                      title={selectedLead.phone}
                    >
                      <Phone className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {selectedLead.research_brief && (
                  <div className="rounded-lg p-4 bg-neutral-900/60 border border-neutral-800">
                    <div className="flex items-center gap-1.5 mb-2 text-emerald-400">
                      <Sparkles className="w-4 h-4 animate-pulse" />
                      <h3 className="text-xs font-bold uppercase tracking-wider text-white">Research Grounding Brief</h3>
                    </div>
                    <p className="text-xs text-neutral-300 leading-relaxed mb-4">
                      {selectedLead.research_brief.company_summary}
                    </p>

                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-[9px] font-bold text-neutral-400 uppercase">Target Pain Points</span>
                        <ul className="list-disc pl-4 text-white mt-1 space-y-0.5">
                          {selectedLead.research_brief.likely_pain_points?.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-[9px] font-bold text-neutral-400 uppercase">Personalization hooks</span>
                        <ul className="list-disc pl-4 text-white mt-1 space-y-0.5">
                          {selectedLead.research_brief.personalization_hooks?.map((p) => (
                            <li key={p}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* AI Outreach Strategy Engine */}
              <div className="rounded-xl border border-neutral-800 p-6 bg-neutral-950 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">AI strategy decision engine</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={handleAnalyze}
                      disabled={isDeciding || isExecuting}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-white flex items-center gap-1.5"
                    >
                      <Bot className="w-3.5 h-3.5 text-blue-400" /> Analyze Strategy
                    </button>
                    <button
                      onClick={handleExecute}
                      disabled={isExecuting || isDeciding}
                      className="px-4 py-1.5 rounded-lg text-xs font-bold text-white flex items-center gap-1.5"
                      style={{ background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))" }}
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      {isExecuting ? "Executing Strategy..." : "Run AI Strategy Loop"}
                    </button>
                  </div>
                </div>

                {reasoningText && (
                  <div className="p-4 rounded-lg bg-neutral-900 border border-neutral-800 space-y-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold uppercase text-[hsl(var(--brand-primary))]">Next Recommended Action:</span>
                      <span className="text-xs font-bold text-white capitalize">{decision?.action?.replace(/_/g, " ")}</span>
                    </div>
                    <p className="text-xs text-neutral-300"><strong>Explainable Reasoning:</strong> {reasoningText}</p>
                  </div>
                )}

                {/* Simulated webhook tools for testing */}
                <div className="border-t border-neutral-800 pt-4">
                  <h4 className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider mb-2">Simulate inbound signals (QA Verification)</h4>
                  <div className="flex gap-2">
                    <button
                      onClick={() => triggerQAEvent("open")}
                      className="px-3 py-1.5 rounded bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 text-[11px] font-semibold"
                    >
                      Simulate Open Event
                    </button>
                    <button
                      onClick={() => triggerQAEvent("reply")}
                      className="px-3 py-1.5 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-semibold"
                    >
                      Simulate Inbound Reply
                    </button>
                    <button
                      onClick={() => triggerQAEvent("bounce")}
                      className="px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-[11px] font-semibold"
                    >
                      Simulate Email Bounce
                    </button>
                  </div>
                </div>

                <div className="border-t border-neutral-800 pt-4 flex flex-col gap-2">
                  <button
                    onClick={handleCall}
                    disabled={isCalling}
                    className="w-full py-2.5 rounded-lg text-xs font-bold text-white transition-all flex items-center justify-center gap-1.5"
                    style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
                  >
                    <Play className="w-3.5 h-3.5" />
                    {isCalling ? "Dialing..." : "Manual Outbound Call"}
                  </button>
                  {callSuccess && (
                    <p className="text-center text-xs font-semibold text-emerald-400 mt-1">{callSuccess}</p>
                  )}
                </div>
              </div>

              {/* Communication Timeline */}
              <div className="rounded-xl border border-neutral-800 p-6 bg-neutral-950 flex flex-col gap-4">
                <div className="flex items-center gap-2 mb-1">
                  <History className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Communication Timeline</h3>
                </div>

                <div className="space-y-4">
                  {timeline.length === 0 ? (
                    <p className="text-xs text-neutral-500">No interaction history registered for this lead.</p>
                  ) : (
                    timeline.map((event) => (
                      <div key={event.id} className="flex gap-3 relative pb-2 border-b border-neutral-900 last:border-0">
                        <div className="w-6 h-6 rounded-full bg-neutral-900 border border-neutral-800 flex items-center justify-center flex-shrink-0 text-xs">
                          {event.channel === "email" ? "✉️" : "📞"}
                        </div>
                        <div className="text-xs flex-1">
                          <div className="flex justify-between items-center">
                            <p className="font-semibold text-white capitalize">
                              {event.direction} {event.channel} touchpoint {event.status}
                            </p>
                            <span className="text-[10px] text-neutral-500">
                              {new Date(event.created_at).toLocaleString()}
                            </span>
                          </div>
                          {event.metadata && event.metadata.draft && (
                            <div className="mt-2 p-2 rounded bg-neutral-900 text-[10px] text-neutral-300 font-mono whitespace-pre-line leading-normal">
                              {event.metadata.draft.body}
                            </div>
                          )}
                          {event.metadata && event.metadata.reply_body && (
                            <div className="mt-2 p-2 rounded bg-emerald-950/20 border border-emerald-950 text-[10px] text-emerald-300 font-mono whitespace-pre-line leading-normal">
                              {event.metadata.reply_body}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-xl border border-neutral-800 p-12 text-center bg-neutral-950 text-neutral-400">
              <p className="text-xs">Select a lead from the list to view target research brief and trigger outreach strategy.</p>
            </div>
          )}
        </div>
      </div>

      {/* Import Lead Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-[480px] rounded-2xl border p-6 shadow-2xl bg-neutral-950 border-neutral-800 text-xs text-white">
            <h2 className="text-lg font-bold text-white mb-4">Import Outbound Lead</h2>
            
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <span className="text-neutral-400">Full Name</span>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-neutral-400">Company Name</span>
                  <input
                    type="text"
                    required
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <span className="text-neutral-400">Website URL (e.g. google.com)</span>
                <input
                  type="text"
                  required
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <span className="text-neutral-400">Email Address</span>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-neutral-400">Phone (E.164 format, e.g. +19195551234)</span>
                  <input
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-neutral-800 bg-neutral-900 text-white outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <span className="text-neutral-400">Assigned Agent (Sales Brain)</span>
                <select
                  value={assignedAgentId}
                  onChange={(e) => setAssignedAgentId(e.target.value)}
                  className="w-full bg-neutral-900 border border-neutral-800 rounded py-2 px-3 outline-none text-white font-medium"
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
                  className="px-4 py-2 rounded border border-neutral-800 hover:bg-neutral-900 text-neutral-400"
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

function UsersIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
