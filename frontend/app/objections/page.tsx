"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, Save, PlusCircle, Trash2, Award, 
  ArrowRight, Inbox, Plus, AlertCircle, PhoneCall 
} from "lucide-react";
import { useOnboardingStore } from "../onboarding/store";
import { BACKEND_URL } from "../config";

interface ObjectionItem {
  objection: string;
  rebuttal: string;
}

interface MissedObjection {
  id: string;
  trigger: string;
  callInfo: string;
  confidence: number;
}

const mockMissedObjections: MissedObjection[] = [
  { id: "mo_1", trigger: "We already use Salesforce CRM, why do we need this?", callInfo: "Call with Sarah Connor (2m 34s)", confidence: 64 },
  { id: "mo_2", trigger: "Does this require us to port our existing business number?", callInfo: "Call with Bruce Wayne (1m 12s)", confidence: 72 },
  { id: "mo_3", trigger: "I'm not the right person, you should talk to our VP of Ops.", callInfo: "Call with Hal Jordan (5m 01s)", confidence: 81 }
];

export default function ObjectionsPage() {
  const { state, loadProgress, saveProgress } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [objections, setObjections] = useState<ObjectionItem[]>([]);
  const [missedObjections, setMissedObjections] = useState<MissedObjection[]>(mockMissedObjections);

  useEffect(() => {
    setMounted(true);
    loadProgress();
  }, []);

  // Initialize values from store
  useEffect(() => {
    if (state.step3) {
      setObjections(state.step3.objectionsList || [
        { objection: "Pricing is too expensive.", rebuttal: "I understand. Many clients start where you are but see immediate ROI through 40% higher bookings." },
        { objection: "AI sounds too mechanical.", rebuttal: "That's a fair point, but our agents match natural human speech patterns and pauses in real-time." }
      ]);
    }
  }, [state.step3]);

  const handleAddObjection = () => {
    setObjections([...objections, { objection: "", rebuttal: "" }]);
  };

  const handleRemoveObjection = (idx: number) => {
    setObjections(objections.filter((_, i) => i !== idx));
  };

  const handleObjectionChange = (idx: number, field: "objection" | "rebuttal", val: string) => {
    const updated = objections.map((item, i) => {
      if (i === idx) {
        return {
          ...item,
          [field]: val,
        };
      }
      return item;
    });
    setObjections(updated);
  };

  const handleAddFromMissed = (missed: MissedObjection) => {
    // Add to active objections list
    setObjections([...objections, { objection: missed.trigger, rebuttal: "" }]);
    // Remove from missed list
    setMissedObjections(missedObjections.filter((mo) => mo.id !== missed.id));
  };

  const handleSaveObjections = async () => {
    if (!state.step3) return;
    setIsSaving(true);

    const updatedStep3 = {
      ...state.step3,
      objectionsList: objections.filter(o => o.objection && o.rebuttal), // Filter empty items
    };

    const mergedState = {
      ...state,
      step3: updatedStep3,
    };

    await saveProgress(mergedState);

    // Call onboarding/complete endpoint to trigger server config DB sync
    try {
      await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: "default_shared_tenant",
          company_name: state.step1?.companyName || "Unknown",
          website: state.step1?.website || "",
          industry: state.step1?.industry || "",
          team_size: state.step1?.teamSize || "",
          annual_revenue: state.step1?.annualRevenue || "",
          target_region: state.step1?.targetRegion || "",
          phone_number: state.step2?.twilioNumber || "",
          agent_name: state.step3?.agentName || "Alex",
          company_description: state.step3?.companyDescription || "",
          value_proposition: state.step3?.valueProposition || "",
          voice: state.step3?.voice || "rachel",
          tone: state.step3?.tone || "consultative",
          timezone: state.step3?.timezone || "America/New_York",
          calling_hours_start: state.step3?.callingHoursStart || "08:00",
          calling_hours_end: state.step3?.callingHoursEnd || "17:00",
          product_name: state.step3?.productName || "",
          product_price: state.step3?.productPrice || "",
          product_features: state.step3?.productFeatures || "",
          target_audience: state.step3?.targetAudience || "",
          kb_description: state.step3?.kbDescription || "",
          kb_faqs: state.step3?.kbFaqs || [],
          objections_list: updatedStep3.objectionsList,
          recording_disclosure: state.step4?.recordingDisclosure || false,
          consent_confirmed: state.step4?.consentConfirmed || false,
          country: state.step4?.country || "US",
          import_source: state.step5?.importSource || "csv",
          campaign_goal: state.step5?.campaignGoal || "",
          playbook_greeting: state.step5?.playbookGreeting || "",
          playbook_booking_link: state.step5?.playbookBookingLink || "",
        }),
      });
    } catch (err) {
      console.warn("DB update failed: ", err);
    }

    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  if (!mounted) return null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Objection Handling Center
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            Train your AI Employee to handle resistance, brush-offs, and objections.
          </p>
        </div>
        <button
          onClick={handleSaveObjections}
          disabled={isSaving}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all"
          style={{
            background: saveSuccess
              ? "hsl(var(--success))"
              : "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          {saveSuccess ? <Award className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
          {saveSuccess ? "Playbook Synced!" : "Save Objection Rules"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Objection Matrix Panel (Left 2 Columns) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse-live" />
                <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                  Objection Rebuttal Mappings
                </h2>
              </div>
              <button
                type="button"
                onClick={handleAddObjection}
                className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 border border-dashed border-emerald-500/30 px-3 py-1.5 rounded hover:bg-emerald-500/5 transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5" /> Add New Rebuttal rule
              </button>
            </div>

            <div className="space-y-4 max-h-[520px] overflow-y-auto pr-1">
              {objections.length === 0 ? (
                <div className="p-8 rounded-lg border border-dashed text-center text-xs" style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-muted))" }}>
                  No objections mapped. Click "Add New Rebuttal rule" to get started.
                </div>
              ) : (
                objections.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border flex flex-col gap-3 relative"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}
                  >
                    <button
                      type="button"
                      onClick={() => handleRemoveObjection(idx)}
                      className="absolute right-2 top-2 p-1.5 text-rose-400 hover:bg-white/5 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">Trigger phrase (What the prospect says)</span>
                      <input
                        type="text"
                        placeholder="e.g. Your price is too expensive."
                        value={item.objection}
                        onChange={(e) => handleObjectionChange(idx, "objection", e.target.value)}
                        className="w-full px-2.5 py-1.5 rounded text-xs border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))]"
                        style={{ background: "hsl(var(--surface-3))", borderColor: "hsl(var(--border-subtle))", color: "hsl(var(--text-primary))" }}
                      />
                    </div>

                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-neutral-400">AI Rebuttal Pivot Response (SDR pivot)</span>
                      <textarea
                        rows={2}
                        placeholder="e.g. I hear you. Many clients see immediate ROI through..."
                        value={item.rebuttal}
                        onChange={(e) => handleObjectionChange(idx, "rebuttal", e.target.value)}
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

        {/* Missed Objections Inbox (Right Column) */}
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <div className="flex items-center gap-2 mb-2">
              <Inbox className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                Missed Objections Inbox
              </h2>
            </div>
            <p className="text-[11px] leading-relaxed" style={{ color: "hsl(var(--text-muted))" }}>
              These phrases were flagged in recent calls where the AI agent encountered resistance that had no mapped rebuttal playbook rules.
            </p>

            <div className="space-y-3 mt-2">
              {missedObjections.length === 0 ? (
                <div className="p-6 rounded-lg border border-dashed text-center text-xs text-neutral-400" style={{ borderColor: "hsl(var(--border-default))" }}>
                  Missed objections queue is empty! Your agent is fully aligned with recent conversations.
                </div>
              ) : (
                missedObjections.map((mo) => (
                  <div
                    key={mo.id}
                    className="p-3.5 rounded-xl border flex flex-col gap-2 relative text-xs"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] flex items-center gap-1 text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded font-medium">
                        <AlertCircle className="w-3 h-3" /> Unresolved
                      </span>
                      <span className="text-[9px] text-neutral-400">Match score: {mo.confidence}%</span>
                    </div>

                    <p className="font-semibold italic" style={{ color: "hsl(var(--text-primary))" }}>
                      "{mo.trigger}"
                    </p>

                    <p className="text-[10px] flex items-center gap-1" style={{ color: "hsl(var(--text-muted))" }}>
                      <PhoneCall className="w-3 h-3" /> {mo.callInfo}
                    </p>

                    <button
                      type="button"
                      onClick={() => handleAddFromMissed(mo)}
                      className="mt-1.5 flex items-center justify-center gap-1 py-1.5 rounded text-[10px] font-bold text-white transition-all bg-emerald-500 hover:bg-emerald-600 w-full"
                    >
                      Train Rebuttal Response <ArrowRight className="w-3 h-3" />
                    </button>
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
