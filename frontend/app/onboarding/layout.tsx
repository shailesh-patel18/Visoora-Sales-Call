"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, HelpCircle, FileText, CheckCircle, RefreshCw, Sparkles } from "lucide-react";
import { useOnboardingStore } from "./store";

const stepsList = [
  { step: 1, label: "Context" },
  { step: 2, label: "Agent" },
  { step: 3, label: "ICP Ind." },
  { step: 4, label: "ICP Reg." },
  { step: 5, label: "Titles" },
  { step: 6, label: "Competitors" },
  { step: 7, label: "Voice" },
  { step: 8, label: "Objections" },
  { step: 9, label: "Avoid-List" },
  { step: 10, label: "Phone" },
  { step: 11, label: "Launch" },
];

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { state, loadProgress, isSaving, isLoading } = useOnboardingStore();
  const currentStep = state.currentStep;
  const pathname = usePathname();
  const isChatOnboarding = pathname === "/onboarding/chat";

  useEffect(() => {
    loadProgress();
  }, []);

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
              Consultative Setup
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
          {!isChatOnboarding && (
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
                      className="text-xs font-semibold uppercase tracking-wider hidden lg:inline"
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
                        className="w-2 h-[1px] md:w-4 hidden sm:block"
                        style={{ background: isPassed ? "hsl(var(--success))" : "hsl(var(--border-subtle))" }}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Steps wrapper */}
          <div className="flex-1 min-h-[500px]">
            {children}
          </div>
        </main>

        {/* Live Business Brain Preview Sidebar */}
        {!isChatOnboarding && (
          <aside className="w-full md:w-[320px] lg:w-[380px] flex-shrink-0">
          <div
            className="glass p-5 rounded-xl border flex flex-col gap-4 sticky top-24"
            style={{ borderColor: "hsl(var(--border-subtle))" }}
          >
            <div className="flex items-center gap-2.5 pb-3 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
              <Sparkles className="w-[18px] h-[18px]" style={{ color: "hsl(var(--brand-primary))" }} />
              <h2 className="font-bold text-[14px] tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
                Live Business Brain
              </h2>
            </div>
            
            <div className="flex flex-col gap-3 text-xs">
              {/* Company context info */}
              <div>
                <span className="font-bold text-[10px] block uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                  Company Profile
                </span>
                <div className="p-3.5 rounded-lg border flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                  <div className="font-semibold text-sm" style={{ color: "hsl(var(--text-primary))" }}>
                    {state.step1?.companyName || "Awaiting Setup..."}
                  </div>
                  {state.step1?.website && (
                    <div className="text-[11px]" style={{ color: "hsl(var(--brand-accent))" }}>
                      {state.step1?.website}
                    </div>
                  )}
                  {state.step1?.companyDescription && (
                    <div className="text-[11px] leading-relaxed line-clamp-3 mt-1" style={{ color: "hsl(var(--text-secondary))" }}>
                      {state.step1?.companyDescription}
                    </div>
                  )}
                </div>
              </div>

              {/* Agent info */}
              {state.step2?.agentName && (
                <div>
                  <span className="font-bold text-[10px] block uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                    AI SDR Persona
                  </span>
                  <div className="p-3 rounded-lg border flex items-center justify-between" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                    <div className="font-semibold" style={{ color: "hsl(var(--text-primary))" }}>
                      {state.step2.agentName}
                    </div>
                    {state.step7?.voice && (
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold" style={{ background: "hsla(210, 100%, 50%, 0.1)", color: "hsl(var(--brand-primary))" }}>
                        {state.step7.voice} ({state.step7.tone})
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* ICP Criteria */}
              {(state.step3?.icpIndustries || state.step4?.icpRegions || state.step5?.decisionMakerTitles) && (
                <div>
                  <span className="font-bold text-[10px] block uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                    ICP Definition
                  </span>
                  <div className="p-3 rounded-lg border flex flex-col gap-2" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                    {state.step3?.icpIndustries && state.step3.icpIndustries.length > 0 && (
                      <div>
                        <div className="font-medium text-[10px] mb-1" style={{ color: "hsl(var(--text-secondary))" }}>Industries:</div>
                        <div className="flex flex-wrap gap-1">
                          {state.step3.icpIndustries.map(ind => (
                            <span key={ind} className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: "hsl(var(--surface-2))", color: "hsl(var(--text-primary))" }}>
                              {ind}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {state.step4?.icpRegions && state.step4.icpRegions.length > 0 && (
                      <div>
                        <div className="font-medium text-[10px] mb-1" style={{ color: "hsl(var(--text-secondary))" }}>Regions:</div>
                        <div className="flex flex-wrap gap-1">
                          {state.step4.icpRegions.map(reg => (
                            <span key={reg} className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: "hsl(var(--surface-2))", color: "hsl(var(--text-primary))" }}>
                              {reg}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {state.step5?.decisionMakerTitles && state.step5.decisionMakerTitles.length > 0 && (
                      <div>
                        <div className="font-medium text-[10px] mb-1" style={{ color: "hsl(var(--text-secondary))" }}>Titles:</div>
                        <div className="flex flex-wrap gap-1">
                          {state.step5.decisionMakerTitles.map(ttl => (
                            <span key={ttl} className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: "hsl(var(--surface-2))", color: "hsl(var(--text-primary))" }}>
                              {ttl}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Competitors & Avoid List */}
              {((state.step6?.competitors && state.step6.competitors.length > 0) || (state.step9?.avoidList && state.step9.avoidList.length > 0)) && (
                <div>
                  <span className="font-bold text-[10px] block uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                    Guardrails
                  </span>
                  <div className="p-3 rounded-lg border flex flex-col gap-2" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                    {state.step6?.competitors && state.step6.competitors.length > 0 && (
                      <div>
                        <div className="font-medium text-[10px] mb-1" style={{ color: "hsl(var(--text-secondary))" }}>Competitors:</div>
                        <div className="text-[11px]" style={{ color: "hsl(var(--text-primary))" }}>
                          {state.step6.competitors.join(", ")}
                        </div>
                      </div>
                    )}
                    {state.step9?.avoidList && state.step9.avoidList.length > 0 && (
                      <div>
                        <div className="font-medium text-[10px] mb-1" style={{ color: "hsl(var(--text-secondary))" }}>Avoid List:</div>
                        <div className="text-[11px] text-red-400 font-mono">
                          {state.step9.avoidList.join(", ")}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Objections */}
              {state.step8?.objectionsList && state.step8.objectionsList.length > 0 && (
                <div>
                  <span className="font-bold text-[10px] block uppercase tracking-wider mb-1" style={{ color: "hsl(var(--text-muted))" }}>
                    Objections ({state.step8.objectionsList.length})
                  </span>
                  <div className="p-3 rounded-lg border flex flex-col gap-1.5" style={{ background: "hsl(var(--surface-1))", borderColor: "hsl(var(--border-subtle))" }}>
                    <div className="font-medium text-[11px]" style={{ color: "hsl(var(--text-primary))" }}>
                      "{state.step8.objectionsList[0].objection}"
                    </div>
                    <div className="text-[10px] italic leading-relaxed" style={{ color: "hsl(var(--text-secondary))" }}>
                      Rebuttal: "{state.step8.objectionsList[0].rebuttal}"
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </aside>
        )}

      </div>
    </div>
  );
}
