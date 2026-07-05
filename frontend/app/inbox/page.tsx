"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Inbox, CheckCircle2, ShieldAlert, BrainCircuit, User, Building,
  Check, X, RefreshCw, Layers, History, Clock, Shield,
  GitCompare, Briefcase, Smile, Zap, CheckCheck
} from "lucide-react";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

interface Artifact {
  id: string;
  prospect_name: string;
  company_name: string;
  email_subject: string;
  email_body: string;
  confidence: number;
  cost_usd: number;
  pain_points: string[];
  reason_selected: string;
  expected_reply_rate: string;
  expected_meeting_prob: string;
  status: string;
  metadata?: {
    personalization_score?: number;
    business_brain_match?: number;
    spam_risk?: string;
    versions?: Array<{ version: number; subject: string; body: string; edited_by: string }>;
    alternatives?: Array<{ label: string; icon: string; email_subject: string; email_body: string }>;
  };
}

function ScoreRing({ value, label, color }: { value: number; label: string; color: string }) {
  const r = 20, circ = 2 * Math.PI * r, dash = (value / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="56" height="56" viewBox="0 0 56 56">
        <circle cx="28" cy="28" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
        <circle cx="28" cy="28" r={r} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={`${dash} ${circ - dash}`} strokeDashoffset={circ / 4} strokeLinecap="round" />
        <text x="28" y="33" textAnchor="middle" fill="white" fontSize="12" fontWeight="700">{value}</text>
      </svg>
      <span className="text-[10px] text-gray-400 text-center leading-tight">{label}</span>
    </div>
  );
}

function SpamBadge({ risk }: { risk: string }) {
  const map: Record<string, { color: string; bg: string }> = {
    Low: { color: "text-[#10B981]", bg: "bg-[#10B981]/10 border-[#10B981]/20" },
    Medium: { color: "text-amber-400", bg: "bg-amber-400/10 border-amber-400/20" },
    High: { color: "text-red-400", bg: "bg-red-400/10 border-red-400/20" },
  };
  const s = map[risk] || map.Low;
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${s.bg} ${s.color}`}><Shield className="w-3 h-3" /> {risk} Spam Risk</span>;
}

function readingTimeSec(text: string) {
  return Math.round((text.trim().split(/\s+/).length / 200) * 60);
}

function DiffView({ original, current }: { original: string; current: string }) {
  const origLines = original.split("\n"), currLines = current.split("\n");
  return (
    <div className="grid grid-cols-2 gap-2 text-xs font-mono rounded-lg overflow-hidden border border-white/10">
      <div className="bg-red-950/40 p-3">
        <div className="text-red-400 font-bold mb-2 text-[10px] uppercase tracking-wider">AI Original</div>
        {origLines.map((line, i) => <div key={i} className={`${currLines[i] !== line ? "text-red-300" : "text-gray-400"} leading-relaxed`}>{line || " "}</div>)}
      </div>
      <div className="bg-green-950/40 p-3">
        <div className="text-green-400 font-bold mb-2 text-[10px] uppercase tracking-wider">Your Edit</div>
        {currLines.map((line, i) => <div key={i} className={`${origLines[i] !== line ? "text-green-300" : "text-gray-400"} leading-relaxed`}>{line || " "}</div>)}
      </div>
    </div>
  );
}

export default function InboxPage() {
  const [pending, setPending] = useState<Artifact[]>([]);
  const [queued, setQueued] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editedBody, setEditedBody] = useState("");
  const [editedSubject, setEditedSubject] = useState("");
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [regenerateHint, setRegenerateHint] = useState("");
  const [showRegenerateInput, setShowRegenerateInput] = useState(false);
  const [generatingAlts, setGeneratingAlts] = useState(false);
  const [showAlts, setShowAlts] = useState(false);
  const [alts, setAlts] = useState<any[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchArtifacts = useCallback(async () => {
    try {
      setFetchError(false);
      const res = await fetch(`${BACKEND_URL}/api/analytics/inbox/artifacts`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        const all: Artifact[] = data.artifacts || [];
        setPending(all.filter(a => a.status === "WAITING_APPROVAL"));
        setQueued(all.filter(a => a.status === "QUEUED"));
      } else {
        setFetchError(true);
      }
    } catch (err) {
      console.error(err);
      setFetchError(true);
    }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchArtifacts(); }, [fetchArtifacts]);
  useEffect(() => { const t = setInterval(fetchArtifacts, 12000); return () => clearInterval(t); }, [fetchArtifacts]);

  const selected = pending.find(a => a.id === selectedId) || null;

  useEffect(() => {
    if (pending.length > 0 && !selectedId) setSelectedId(pending[0].id);
    if (pending.length === 0) setSelectedId(null);
  }, [pending, selectedId]);

  useEffect(() => {
    if (selected) {
      setEditedBody(selected.email_body || "");
      setEditedSubject(selected.email_subject || "");
      setIsDirty(false); setShowDiff(false); setShowAlts(false);
      setAlts(selected.metadata?.alternatives || []);
      setSelectedVersion(null); setShowRegenerateInput(false); setRegenerateHint("");
    }
  }, [selected?.id]);

  const autoSave = async (body: string, subject: string) => {
    if (!selectedId) return;
    setIsSaving(true);
    try {
      await fetch(`${BACKEND_URL}/api/analytics/inbox/artifacts/${selectedId}`, {
        method: "PATCH",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ email_body: body, email_subject: subject })
      });
    } finally { setIsSaving(false); }
  };

  const handleBodyChange = (val: string) => {
    setEditedBody(val); setIsDirty(true);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => autoSave(val, editedSubject), 1500);
  };

  const handleApprove = async (id: string) => {
    if (isDirty) await autoSave(editedBody, editedSubject);
    try {
      await fetch(`${BACKEND_URL}/api/analytics/inbox/artifacts/${id}/approve`, { method: "POST", headers: getAuthHeaders() });
    } catch (err) { console.error(err); }
    setPending(prev => {
      const removed = prev.find(a => a.id === id);
      if (removed) setQueued(q => [{ ...removed, status: "QUEUED" }, ...q]);
      const next = prev.filter(a => a.id !== id);
      setSelectedId(next[0]?.id || null);
      return next;
    });
  };

  const handleReject = async (id: string) => {
    try { await fetch(`${BACKEND_URL}/api/analytics/inbox/artifacts/${id}/reject`, { method: "POST", headers: getAuthHeaders() }); }
    catch (err) { console.error(err); }
    setPending(prev => { const next = prev.filter(a => a.id !== id); setSelectedId(next[0]?.id || null); return next; });
  };

  const handleApproveAll = async () => {
    try { await fetch(`${BACKEND_URL}/api/analytics/inbox/approve-batch`, { method: "POST", headers: getAuthHeaders() }); }
    catch (err) { console.error(err); }
    setQueued(q => [...pending.map(a => ({ ...a, status: "QUEUED" })), ...q]);
    setPending([]); setSelectedId(null);
  };

  const handleRegenerate = async () => {
    if (!selectedId) return;
    setRegenerating(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/analytics/inbox/artifacts/${selectedId}/regenerate`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ hint: regenerateHint || null })
      });
      if (res.ok) {
        const data = await res.json();
        setEditedBody(data.email_body || ""); setEditedSubject(data.email_subject || "");
        setIsDirty(false); setShowRegenerateInput(false); setRegenerateHint("");
        await fetchArtifacts();
      }
    } finally { setRegenerating(false); }
  };

  const handleGenerateAlts = async () => {
    if (!selectedId) return;
    setGeneratingAlts(true); setShowAlts(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/analytics/inbox/artifacts/${selectedId}/generate-alternatives`, {
        method: "POST", headers: getAuthHeaders()
      });
      if (res.ok) { const data = await res.json(); setAlts(data.alternatives || []); }
    } finally { setGeneratingAlts(false); }
  };

  const applyAlternative = (alt: { email_subject: string; email_body: string }) => {
    setEditedBody(alt.email_body); setEditedSubject(alt.email_subject); setIsDirty(true); setShowAlts(false);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => autoSave(alt.email_body, alt.email_subject), 800);
  };

  const meta = selected?.metadata;
  const personalization = meta?.personalization_score ?? selected?.confidence ?? 90;
  const brainMatch = meta?.business_brain_match ?? 90;
  const spamRisk = meta?.spam_risk ?? "Low";
  const versions = meta?.versions ?? [];
  const originalBody = versions.length > 0 ? versions[0].body : (selected?.email_body || "");
  const readTime = readingTimeSec(editedBody);
  const toneIcon: Record<string, React.ReactNode> = {
    Professional: <Briefcase className="w-3.5 h-3.5" />,
    Friendly: <Smile className="w-3.5 h-3.5" />,
    "Very Short": <Zap className="w-3.5 h-3.5" />,
  };

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a] overflow-hidden">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#00F0FF]/10 border border-[#00F0FF]/20 flex items-center justify-center">
            <Inbox className="w-4 h-4 text-[#00F0FF]" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-base">Approvals Inbox</h1>
            <p className="text-gray-500 text-xs">Review AI drafts before they enter the Ready to Send queue.</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {queued.length > 0 && (
            <div className="flex items-center gap-2 bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg px-3 py-1.5">
              <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
              <span className="text-sm font-semibold text-[#10B981]">{queued.length} Ready to Send</span>
            </div>
          )}
          {pending.length > 0 && (
            <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-semibold text-amber-400">{pending.length} Pending</span>
            </div>
          )}
          {pending.length > 1 && (
            <button onClick={handleApproveAll} className="flex items-center gap-2 bg-white text-black text-sm font-bold px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
              <CheckCheck className="w-4 h-4" /> Approve All
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      {loading ? (
        <div className="flex flex-col items-center justify-center h-[50vh] text-gray-500">
           <RefreshCw className="w-8 h-8 animate-spin text-[#00F0FF] mb-4" />
           <p>Syncing Inbox...</p>
        </div>
      ) : fetchError ? (
        <div className="flex flex-col items-center justify-center h-[50vh] text-gray-500">
           <ShieldAlert className="w-12 h-12 text-red-500 mb-4" />
           <p className="mb-4">Failed to load inbox.</p>
           <button onClick={() => { setLoading(true); fetchArtifacts(); }} className="px-4 py-2 bg-white text-black font-semibold rounded-lg hover:bg-gray-200">
             Retry
           </button>
        </div>
      ) : pending.length === 0 && queued.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="w-16 h-16 bg-[#10B981]/10 rounded-full flex items-center justify-center border border-[#10B981]/20">
            <CheckCircle2 className="w-8 h-8 text-[#10B981]" />
          </div>
          <h3 className="text-xl font-semibold text-white">Inbox Zero</h3>
          <p className="text-gray-500">All drafts reviewed. Launch a new mission to generate more.</p>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Email List */}
          <div className="w-[272px] flex-shrink-0 border-r border-white/[0.06] flex flex-col overflow-hidden">
            {pending.length > 0 && (
              <div className="flex-1 overflow-y-auto">
                <div className="px-4 pt-4 pb-2">
                  <span className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">Pending Review</span>
                </div>
                {pending.map((a) => (
                  <button key={a.id} onClick={() => setSelectedId(a.id)}
                    className={`w-full text-left px-4 py-3 border-b border-white/[0.04] transition-colors ${selectedId === a.id ? "bg-[#00F0FF]/[0.07] border-l-2 border-l-[#00F0FF]" : "hover:bg-white/[0.03]"}`}>
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="text-sm font-semibold text-white truncate">{a.prospect_name}</span>
                      <span className="text-[10px] text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded flex-shrink-0">Pending</span>
                    </div>
                    <div className="text-xs text-gray-400 truncate">{a.company_name}</div>
                    <div className="text-xs text-gray-600 truncate mt-0.5">{a.email_subject || "No subject"}</div>
                  </button>
                ))}
              </div>
            )}
            {queued.length > 0 && (
              <div className="border-t border-white/[0.06] flex-shrink-0 max-h-[180px] overflow-y-auto">
                <div className="px-4 pt-3 pb-2">
                  <span className="text-[10px] uppercase tracking-widest text-[#10B981] font-bold">✓ Ready to Send</span>
                </div>
                {queued.map((a) => (
                  <div key={a.id} className="px-4 py-2 border-b border-white/[0.04]">
                    <div className="text-sm text-gray-400 truncate">{a.prospect_name}</div>
                    <div className="text-xs text-gray-600 truncate">{a.company_name}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: Preview Panel */}
          {selected ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Email header */}
              <div className="px-6 py-4 border-b border-white/[0.06] flex-shrink-0 space-y-2">
                <input value={editedSubject}
                  onChange={(e) => { setEditedSubject(e.target.value); setIsDirty(true); }}
                  onBlur={() => isDirty && autoSave(editedBody, editedSubject)}
                  className="w-full text-white font-semibold text-base bg-transparent border-none outline-none focus:bg-white/5 rounded px-1 -mx-1 transition-colors"
                  placeholder="Email subject…" />
                <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1"><User className="w-3 h-3" /> To: <span className="text-gray-300 ml-1">{selected.prospect_name}</span></span>
                  <span className="flex items-center gap-1"><Building className="w-3 h-3" /> {selected.company_name}</span>
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> ~{readTime}s read</span>
                  <SpamBadge risk={spamRisk} />
                  {isSaving && <span className="text-gray-600 italic">Saving…</span>}
                  {isDirty && !isSaving && <span className="text-[#10B981]">● Edited</span>}
                </div>
              </div>

              {/* Confidence summary */}
              <div className="px-6 py-3 border-b border-white/[0.06] flex-shrink-0 flex items-center gap-6 bg-white/[0.015]">
                <ScoreRing value={personalization} label="Personalization" color="#00F0FF" />
                <ScoreRing value={brainMatch} label="Brain Match" color="#a855f7" />
                <ScoreRing value={selected.confidence ?? 90} label="AI Confidence" color="#10B981" />
                <div className="ml-auto grid grid-cols-2 gap-x-8 gap-y-1 text-xs">
                  <div className="text-gray-500">Expected Reply</div>
                  <div className="text-white font-semibold">{selected.expected_reply_rate || "—"}</div>
                  <div className="text-gray-500">Meeting Prob.</div>
                  <div className="text-white font-semibold">{selected.expected_meeting_prob || "—"}</div>
                  <div className="text-gray-500">AI Cost</div>
                  <div className="text-white font-semibold">${(selected.cost_usd ?? 0.04).toFixed(2)}</div>
                </div>
                {versions.length > 0 && (
                  <div className="ml-4 flex items-center gap-1 flex-shrink-0">
                    <History className="w-3.5 h-3.5 text-gray-500" />
                    <span className="text-[10px] text-gray-500 mr-1">Versions:</span>
                    {versions.map((v, idx) => (
                      <button key={idx}
                        onClick={() => { setSelectedVersion(idx); setEditedBody(v.body); setEditedSubject(v.subject); setIsDirty(false); }}
                        className={`w-6 h-6 rounded text-[10px] font-bold transition-colors ${selectedVersion === idx ? "bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/40" : "text-gray-500 hover:text-white hover:bg-white/10"}`}>
                        {v.version}
                      </button>
                    ))}
                    <button
                      onClick={() => { setSelectedVersion(null); setEditedBody(selected.email_body || ""); setEditedSubject(selected.email_subject || ""); setIsDirty(false); }}
                      className={`px-2 h-6 rounded text-[10px] font-bold transition-colors ${selectedVersion === null ? "bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/40" : "text-gray-500 hover:text-white hover:bg-white/10"}`}>
                      Current
                    </button>
                  </div>
                )}
              </div>

              {/* Pain points */}
              {selected.pain_points?.length > 0 && (
                <div className="px-6 py-2 border-b border-white/[0.06] flex-shrink-0 flex flex-wrap gap-2">
                  {selected.pain_points.map((pp, i) => <span key={i} className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded border border-red-500/20">{pp}</span>)}
                  {selected.reason_selected && <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded border border-purple-500/20 ml-auto max-w-xs truncate">{selected.reason_selected}</span>}
                </div>
              )}

              {/* Email body editor */}
              <div className="flex-1 overflow-y-auto px-6 py-4">
                {showDiff && isDirty ? (
                  <DiffView original={originalBody} current={editedBody} />
                ) : (
                  <textarea
                    value={editedBody}
                    onChange={(e) => handleBodyChange(e.target.value)}
                    className="w-full h-full min-h-[200px] bg-transparent text-gray-200 text-sm font-mono leading-relaxed resize-none outline-none border-none"
                    placeholder="Email body will appear here…"
                  />
                )}
              </div>

              {/* 3 Alternatives panel */}
              <AnimatePresence>
                {showAlts && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                    className="border-t border-white/[0.06] flex-shrink-0 overflow-hidden">
                    <div className="px-6 py-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Layers className="w-4 h-4 text-[#00F0FF]" />
                        <span className="text-sm font-semibold text-white">3 AI Alternatives</span>
                        {generatingAlts && <span className="text-xs text-gray-500 animate-pulse">Generating in parallel…</span>}
                        <button onClick={() => setShowAlts(false)} className="ml-auto text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        {generatingAlts ? [1,2,3].map(i => (
                          <div key={i} className="bg-white/5 rounded-xl p-3 animate-pulse space-y-2 border border-white/10">
                            <div className="h-3 bg-white/10 rounded w-24" />
                            <div className="h-16 bg-white/10 rounded" />
                          </div>
                        )) : alts?.map((alt, idx) => (
                          <div key={idx} className="bg-white/5 rounded-xl p-3 border border-white/10 hover:border-[#00F0FF]/30 transition-colors flex flex-col">
                            <div className="flex items-center gap-1.5 mb-2">
                              <span className="text-[#00F0FF]">{toneIcon[alt.label]}</span>
                              <span className="text-xs font-bold text-white">{alt.label}</span>
                            </div>
                            <p className="text-xs text-gray-400 line-clamp-4 font-mono mb-3 flex-1">{alt.email_body}</p>
                            <button onClick={() => applyAlternative(alt)}
                              className="w-full text-xs font-semibold text-black bg-white py-1.5 rounded-lg hover:bg-gray-100 transition-colors">
                              Use This Draft
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Regenerate hint input */}
              <AnimatePresence>
                {showRegenerateInput && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                    className="border-t border-white/[0.06] flex-shrink-0 px-6 py-3 flex gap-2 items-center overflow-hidden">
                    <input value={regenerateHint} onChange={(e) => setRegenerateHint(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleRegenerate()}
                      placeholder='Optional hint: "make it shorter", "more direct", "mention their Series A"…'
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-[#00F0FF]/40"
                      autoFocus />
                    <button onClick={handleRegenerate} disabled={regenerating}
                      className="px-4 py-2 bg-[#00F0FF]/10 border border-[#00F0FF]/30 text-[#00F0FF] text-sm font-semibold rounded-lg hover:bg-[#00F0FF]/20 transition-colors disabled:opacity-50">
                      {regenerating ? "Generating…" : "Regenerate"}
                    </button>
                    <button onClick={() => setShowRegenerateInput(false)} className="text-gray-500 hover:text-white"><X className="w-4 h-4" /></button>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Action bar */}
              <div className="flex-shrink-0 border-t border-white/[0.06] px-6 py-4 flex items-center gap-3">
                <button onClick={() => handleApprove(selected.id)}
                  className="flex items-center gap-2 bg-white text-black font-bold px-5 py-2.5 rounded-lg hover:bg-gray-100 transition-colors">
                  <Check className="w-4 h-4" /> Approve Draft
                </button>
                {isDirty && (
                  <button onClick={() => setShowDiff(!showDiff)}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${showDiff ? "bg-[#00F0FF]/10 border-[#00F0FF]/40 text-[#00F0FF]" : "border-white/10 text-gray-400 hover:text-white hover:border-white/20"}`}>
                    <GitCompare className="w-4 h-4" /> View AI Changes
                  </button>
                )}
                <button onClick={() => setShowRegenerateInput(!showRegenerateInput)} disabled={regenerating}
                  className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-white/10 text-gray-400 hover:text-white hover:border-white/20 text-sm font-medium transition-colors disabled:opacity-50">
                  <RefreshCw className={`w-4 h-4 ${regenerating ? "animate-spin" : ""}`} />
                  {regenerating ? "Regenerating…" : "Regenerate"}
                </button>
                <button onClick={showAlts ? () => setShowAlts(false) : handleGenerateAlts}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${showAlts ? "bg-purple-500/10 border-purple-500/40 text-purple-400" : "border-white/10 text-gray-400 hover:text-white hover:border-white/20"}`}>
                  <Layers className="w-4 h-4" /> 3 Alternatives
                </button>
                <div className="flex-1" />
                <button onClick={() => handleReject(selected.id)}
                  className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm font-medium transition-colors">
                  <X className="w-4 h-4" /> Reject
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-600">Select a draft to review</div>
          )}
        </div>
      )}
    </div>
  );
}
