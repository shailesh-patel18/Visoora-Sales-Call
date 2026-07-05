"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Globe, ArrowRight, ShieldCheck, Mail, Calendar, CheckCircle2 } from "lucide-react";
import { SkeletonAnalyzer } from "../components/SkeletonAnalyzer";
import { analyzeDomain, type AnalyzeDomainResponse, completeOnboarding } from "./api";
import { useAuthStore } from "../auth/store"; // Import for tenant_id if needed, or we'll generate one

type OnboardingStep = "input_url" | "analyzing" | "confirming_brain" | "saving_and_spinning_up" | "done";

export default function V3OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<OnboardingStep>("input_url");
  const [url, setUrl] = useState("");
  const [brainData, setBrainData] = useState<AnalyzeDomainResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isFinished, setIsFinished] = useState(false);
  const { user } = useAuthStore();

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    
    setStep("analyzing");
    setIsFinished(false);
    setAnalysisError(null);
    setBrainData(null);

    try {
      const data = await analyzeDomain(url);
      setBrainData(data);
      setIsFinished(true); // Triggers SkeletonAnalyzer to finish
    } catch (err: any) {
      console.error(err);
      setAnalysisError(err.message || "Failed to analyze website");
    }
  };

  const handleConfirmBrain = async () => {
    if (!brainData) return;
    setStep("saving_and_spinning_up");

    try {
      // 1. Generate or fetch tenant ID
      const tenantId = user?.id || `t_${Math.random().toString(36).substring(7)}`;

      // 2. Call complete API
      await completeOnboarding({
        tenant_id: tenantId,
        company_name: brainData.company_name,
        website: url,
        company_description: brainData.company_description,
        value_proposition: brainData.value_proposition,
        competitors: brainData.potential_competitors,
        icp_segments: brainData.suggested_segments,
        decision_maker_titles: brainData.estimated_decision_makers.map(dm => dm.title),
        brand_voice_tone: brainData.brand_voice_tone,
        // Mark voice as explicitly not configured
        phone_number: null,
        agent_name: "Visoora AI",
        recording_disclosure: false
      });

      // 3. Wait 2 seconds for visual effect
      await new Promise(resolve => setTimeout(resolve, 2500));

      // 4. Redirect to dashboard
      router.push("/dashboard");

    } catch (err) {
      console.error(err);
      setStep("confirming_brain");
      alert("Failed to save Business Brain. Please try again.");
    }
  };

  const renderStep = () => {
    switch (step) {
      case "input_url":
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full max-w-md mx-auto text-center space-y-8"
          >
            <div className="space-y-3">
              <h1 className="text-3xl font-bold tracking-tight text-white">Train your AI Sales Team</h1>
              <p className="text-[hsl(var(--text-secondary))]">Enter your company website. Our Research Agent will read it, identify your Ideal Customer Profile, and build your Business Brain in seconds.</p>
            </div>
            
            <form onSubmit={handleStartAnalysis} className="relative group">
              <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <Globe className="w-5 h-5 text-gray-500 group-focus-within:text-[#00F0FF] transition-colors" />
              </div>
              <input
                type="url"
                required
                placeholder="https://yourcompany.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full pl-11 pr-14 py-4 bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#00F0FF] focus:ring-1 focus:ring-[#00F0FF] transition-all shadow-inner"
              />
              <button
                type="submit"
                disabled={!url.trim()}
                className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-[hsl(var(--brand-primary))] hover:bg-[#00d0e6] text-black rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ArrowRight className="w-5 h-5" />
              </button>
            </form>
          </motion.div>
        );

      case "analyzing":
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            className="w-full"
          >
            <SkeletonAnalyzer 
              onComplete={() => setStep("confirming_brain")} 
              isFinished={isFinished}
              error={analysisError}
            />
            {analysisError && (
              <div className="mt-6 text-center">
                <button 
                  onClick={() => setStep("input_url")}
                  className="text-sm text-gray-400 hover:text-white"
                >
                  Go Back
                </button>
              </div>
            )}
          </motion.div>
        );

      case "confirming_brain":
        if (!brainData) return null; // Should not happen
        
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl mx-auto space-y-8"
          >
            <div className="text-center space-y-3">
              <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
                <ShieldCheck className="w-6 h-6 text-[#10B981]" />
                Analysis Complete
              </h2>
              <p className="text-[hsl(var(--text-secondary))]">Is this accurate? Your AI team will use this to find leads and draft emails.</p>
            </div>

            <div className="p-6 bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl shadow-xl space-y-6">
              
              <div className="border-b border-[hsl(var(--border-subtle))] pb-4 mb-4">
                 <h3 className="text-lg font-bold text-white mb-2">{brainData.company_name}</h3>
                 <p className="text-sm text-gray-400">{brainData.company_description}</p>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="col-span-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2 block">Value Proposition</label>
                  <textarea 
                    className="w-full bg-[#1A1A1A] text-gray-200 text-sm border border-[#00F0FF]/30 rounded-lg p-3 focus:outline-none focus:border-[#00F0FF] transition-colors"
                    value={brainData.value_proposition}
                    onChange={(e) => setBrainData({...brainData, value_proposition: e.target.value})}
                    rows={2}
                  />
                </div>

                <div className="col-span-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2 block">Ideal Customer Profiles (ICP)</label>
                  <div className="space-y-3">
                    {brainData.suggested_segments.map((seg, idx) => (
                      <div key={idx} className="p-3 bg-white/5 border border-white/10 rounded-lg flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                          <input 
                            className="font-semibold text-white text-sm bg-transparent border-b border-transparent hover:border-gray-500 focus:border-[#00F0FF] focus:outline-none w-2/3"
                            value={seg.segment}
                            onChange={(e) => {
                              const newSegs = [...brainData.suggested_segments];
                              newSegs[idx].segment = e.target.value;
                              setBrainData({...brainData, suggested_segments: newSegs});
                            }}
                          />
                          <span className="text-xs font-bold text-[#10B981]">{seg.confidence}% match</span>
                        </div>
                        <input 
                          className="text-xs text-gray-400 bg-transparent border-b border-transparent hover:border-gray-600 focus:border-[#00F0FF] focus:outline-none w-full"
                          value={seg.rationale}
                          onChange={(e) => {
                              const newSegs = [...brainData.suggested_segments];
                              newSegs[idx].rationale = e.target.value;
                              setBrainData({...brainData, suggested_segments: newSegs});
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="col-span-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2 block">Target Decision Makers</label>
                  <textarea 
                    className="w-full bg-[#1A1A1A] text-sm text-gray-300 border border-[hsl(var(--border-subtle))] rounded-lg p-3 focus:outline-none focus:border-[#00F0FF] transition-colors"
                    value={brainData.estimated_decision_makers.map(dm => dm.title).join(", ")}
                    onChange={(e) => {
                      const titles = e.target.value.split(",").map(t => t.trim()).filter(Boolean);
                      setBrainData({
                        ...brainData, 
                        estimated_decision_makers: titles.map(t => ({ title: t, confidence: 90 }))
                      });
                    }}
                    placeholder="e.g. CEO, VP of Sales (comma separated)"
                    rows={2}
                  />
                  <p className="text-xs text-gray-500 mt-1">Comma separated</p>
                </div>
                
                <div className="col-span-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2 block">Likely Competitors</label>
                  <textarea 
                    className="w-full bg-[#1A1A1A] text-sm text-red-400 font-bold border border-red-500/30 rounded-lg p-3 focus:outline-none focus:border-red-500 transition-colors"
                    value={brainData.potential_competitors.join(", ")}
                    onChange={(e) => {
                      const comps = e.target.value.split(",").map(c => c.trim()).filter(Boolean);
                      setBrainData({...brainData, potential_competitors: comps});
                    }}
                    placeholder="e.g. Salesforce, HubSpot (comma separated)"
                    rows={2}
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <button 
                onClick={() => setStep("input_url")}
                className="flex-1 py-3 px-4 border border-[hsl(var(--border-subtle))] hover:bg-white/5 rounded-xl text-white font-medium transition-colors"
              >
                Start Over
              </button>
              <button 
                onClick={handleConfirmBrain}
                className="flex-1 py-3 px-4 bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] text-black font-semibold rounded-xl hover:opacity-90 transition-opacity shadow-[0_0_20px_rgba(0,240,255,0.3)]"
              >
                Yes, this is accurate
              </button>
            </div>
          </motion.div>
        );

      case "saving_and_spinning_up":
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md mx-auto text-center space-y-8 py-12"
          >
             <div className="flex justify-center mb-6">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                  className="w-20 h-20 bg-[#111] rounded-full flex items-center justify-center border-t-2 border-r-2 border-[#10B981] shadow-[0_0_30px_rgba(16,185,129,0.2)]"
                >
                    <CheckCircle2 className="w-10 h-10 text-[#10B981]" />
                </motion.div>
             </div>
             
             <div className="space-y-4">
              <motion.h2 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-2xl font-bold text-white"
              >
                ✓ Business Brain Saved
              </motion.h2>
              
              <div className="space-y-2 pt-4">
                <motion.p 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 }}
                  className="text-[#00F0FF] font-medium"
                >
                  Research Agent has started...
                </motion.p>
                
                <motion.p 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.5 }}
                  className="text-gray-400 text-sm"
                >
                  Preparing Mission Alpha.
                </motion.p>

                <motion.p 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 2.2 }}
                  className="text-gray-500 text-xs italic pt-4"
                >
                  You'll enter the Command Center in a moment...
                </motion.p>
              </div>
            </div>
          </motion.div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
       {/* Ambient Background */}
       <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[hsl(var(--brand-primary))] opacity-[0.03] blur-[100px] rounded-full" />
      </div>

      <div className="relative z-10 w-full">
        <AnimatePresence mode="wait">
          {renderStep()}
        </AnimatePresence>
      </div>
    </div>
  );
}
