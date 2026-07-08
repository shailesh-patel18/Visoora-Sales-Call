"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

interface Evidence {
    step: string;
    detail: string;
}

interface Draft {
    id: string;
    lead_id: string;
    subject: string;
    body: string;
    evidence_log: Evidence[];
    status: string;
}

export default function CockpitPage() {
    const [drafts, setDrafts] = useState<Draft[]>([]);
    const [selectedDraftId, setSelectedDraftId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    
    // Editable state for the selected draft
    const [editSubject, setEditSubject] = useState("");
    const [editBody, setEditBody] = useState("");

    useEffect(() => {
        fetchDrafts();
    }, []);

    const fetchDrafts = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${BACKEND_URL}/api/v1/drafts`, {
                headers: getAuthHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setDrafts(data);
                if (data.length > 0 && !selectedDraftId) {
                    selectDraft(data[0]);
                }
            }
        } catch (err) {
            console.error("Failed to fetch drafts", err);
        } finally {
            setLoading(false);
        }
    };

    const selectDraft = (draft: Draft) => {
        setSelectedDraftId(draft.id);
        setEditSubject(draft.subject);
        setEditBody(draft.body);
    };

    const handleApprove = async () => {
        if (!selectedDraftId) return;
        setSaving(true);
        try {
            // First save any edits
            await fetch(`${BACKEND_URL}/api/v1/drafts/${selectedDraftId}`, {
                method: "PUT",
                headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
                body: JSON.stringify({ subject: editSubject, body: editBody })
            });
            // Then approve
            await fetch(`${BACKEND_URL}/api/v1/drafts/${selectedDraftId}/approve`, {
                method: "POST",
                headers: getAuthHeaders()
            });
            
            // Remove from list
            setDrafts(prev => prev.filter(d => d.id !== selectedDraftId));
            setSelectedDraftId(null);
            
            // Select next if available
            const remaining = drafts.filter(d => d.id !== selectedDraftId);
            if (remaining.length > 0) {
                selectDraft(remaining[0]);
            }
        } catch (err) {
            console.error("Failed to approve", err);
        } finally {
            setSaving(false);
        }
    };

    const handleReject = async () => {
        if (!selectedDraftId) return;
        setSaving(true);
        try {
            await fetch(`${BACKEND_URL}/api/v1/drafts/${selectedDraftId}/reject`, {
                method: "POST",
                headers: getAuthHeaders()
            });
            setDrafts(prev => prev.filter(d => d.id !== selectedDraftId));
            setSelectedDraftId(null);
            const remaining = drafts.filter(d => d.id !== selectedDraftId);
            if (remaining.length > 0) {
                selectDraft(remaining[0]);
            }
        } catch (err) {
            console.error("Failed to reject", err);
        } finally {
            setSaving(false);
        }
    };

    const selectedDraft = drafts.find(d => d.id === selectedDraftId);

    return (
        <div className="flex h-[calc(100vh-80px)] bg-[#0a0a0a] text-white overflow-hidden">
            {/* Left Pane: Inbox */}
            <div className="w-1/3 border-r border-white/10 flex flex-col bg-[#111]">
                <div className="p-6 border-b border-white/10">
                    <h1 className="text-xl font-bold flex items-center gap-2">
                        <span className="text-[#00F0FF]">Approval Cockpit</span>
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">Review AI-generated drafts before dispatch.</p>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                    {loading ? (
                        <div className="text-center text-gray-500 p-8">Loading drafts...</div>
                    ) : drafts.length === 0 ? (
                        <div className="text-center text-gray-500 p-8 border border-white/5 rounded-xl border-dashed">
                            No pending drafts. Your inbox is clean!
                        </div>
                    ) : (
                        drafts.map((draft) => (
                            <motion.button
                                key={draft.id}
                                onClick={() => selectDraft(draft)}
                                className={`w-full text-left p-4 rounded-xl transition-all border ${
                                    selectedDraftId === draft.id 
                                        ? 'bg-[#00F0FF]/10 border-[#00F0FF]/50 shadow-[0_0_15px_rgba(0,240,255,0.1)]' 
                                        : 'bg-black/40 border-white/5 hover:border-white/20'
                                }`}
                            >
                                <div className="text-xs text-gray-400 mb-1 uppercase tracking-wider font-semibold">
                                    Lead ID: {draft.lead_id.substring(0, 8)}
                                </div>
                                <div className={`font-medium truncate ${selectedDraftId === draft.id ? 'text-[#00F0FF]' : 'text-gray-200'}`}>
                                    {draft.subject}
                                </div>
                                <div className="text-sm text-gray-500 truncate mt-1">
                                    {draft.body.substring(0, 60)}...
                                </div>
                            </motion.button>
                        ))
                    )}
                </div>
            </div>

            {/* Right Pane: Editor & Replay */}
            <div className="w-2/3 flex flex-col relative bg-[#0a0a0a]">
                {selectedDraft ? (
                    <AnimatePresence mode="wait">
                        <motion.div 
                            key={selectedDraft.id}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="flex flex-col h-full"
                        >
                            {/* Toolbar */}
                            <div className="p-4 border-b border-white/10 flex justify-between items-center bg-[#111]">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                                    <span className="text-sm font-medium text-yellow-500 uppercase tracking-widest">Pending Review</span>
                                </div>
                                <div className="flex gap-3">
                                    <button 
                                        onClick={handleReject}
                                        disabled={saving}
                                        className="px-6 py-2 rounded-lg text-red-400 hover:bg-red-500/10 font-medium transition-colors"
                                    >
                                        Reject
                                    </button>
                                    <button 
                                        onClick={handleApprove}
                                        disabled={saving}
                                        className="px-8 py-2 rounded-lg bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] text-black font-bold hover:opacity-90 shadow-[0_0_20px_rgba(0,240,255,0.3)] transition-all"
                                    >
                                        {saving ? "Processing..." : "Approve & Send"}
                                    </button>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-8 flex gap-8">
                                {/* Editor */}
                                <div className="flex-1 space-y-6">
                                    <div>
                                        <label className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-2 block">Subject Line</label>
                                        <input 
                                            type="text" 
                                            value={editSubject}
                                            onChange={(e) => setEditSubject(e.target.value)}
                                            className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00F0FF] transition-colors font-medium text-lg"
                                        />
                                    </div>
                                    <div className="flex-1 flex flex-col h-[calc(100%-100px)]">
                                        <label className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-2 block">Email Body</label>
                                        <textarea 
                                            value={editBody}
                                            onChange={(e) => setEditBody(e.target.value)}
                                            className="w-full flex-1 bg-black border border-white/10 rounded-xl p-4 text-gray-300 focus:outline-none focus:border-[#00F0FF] transition-colors resize-none leading-relaxed"
                                        />
                                    </div>
                                </div>

                                {/* Mission Replay Sidebar */}
                                <div className="w-80 border-l border-white/10 pl-8 space-y-6">
                                    <div>
                                        <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-6">
                                            <svg className="w-4 h-4 text-[#00F0FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                            Mission Replay
                                        </h3>
                                        <div className="space-y-6 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
                                            {selectedDraft.evidence_log?.map((log, idx) => (
                                                <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                                    <div className="flex items-center justify-center w-5 h-5 rounded-full border border-[#00F0FF] bg-[#111] text-[#00F0FF] shadow-[0_0_10px_rgba(0,240,255,0.2)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 relative z-10">
                                                        <div className="w-1.5 h-1.5 rounded-full bg-[#00F0FF]"></div>
                                                    </div>
                                                    <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.25rem)] p-4 rounded-xl border border-white/5 bg-black/40 shadow">
                                                        <div className="flex items-center justify-between mb-1">
                                                            <div className="font-bold text-gray-200 text-xs uppercase">{log.step}</div>
                                                        </div>
                                                        <div className="text-sm text-gray-400 leading-snug">{log.detail}</div>
                                                    </div>
                                                </div>
                                            ))}
                                            {(!selectedDraft.evidence_log || selectedDraft.evidence_log.length === 0) && (
                                                <div className="text-sm text-gray-500 italic text-center mt-10">No AI reasoning log provided.</div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </AnimatePresence>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-500 flex-col gap-4">
                        <svg className="w-16 h-16 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" /></svg>
                        <p>Select a draft from the inbox to review</p>
                    </div>
                )}
            </div>
        </div>
    );
}
