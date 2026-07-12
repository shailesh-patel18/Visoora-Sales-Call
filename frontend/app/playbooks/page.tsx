"use client";

import React, { useState, useEffect } from "react";
import { 
  BookOpen, HelpCircle, ArrowRight, Save, Award, ListChecks, CheckSquare, 
  MessageSquare, Sparkles, AlertTriangle, ArrowDown, ShieldAlert 
} from "lucide-react";
import { useOnboardingStore } from "../onboarding/store";
import { useCRMStore } from "../store";
import { useRouter } from "next/navigation";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

interface PlaybookStep {
  state: string;
  label: string;
  desc: string;
  color: string;
  bullet: string;
}

const playbookSteps: PlaybookStep[] = [
  { state: "INITIATION", label: "1. Introduction", desc: "Greet the prospect, state company name, and verify decision maker identity.", color: "#f59e0b", bullet: "Opening Greeting script reads aloud" },
  { state: "DISCOVERY", label: "2. Discovery", desc: "Ask open-ended questions about current systems, pain points, and challenges.", color: "#3b82f6", bullet: "Curious questioning about workflows" },
  { state: "PITCH", label: "3. Value Pitch", desc: "Pitch value hook answering pain points. Share core product catalog details.", color: "#8b5cf6", bullet: "Target value pitch, product pricing & features" },
  { state: "QUALIFICATION", label: "4. Lead Qualification", desc: "Confirm lead fit based on BANT criteria (Budget, Authority, Need, Timeline).", color: "#ec4899", bullet: "Checking BANT criteria boxes" },
  { state: "BOOKING", label: "5. Meeting Booking", desc: "Offer slot recommendations and share schedule calendar link.", color: "#10b981", bullet: "Calendar booking link recommendation" },
  { state: "SUCCESS_COMPLETE", label: "6. Success Confirm", desc: "Verify booking slot time, state immediate next steps, close call.", color: "#06b6d4", bullet: "Confirm schedule details and goodbye" }
];

export default function PlaybooksPage() {
  const { state, loadProgress, saveProgress, completeOnboarding } = useOnboardingStore();
  const { markStepComplete, setWorkflowStep } = useCRMStore();
  const router = useRouter();
  
  const [mounted, setMounted] = useState(false);
  const [activeStepState, setActiveStepState] = useState("INITIATION");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [greetingInput, setGreetingInput] = useState("");
  const [bookingLinkInput, setBookingLinkInput] = useState("");
  const [goalInput, setGoalInput] = useState("Book Demo Meeting");

  // BANT Checklist defaults
  const [bantBudget, setBantBudget] = useState(true);
  const [bantAuthority, setBantAuthority] = useState(true);
  const [bantNeed, setBantNeed] = useState(true);
  const [bantTimeline, setBantTimeline] = useState(false);

  useEffect(() => {
    setMounted(true);
    loadProgress();
  }, []);

  // Initialize values from store
  useEffect(() => {
    setGreetingInput(state.playbookGreeting || "Hi, is this the owner? I was calling because we noticed your agency is booking demos manually...");
    setBookingLinkInput(state.playbookBookingLink || "https://calendly.com/acme-demos/15min");
    setGoalInput(state.campaignGoal || "Book Demo Meeting");
  }, [state.playbookGreeting, state.playbookBookingLink, state.campaignGoal]);

  const handleSavePlaybook = async () => {
    setIsSaving(true);

    const mergedState = {
      ...state,
      playbookGreeting: greetingInput,
      playbookBookingLink: bookingLinkInput,
      campaignGoal: goalInput,
    };

    await saveProgress(mergedState);

    // Call onboarding/complete endpoint to trigger server config DB sync
    try {
      await completeOnboarding();
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
            Sales Playbook Builder
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "hsl(var(--text-muted))" }}>
            Map the conversational timeline and qualify leads using step-based SDR scripts.
          </p>
        </div>
        <button
          onClick={handleSavePlaybook}
          disabled={isSaving}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white transition-all"
          style={{
            background: saveSuccess
              ? "hsl(var(--success))"
              : "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          {saveSuccess ? <Award className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
          {saveSuccess ? "Playbook Saved!" : "Save Playbook"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Navigation (Left Column) */}
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            <h2 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
              Conversational Stages (FSM)
            </h2>
            <div className="relative pl-4 border-l space-y-4" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              {playbookSteps.map((step) => {
                const isActive = activeStepState === step.state;
                return (
                  <div
                    key={step.state}
                    onClick={() => setActiveStepState(step.state)}
                    className="relative cursor-pointer transition-all"
                  >
                    {/* Node Dot */}
                    <div
                      className="absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full border-2 transition-all flex items-center justify-center"
                      style={{
                        background: isActive ? step.color : "hsl(var(--surface-1))",
                        borderColor: step.color,
                      }}
                    >
                      {isActive && <div className="w-1 h-1 rounded-full bg-white animate-ping" />}
                    </div>
                    <div>
                      <p
                        className="text-xs font-bold transition-colors"
                        style={{ color: isActive ? "hsl(var(--text-primary))" : "hsl(var(--text-muted))" }}
                      >
                        {step.label}
                      </p>
                      <p className="text-[10px] mt-0.5 line-clamp-1" style={{ color: "hsl(var(--text-secondary))" }}>
                        {step.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Step configuration panel (Right 2 Columns) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="rounded-xl border p-6 flex flex-col gap-6" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
            
            {/* Active Step Banner */}
            <div className="flex items-center gap-3 pb-4 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                style={{ background: `${playbookSteps.find((s) => s.state === activeStepState)?.color}20`, color: playbookSteps.find((s) => s.state === activeStepState)?.color }}
              >
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                  {playbookSteps.find((s) => s.state === activeStepState)?.label} Config
                </h3>
                <p className="text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>
                  {playbookSteps.find((s) => s.state === activeStepState)?.desc}
                </p>
              </div>
            </div>

            {/* Stage wise inputs */}
            {activeStepState === "INITIATION" && (
              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                    SDR Cold Opening Hook (Greeting Script)
                  </label>
                  <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>
                    The AI rep will recite this statement word-for-word upon phone pick-up.
                  </p>
                  <textarea
                    rows={4}
                    value={greetingInput}
                    onChange={(e) => setGreetingInput(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] resize-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>
              </div>
            )}

            {activeStepState === "DISCOVERY" && (
              <div className="flex flex-col gap-4 text-xs leading-relaxed" style={{ color: "hsl(var(--text-secondary))" }}>
                <div className="rounded-lg p-4 border" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                  <span className="font-semibold text-blue-400 block mb-1">Conversational Behavior:</span>
                  The AI is instructed to ask open-ended questions about tools, systems, and challenges.
                  <ul className="list-disc pl-4 mt-2 space-y-1.5">
                    <li>How are you currently scheduling demo requests for your SDR team?</li>
                    <li>What are the primary bottleneck constraints in your outbound pipeline today?</li>
                    <li>How much time is your sales rep team spending sorting stale prospects?</li>
                  </ul>
                </div>
                <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>
                  Discovery guides the conversation dynamically before product pitch injection, boosting credibility.
                </p>
              </div>
            )}

            {activeStepState === "PITCH" && (
              <div className="flex flex-col gap-4 text-xs leading-relaxed" style={{ color: "hsl(var(--text-secondary))" }}>
                <div className="rounded-lg p-4 border" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                  <span className="font-semibold text-purple-400 block mb-1">Active Pitch Context:</span>
                  During this stage, the AI Employee dynamically retrieves target values from your **Product Catalog** configurations (configured in Onboarding or Agent settings):
                  <ul className="list-disc pl-4 mt-2 space-y-1">
                    <li>Company Name: <span className="font-semibold text-white">{state.step1?.companyName || "Visoora"}</span></li>
                    <li>Value Proposition: <span className="font-semibold text-white">"{state.step1?.valueProposition || "None"}"</span></li>
                    <li>Description: <span className="font-semibold text-white">{state.step1?.companyDescription || "None"}</span></li>
                    <li>Website: <span className="font-semibold text-white">{state.step1?.website || "None"}</span></li>
                  </ul>
                </div>
              </div>
            )}

            {activeStepState === "QUALIFICATION" && (
              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                    BANT Qualification Checklist Criteria
                  </label>
                  <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>
                    Select which elements the AI employee must qualify on the call before offering schedule booking slots.
                  </p>
                  
                  <div className="space-y-2 mt-2">
                    <div className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-white/5 cursor-pointer" onClick={() => setBantBudget(!bantBudget)}>
                      <input type="checkbox" checked={bantBudget} readOnly className="rounded border-neutral-700 bg-neutral-900" />
                      <div>
                        <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Budget [B]</p>
                        <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Determine whether they have budget allocated or fit pricing guidelines.</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-white/5 cursor-pointer" onClick={() => setBantAuthority(!bantAuthority)}>
                      <input type="checkbox" checked={bantAuthority} readOnly className="rounded border-neutral-700 bg-neutral-900" />
                      <div>
                        <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Authority [A]</p>
                        <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Verify the call contact is a decision maker (founder, VP, director).</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-white/5 cursor-pointer" onClick={() => setBantNeed(!bantNeed)}>
                      <input type="checkbox" checked={bantNeed} readOnly className="rounded border-neutral-700 bg-neutral-900" />
                      <div>
                        <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Need [N]</p>
                        <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Identify active pain points that match the value hook proposition.</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-white/5 cursor-pointer" onClick={() => setBantTimeline(!bantTimeline)}>
                      <input type="checkbox" checked={bantTimeline} readOnly className="rounded border-neutral-700 bg-neutral-900" />
                      <div>
                        <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Timeline [T]</p>
                        <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Determine time-horizon for purchasing or demo implementation decisions.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeStepState === "BOOKING" && (
              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                    Campaign Target Goal Description
                  </label>
                  <input
                    type="text"
                    value={goalInput}
                    onChange={(e) => setGoalInput(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
                    Meeting Calendar Booking Link
                  </label>
                  <input
                    type="text"
                    value={bookingLinkInput}
                    onChange={(e) => setBookingLinkInput(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg text-sm border outline-none"
                    style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
                  />
                </div>
              </div>
            )}

            {activeStepState === "SUCCESS_COMPLETE" && (
              <div className="flex flex-col gap-4 text-xs leading-relaxed" style={{ color: "hsl(var(--text-secondary))" }}>
                <div className="rounded-lg p-4 border" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-subtle))" }}>
                  <span className="font-semibold text-emerald-400 block mb-1">Confirming Scheduling:</span>
                  The AI confirms details, offers scheduling details verbally, and reviews next steps.
                  <p className="mt-2 text-[11px]" style={{ color: "hsl(var(--text-muted))" }}>
                    A booking confirmation trigger event will be dispatched instantly over active webhooks to dashboard pipeline components.
                  </p>
                </div>
              </div>
            )}

            {/* Objection handler trigger alert */}
            <div className="p-3.5 rounded-lg border flex items-start gap-2.5" style={{ background: "hsla(0, 84%, 60%, 0.03)", borderColor: "hsla(0, 84%, 60%, 0.15)" }}>
              <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs">
                <span className="font-semibold text-red-400 block mb-0.5">Re-entrant Objection State:</span>
                <span style={{ color: "hsl(var(--text-secondary))" }}>
                  An objection trigger will automatically pause the playbook flow at any stage, handle the concern using the **Objection Handling Playbook**, and then return back here seamlessly.
                </span>
              </div>
            </div>

            {/* Next stage button */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => {
                  const currIdx = playbookSteps.findIndex((s) => s.state === activeStepState);
                  const nextIdx = (currIdx + 1) % playbookSteps.length;
                  setActiveStepState(playbookSteps[nextIdx].state);
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold border"
                style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-primary))" }}
              >
                Inspect Next Stage <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>
        </div>
      </div>

      {/* Next Step Progression */}
      <div className="flex justify-end pt-8 mt-8 border-t border-[hsl(var(--border-subtle))]">
        <button 
          onClick={() => {
            markStepComplete(3);
            setWorkflowStep(4);
            router.push("/settings/email");
          }}
          className="px-8 py-3 bg-gradient-to-r from-[#00F0FF] to-[#0080FF] text-white font-bold rounded-xl shadow-[0_0_20px_rgba(0,240,255,0.3)] hover:shadow-[0_0_30px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2"
        >
          Continue to Integrations
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
