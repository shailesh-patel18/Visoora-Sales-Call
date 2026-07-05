"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Brain, CheckCircle2, ChevronRight, Target, Users, Zap, ShieldAlert, ArrowRight, Loader2 } from "lucide-react";
import { useAuthStore, getAuthHeaders } from "../auth/store";
import { BACKEND_URL } from "../config";

function ActivationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reportId = searchParams.get("report_id");
  
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [isLoading, setIsLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [brain, setBrain] = useState<any>(null);
  
  const [activationScore, setActivationScore] = useState(68);

  useEffect(() => {
    // If not authenticated, redirect to login
    if (!isAuthenticated && useAuthStore.getState().user === null) {
        // Wait a tick to ensure store is hydrated
        setTimeout(() => {
            if (!useAuthStore.getState().isAuthenticated) {
                router.push(reportId ? `/login?report_id=${reportId}` : "/login");
            }
        }, 100);
        return;
    }

    const initActivation = async () => {
      try {
        const headers = getAuthHeaders();
        
        // Step 1: Claim Brain if report_id is in URL
        if (reportId) {
          setClaiming(true);
          await fetch(`${BACKEND_URL}/api/activation/claim-brain`, {
            method: "POST",
            headers,
            body: JSON.stringify({ report_id: reportId })
          });
          setClaiming(false);
          // Remove report_id from URL so we don't re-claim on refresh
          router.replace("/activation", undefined);
        }

        // Step 2: Fetch the Business Brain for this tenant
        const res = await fetch(`${BACKEND_URL}/api/activation/brain`, {
          headers
        });
        
        if (res.ok) {
          const data = await res.json();
          setBrain(data);
          
          // Calculate a mock activation score based on data completeness
          let score = 50;
          if (data.icp && data.icp.length > 0) score += 15;
          if (data.products && data.products.length > 0) score += 15;
          if (data.competitors && data.competitors.length > 0) score += 10;
          setActivationScore(score);
        } else {
          // No brain found - perhaps they didn't go through the landing page?
          // We can generate an empty one or redirect them to dashboard
          router.push("/dashboard");
        }
      } catch (err) {
        console.error("Activation error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    initActivation();
  }, [isAuthenticated, reportId, router]);

  if (isLoading || claiming) {
    return (
      <div className="min-h-screen bg-[hsl(var(--surface-0))] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-[hsl(var(--brand-primary))] flex items-center justify-center animate-pulse">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <p className="text-white font-medium">{claiming ? "Transferring AI Intelligence..." : "Waking up your AI team..."}</p>
        </div>
      </div>
    );
  }

  if (!brain) return null;

  // Helper to extract fields from JSONB metadata
  const getFullReport = () => brain?.metadata?.full_report || {};
  const reportData = getFullReport();

  return (
    <div className="min-h-screen bg-[hsl(var(--surface-0))] flex text-white font-sans">
      
      {/* Left Panel: The AI Conversation */}
      <div className="w-full lg:w-3/5 flex flex-col p-8 lg:p-16 h-screen overflow-y-auto">
        <div className="max-w-2xl mx-auto w-full">
          
          <div className="mb-12">
            <div className="w-12 h-12 rounded-xl bg-[hsl(var(--brand-primary))] flex items-center justify-center mb-6">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold tracking-tight mb-4">We've already analyzed your company.</h1>
            <p className="text-xl text-[hsl(var(--text-secondary))] leading-relaxed">
              Here's what we've learned. Let's verify a few things before your AI Growth Team begins working.
            </p>
          </div>

          <div className="space-y-8">
            {/* Industry verification */}
            <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                    <Target className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-lg">Industry Focus</h3>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-bold">
                  96% Confidence
                </div>
              </div>
              
              <div className="bg-black/20 p-4 rounded-xl border border-zinc-800/50 mb-6">
                <p className="text-lg">
                  I believe your company builds <span className="font-semibold text-white">{brain.industry || reportData.executive_summary?.industry || "Software"}</span> solutions.
                </p>
              </div>

              <div className="flex gap-3">
                <button className="flex-1 py-3 bg-[hsl(var(--brand-primary))] hover:opacity-90 rounded-xl font-bold transition-opacity">
                  Yes, that's correct
                </button>
                <button className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors">
                  Edit Industry
                </button>
              </div>
            </div>

            {/* ICP verification */}
            <div className="p-6 rounded-2xl bg-zinc-900/50 border border-zinc-800">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                    <Users className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-lg">Target Customers (ICP)</h3>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-sm font-bold">
                  82% Confidence
                </div>
              </div>
              
              <p className="text-[hsl(var(--text-secondary))] mb-4">These appear to be your ideal customers. Agree?</p>
              
              <div className="space-y-2 mb-6">
                {(brain.icp || reportData.business_intelligence?.icp || ["B2B SaaS", "Tech Founders"]).map((icp: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-black/20 border border-zinc-800/50">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    <span className="font-medium">{typeof icp === 'string' ? icp : icp.segment || icp.name}</span>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button className="flex-1 py-3 bg-[hsl(var(--brand-primary))] hover:opacity-90 rounded-xl font-bold transition-opacity">
                  Looks good
                </button>
                <button className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors">
                  Add/Remove Segments
                </button>
              </div>
            </div>
            
            {/* Low Confidence Catch */}
            <div className="p-6 rounded-2xl bg-rose-500/5 border border-rose-500/20">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-lg text-rose-100">Pricing Strategy</h3>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 text-sm font-bold">
                  45% Confidence
                </div>
              </div>
              <p className="text-rose-200/70 mb-4">I couldn't confidently determine your pricing model from the public website. How do you charge?</p>
              
              <input 
                type="text" 
                placeholder="e.g. $5k MRR, or $200/mo per seat..."
                className="w-full bg-black/40 border border-rose-500/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-rose-500/50"
              />
            </div>
            
            <button 
              onClick={() => router.push("/dashboard")}
              className="w-full py-4 bg-white text-black hover:bg-zinc-200 rounded-xl font-bold transition-colors flex items-center justify-center gap-2 mt-8 text-lg"
            >
              Initialize Workspace <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel: Activation Status (Hidden on Mobile) */}
      <div className="hidden lg:flex w-2/5 border-l border-zinc-800/50 bg-black/20 p-12 flex-col relative">
        <div className="sticky top-12">
          <h2 className="text-2xl font-bold tracking-tight mb-2">Business Activation</h2>
          <p className="text-[hsl(var(--text-secondary))] mb-8">Completing this context allows your AI team to work autonomously.</p>
          
          <div className="mb-10">
            <div className="flex justify-between items-end mb-2">
              <span className="text-4xl font-bold text-white">{activationScore}%</span>
              <span className="text-sm font-medium text-emerald-400">Ready for Launch</span>
            </div>
            <div className="h-3 w-full bg-zinc-900 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-[hsl(var(--brand-primary))] rounded-full transition-all duration-1000 ease-out" 
                style={{ width: `${activationScore}%` }}
              />
            </div>
          </div>
          
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Activation Checklist</h4>
            
            {[
              { label: "Website Analyzed", done: true },
              { label: "Business Brain Created", done: true },
              { label: "Industry Verified", done: true },
              { label: "ICP Confirmed", done: false },
              { label: "Pricing Clarified", done: false },
              { label: "CRM Initialized", done: false },
              { label: "Email Connected", done: false },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center ${item.done ? 'bg-emerald-500/20 text-emerald-500' : 'bg-zinc-800 text-zinc-500'}`}>
                  {item.done && <CheckCircle2 className="w-3.5 h-3.5" />}
                </div>
                <span className={item.done ? 'text-white font-medium' : 'text-[hsl(var(--text-secondary))]'}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}

export default function ActivationPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[hsl(var(--surface-0))] flex items-center justify-center text-white">Loading...</div>}>
      <ActivationContent />
    </Suspense>
  );
}
