"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Zap, HelpCircle, FileText, CheckCircle, RefreshCw } from "lucide-react";
import { useOnboardingStore } from "./store";

const stepsList = [
  { step: 1, label: "Company" },
  { step: 2, label: "Phone" },
  { step: 3, label: "Agent" },
  { step: 4, label: "Compliance" },
  { step: 5, label: "Import" },
  { step: 6, label: "Launch" },
];

const helpContent: Record<number, { title: string; desc: string; docLink: string }> = {
  1: {
    title: "Company Setup Help",
    desc: "We validate your business website to automatically retrieve profile information and size metrics. This accelerates setup and ensures your outbound profile matches your true identity.",
    docLink: "https://docs.visoora.com/company-setup",
  },
  2: {
    title: "Phone Provisioning Help",
    desc: "Choose to provision a clean, vetted Twilio phone number in your target area code or initiate a secure porting request. Vetted caller lines boost contact rates up to 40%.",
    docLink: "https://docs.visoora.com/phone-numbers",
  },
  3: {
    title: "AI Agent Config Help",
    desc: "Design your AI agent's name, core system instructions, and choose from 5 premium conversational voice profiles. Adjust business calling hours to conform with telecom laws.",
    docLink: "https://docs.visoora.com/agent-personas",
  },
  4: {
    title: "Regulatory Compliance Help",
    desc: "Visoora enforces strict regulatory compliance constraints before outbound calls are dialed. Toggling the call recording disclosure will notify prospects automatically.",
    docLink: "https://docs.visoora.com/compliance-tcpa",
  },
  5: {
    title: "Lead Importer Help",
    desc: "Upload a standard contacts CSV and map column fields to establish prospect structures. We process contact records through real-time formatting queues.",
    docLink: "https://docs.visoora.com/csv-import",
  },
  6: {
    title: "Sandbox Sandbox Test Help",
    desc: "Trigger a real call to your personal mobile line to audit Visoora's low-latency dialogue capabilities. Watch a live WebSocket transcription feed in the sandbox console.",
    docLink: "https://docs.visoora.com/test-calling",
  },
};

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { state, loadProgress, isSaving, isLoading } = useOnboardingStore();
  const currentStep = state.currentStep;

  useEffect(() => {
    loadProgress();
  }, []);

  const activeHelp = helpContent[currentStep] || helpContent[1];

  return (
    <div
      className="flex flex-col min-h-screen relative overflow-x-hidden"
      style={{ background: "hsl(var(--surface-0))" }}
    >
      {/* Dynamic Background Gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full opacity-[0.03] pointer-events-none filter blur-[120px] bg-[hsl(var(--brand-primary))]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[50%] rounded-full opacity-[0.03] pointer-events-none filter blur-[120px] bg-[hsl(var(--brand-accent))]" />

      {/* Header bar */}
      <header
        className="glass sticky top-0 z-40 flex items-center justify-between px-6 py-4 border-b"
        style={{ borderColor: "hsl(var(--border-subtle))" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
            }}
          >
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <span
              className="font-bold text-[15px] tracking-tight"
              style={{ color: "hsl(var(--text-primary))" }}
            >
              Visoora Onboarding
            </span>
            <span
              className="text-[10px] ml-2 px-1.5 py-0.5 rounded-full font-medium"
              style={{ background: "hsl(var(--surface-2))", color: "hsl(var(--text-secondary))" }}
            >
              Setup Wizard
            </span>
          </div>
        </div>

        {/* Loading / Saving indicators */}
        <div className="flex items-center gap-2">
          {isSaving && (
            <span
              className="flex items-center gap-1 text-[11px] font-medium"
              style={{ color: "hsl(var(--brand-primary))" }}
            >
              <RefreshCw className="w-3 h-3 animate-spin" /> Saving progress...
            </span>
          )}
          {isLoading && (
            <span
              className="flex items-center gap-1 text-[11px] font-medium text-amber-400"
            >
              <RefreshCw className="w-3 h-3 animate-spin" /> Restoring sandbox...
            </span>
          )}
        </div>
      </header>

      {/* Main stepper and view wrapper */}
      <div className="flex-1 flex flex-col md:flex-row w-full max-w-[1440px] mx-auto p-4 md:p-6 lg:p-8 gap-6 md:gap-8">
        
        {/* Central Form Container */}
        <main className="flex-1 flex flex-col min-w-0 bg-transparent">
          
          {/* Stepper Display */}
          <div
            className="glass flex flex-row items-center justify-between p-4 rounded-xl border mb-6 overflow-x-auto gap-4"
            style={{ borderColor: "hsl(var(--border-subtle))" }}
          >
            {stepsList.map((item, idx) => {
              const isActive = item.step === currentStep;
              const isPassed = item.step < currentStep;

              return (
                <div key={item.step} className="flex items-center gap-2 flex-shrink-0">
                  <div
                    className="flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold transition-all"
                    style={{
                      background: isActive
                        ? "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                        : isPassed
                        ? "hsla(142, 71%, 45%, 0.15)"
                        : "hsl(var(--surface-3))",
                      color: isActive
                        ? "white"
                        : isPassed
                        ? "#22c55e"
                        : "hsl(var(--text-secondary))",
                      boxShadow: isActive
                        ? "0 0 10px -2px hsla(var(--brand-primary), 0.4)"
                        : "none",
                    }}
                  >
                    {isPassed ? <CheckCircle className="w-4 h-4" /> : item.step}
                  </div>
                  <span
                    className="text-xs font-semibold uppercase tracking-wider"
                    style={{
                      color: isActive
                        ? "hsl(var(--text-primary))"
                        : isPassed
                        ? "hsl(var(--success))"
                        : "hsl(var(--text-muted))",
                    }}
                  >
                    {item.label}
                  </span>
                  {idx < stepsList.length - 1 && (
                    <div
                      className="w-4 h-[1px] md:w-8 hidden sm:block"
                      style={{ background: isPassed ? "hsl(var(--success))" : "hsl(var(--border-subtle))" }}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Steps wrapper */}
          <div className="flex-1 min-h-[500px]">
            {children}
          </div>
        </main>

        {/* Floating Sidebar Container */}
        <aside className="w-full md:w-[280px] lg:w-[320px] flex-shrink-0">
          <div
            className="glass p-5 rounded-xl border flex flex-col gap-4 sticky top-24"
            style={{
              borderColor: "hsl(var(--border-subtle))",
            }}
          >
            <div className="flex items-center gap-2.5 pb-3 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              <HelpCircle className="w-[18px] h-[18px]" style={{ color: "hsl(var(--brand-primary))" }} />
              <h2 className="font-bold text-[14px] tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
                {activeHelp.title}
              </h2>
            </div>
            
            <p className="text-xs leading-relaxed" style={{ color: "hsl(var(--text-secondary))" }}>
              {activeHelp.desc}
            </p>

            <Link
              href={activeHelp.docLink}
              target="_blank"
              className="flex items-center gap-1.5 mt-2 text-[11px] font-semibold transition-colors"
              style={{ color: "hsl(var(--brand-accent))" }}
            >
              <FileText className="w-3.5 h-3.5" /> View documentation
            </Link>
          </div>
        </aside>

      </div>
    </div>
  );
}
