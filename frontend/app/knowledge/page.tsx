"use client";

import React, { useState, useEffect } from "react";
import { 
  FolderOpen, HelpCircle, Save, Plus, Trash2, Award, 
  FileText, PlusCircle, CheckCircle2, BookOpen 
} from "lucide-react";
import { useOnboardingStore } from "../onboarding/store";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

interface FAQItem {
  question: string;
  answer: string;
}

export default function KnowledgePage() {
  const { state, loadProgress, saveProgress, updateStep1, updateStep7, updateStep8, completeOnboarding } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [wikiInput, setWikiInput] = useState("");
  const [faqs, setFaqs] = useState<FAQItem[]>([]);
  const [companyDescriptionInput, setCompanyDescriptionInput] = useState("");
  const [valuePropositionInput, setValuePropositionInput] = useState("");

  const [agents, setAgents] = useState<{ id: string; name: string }[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [crawling, setCrawling] = useState(false);
  const [crawlSuccess, setCrawlSuccess] = useState(false);

  const fetchAgents = async () => {
    setIsLoadingAgents(true);
    setFetchError(false);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/agents`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
        if (data && data.length > 0) {
          setSelectedAgentId(data[0].id);
        }
      } else {
        setFetchError(true);
      }
    } catch (err) {
      console.warn("Failed to load agents in knowledge page:", err);
      setFetchError(true);
    } finally {
      setIsLoadingAgents(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    loadProgress();
    fetchAgents();
  }, []);

  // Initialize values from store
  useEffect(() => {
    setWikiInput(state.kbDescription || "Visoora CRM covers built-in Twilio lines, automatic calendar slots scheduling, local compliance triggers, and multi-channel SMS followups.");
    setCompanyDescriptionInput(state.step1?.companyDescription || "");
    setValuePropositionInput(state.step1?.valueProposition || "");
    setFaqs(state.kbFaqs || [
      { question: "What is your pricing model?", answer: "Pricing starts at $199/month for our growth plan, covering unlimited calling and direct CRM integrations." },
      { question: "How long does setup take?", answer: "Setup takes less than 10 minutes. You can claim a Twilio number and start dialing instantly." }
    ]);
  }, [state.step1, state.kbDescription, state.kbFaqs]);


  const handleAddFaq = () => {
    setFaqs([...faqs, { question: "", answer: "" }]);
  };

  const handleRemoveFaq = (idx: number) => {
    setFaqs(faqs.filter((_, i) => i !== idx));
  };

  const handleFaqChange = (idx: number, field: "question" | "answer", val: string) => {
    const updated = faqs.map((faq, i) => {
      if (i === idx) {
        return {
          ...faq,
          [field]: val,
        };
      }
      return faq;
    });
    setFaqs(updated);
  };

  const handleSaveKnowledge = async () => {
    setIsSaving(true);

    const mergedState = {
      ...state,
      step1: state.step1 ? {
        ...state.step1,
        companyDescription: companyDescriptionInput,
        valueProposition: valuePropositionInput,
      } : null,
      kbDescription: wikiInput,
      kbFaqs: faqs.filter(f => f.question && f.answer),
    };

    await saveProgress(mergedState);

    // Save plain text grounding wiki to backend for selected agent
    if (selectedAgentId && wikiInput.trim()) {
      try {
        await fetch(`${BACKEND_URL}/api/v1/sales-employee/agents/${selectedAgentId}/knowledge/text`, {
          method: "POST",
          headers: {
            ...getAuthHeaders(),
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            source_file: "wiki_grounding.txt",
            text: wikiInput.trim()
          })
        });
      } catch (err) {
        console.error("Failed to save grounding wiki to backend:", err);
      }
    }

    try {
      await completeOnboarding();
    } catch (err) {
      console.warn("DB update failed: ", err);
    }

    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleCrawlWebsite = async () => {
    if (!selectedAgentId || !websiteUrl.trim()) {
      alert("Please select an agent and enter a website URL.");
      return;
    }
    setCrawling(true);
    setCrawlSuccess(false);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/sales-employee/agents/${selectedAgentId}/knowledge/website`, {
        method: "POST",
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: websiteUrl.trim() })
      });
      if (res.ok) {
        setCrawlSuccess(true);
        setWebsiteUrl("");
        setTimeout(() => setCrawlSuccess(false), 2000);
      } else {
        const errData = await res.json();
        alert(`Crawling failed: ${errData.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Error crawling website.");
    }
    setCrawling(false);
  };


  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Grounding Knowledge Base
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            Identify and edit business parameters that define what the AI knows during customer calls.
          </p>
        </div>
        <button
          onClick={handleSaveKnowledge}
          disabled={isSaving}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all"
          style={{
            background: saveSuccess
              ? "hsl(var(--success))"
              : "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          {saveSuccess ? <Award className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
          {saveSuccess ? "Knowledge Saved!" : "Save Grounding Docs"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bulk Wiki Context (Left Column) */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          {/* Agent Selection Card */}
          <div className="rounded-xl border p-5 flex flex-col gap-3" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">Select AI Agent to Ground</span>
            {isLoadingAgents ? (
              <div className="flex justify-center items-center py-4">
                <span className="text-xs text-gray-500 animate-pulse">Loading Agents...</span>
              </div>
            ) : fetchError ? (
              <div className="flex flex-col gap-2 p-2">
                <span className="text-xs text-red-500">Failed to load agents.</span>
                <button onClick={fetchAgents} className="text-xs bg-white/10 px-2 py-1 rounded">Retry</button>
              </div>
            ) : (
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 px-3 text-xs text-white focus:outline-none focus:border-[hsl(var(--brand-primary))]"
              >
                {agents.length === 0 ? (
                  <option value="">No Agents Created Yet</option>
                ) : (
                  agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))
                )}
              </select>
            )}
          </div>

          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                Company Grounding Profile
              </h2>
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-semibold text-neutral-400">Company Brief Description</span>
                <textarea
                  rows={4}
                  value={companyDescriptionInput}
                  onChange={(e) => setCompanyDescriptionInput(e.target.value)}
                  className="w-full px-3 py-2 rounded text-xs border outline-none resize-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-semibold text-neutral-400">Value Proposition Hook</span>
                <textarea
                  rows={3}
                  value={valuePropositionInput}
                  onChange={(e) => setValuePropositionInput(e.target.value)}
                  className="w-full px-3 py-2 rounded text-xs border outline-none resize-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-semibold text-neutral-400">Grounding Wiki Context</span>
                <textarea
                  rows={6}
                  value={wikiInput}
                  onChange={(e) => setWikiInput(e.target.value)}
                  placeholder="Paste any company documentations, catalog pricing guidelines or details..."
                  className="w-full px-3 py-2 rounded text-xs border outline-none resize-none"
                  style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                />
              </div>
            </div>
          </div>

          {/* Crawl website section */}
          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
              Crawl Website URL
            </h2>
            <p className="text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>
              Enter a website URL to crawl and ingest its copy directly into this agent's vector brain.
            </p>
            <div className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="https://example.com"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                className="w-full px-3 py-2 rounded text-xs border outline-none"
                style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
              />
              <button
                type="button"
                onClick={handleCrawlWebsite}
                disabled={crawling}
                className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all bg-[hsl(var(--brand-primary))]"
              >
                {crawling ? "Crawling & Ingesting..." : crawlSuccess ? "Crawl Success!" : "Crawl website"}
              </button>
            </div>
          </div>
        </div>


        {/* FAQs list manager (Right 2 Columns) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              <div className="flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                  AI Grounding FAQs List
                </h2>
              </div>
              <button
                type="button"
                onClick={handleAddFaq}
                className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 border border-dashed border-emerald-500/30 px-3 py-1.5 rounded hover:bg-emerald-500/5 transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5" /> Add New FAQ Rule
              </button>
            </div>

            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
              {faqs.length === 0 ? (
                <div className="p-8 rounded-lg border border-dashed text-center text-xs" style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-muted))" }}>
                  No FAQs mapped. Click "Add New FAQ Rule" to get started.
                </div>
              ) : (
                faqs.map((faq, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border flex flex-col gap-3 relative"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}
                  >
                    <button
                      type="button"
                      onClick={() => handleRemoveFaq(idx)}
                      className="absolute right-2 top-2 p-1.5 text-rose-400 hover:bg-white/5 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">Question #{idx + 1}</span>
                      <input
                        type="text"
                        placeholder="What is the pricing model?"
                        value={faq.question}
                        onChange={(e) => handleFaqChange(idx, "question", e.target.value)}
                        className="w-full px-2.5 py-1.5 rounded text-xs border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))]"
                        style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
                      />
                    </div>

                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">Answer</span>
                      <textarea
                        rows={2}
                        placeholder="Pricing starts at $199/month..."
                        value={faq.answer}
                        onChange={(e) => handleFaqChange(idx, "answer", e.target.value)}
                        className="w-full px-2.5 py-1.5 rounded text-xs border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] resize-none"
                        style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
