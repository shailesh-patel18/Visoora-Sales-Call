"use client";

import React, { useState, useEffect } from "react";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";
import { 
  BrainCircuit, GitCommit, GitPullRequest, Search, CheckCircle2, 
  Target, Users, Zap, ShieldAlert, FileText, ChevronDown, Plus, ArrowRight 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useCRMStore } from "../store";
import { useRouter } from "next/navigation";
import EvidenceCard from "../components/evidence-card";

export default function BusinessBrainPage() {
  const [activeTab, setActiveTab] = useState<"knowledge" | "memory">("knowledge");
  const [brainData, setBrainData] = useState<any>(null);
  const router = useRouter();
  const { markStepComplete, setWorkflowStep } = useCRMStore();

  const handleNextStep = () => {
    markStepComplete(2);
    setWorkflowStep(3);
    router.push("/playbooks");
  };

  useEffect(() => {
    async function loadBrain() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/analytics/business-map`, {
          headers: getAuthHeaders()
        });
        if (res.ok) {
          const data = await res.json();
          setBrainData(data.agent_config);
        }
      } catch (err) {
        console.error("Failed to fetch brain data:", err);
      }
    }
    loadBrain();
  }, []);

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header & Versioning */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-[hsl(var(--border-subtle))] pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <BrainCircuit className="w-8 h-8 text-[#8A2BE2]" /> 
              Business Brain
            </h1>
            <span className="px-3 py-1 bg-[#8A2BE2]/10 text-[#8A2BE2] rounded-full text-xs font-bold tracking-wider border border-[#8A2BE2]/20">
              94% CONFIDENCE
            </span>
          </div>
          <p className="text-[hsl(var(--text-secondary))] max-w-2xl">
            The core intelligence of your AI workforce. Every agent (Research, Email, Voice) relies on this source of truth to execute missions.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-lg px-4 py-2 flex items-center gap-3">
            <GitCommit className="w-4 h-4 text-gray-500" />
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 font-semibold uppercase">Current Version</span>
              <span className="text-sm font-bold text-white">v17.0 (Live)</span>
            </div>
            <button className="ml-2 text-xs text-[#00F0FF] hover:underline">History</button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-[hsl(var(--border-subtle))]">
        <button 
          onClick={() => setActiveTab("knowledge")}
          className={`pb-3 font-semibold text-sm transition-colors ${activeTab === "knowledge" ? "text-white border-b-2 border-[#8A2BE2]" : "text-gray-500 hover:text-gray-300"}`}
        >
          Knowledge Graph
        </button>
        <button 
          onClick={() => setActiveTab("memory")}
          className={`pb-3 font-semibold text-sm transition-colors flex items-center gap-2 ${activeTab === "memory" ? "text-white border-b-2 border-[#8A2BE2]" : "text-gray-500 hover:text-gray-300"}`}
        >
          Learning Engine <span className="w-5 h-5 bg-[#00F0FF]/10 text-[#00F0FF] rounded-full flex items-center justify-center text-[10px]">1</span>
        </button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === "knowledge" ? (
          <motion.div 
            key="knowledge"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid lg:grid-cols-3 gap-6"
          >
            {/* Left Column */}
            <div className="space-y-6">
              {/* Core Identity */}
              <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6 shadow-md">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-500" /> Core Identity
                </h3>
                <div className="space-y-1">
                  <EvidenceCard 
                    title="Industry / Description" 
                    field={brainData?.company_description?.value ? brainData.company_description : { value: brainData?.company_description || "N/A", confidence: 0, snippet: "Manual Entry", source_url: "" }} 
                  />
                  <EvidenceCard 
                    title="Value Proposition" 
                    field={brainData?.value_proposition?.value ? brainData.value_proposition : { value: brainData?.value_proposition || "N/A", confidence: 0, snippet: "Manual Entry", source_url: "" }} 
                  />
                  <EvidenceCard 
                    title="Brand Tone" 
                    field={brainData?.brand_voice_tone?.value ? brainData.brand_voice_tone : { value: brainData?.brand_voice_tone || "N/A", confidence: 0, snippet: "Manual Entry", source_url: "" }} 
                  />
                </div>
              </div>

              {/* Competitors */}
              <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6 shadow-md">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-red-500" /> Competitors & Objections
                </h3>
                <div className="space-y-1">
                  <EvidenceCard 
                    title="Known Competitors" 
                    field={brainData?.potential_competitors?.value ? brainData.potential_competitors : { value: brainData?.competitors || [], confidence: 0, snippet: "Manual Entry", source_url: "" }}
                    renderValue={(val) => (
                      <div className="flex flex-wrap gap-2">
                        {Array.isArray(val) && val.map((c: string, i: number) => (
                          <span key={i} className="px-3 py-1 bg-white/5 border border-[hsl(var(--border-subtle))] rounded-lg text-sm text-gray-300">{c}</span>
                        ))}
                      </div>
                    )}
                  />
                  <EvidenceCard 
                    title="Common Objections" 
                    field={brainData?.potential_objections?.value ? brainData.potential_objections : { value: brainData?.objections_list || [], confidence: 0, snippet: "Manual Entry", source_url: "" }}
                    renderValue={(val) => (
                      <ul className="list-disc pl-4 text-sm text-gray-300 space-y-1">
                        {Array.isArray(val) && val.map((obj: string, i: number) => (
                          <li key={i}>{obj}</li>
                        ))}
                      </ul>
                    )}
                  />
                </div>
              </div>
            </div>

            {/* Middle Column */}
            <div className="space-y-6">
              <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6 shadow-md h-full">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-[#00F0FF]" /> Ideal Customer Profiles (ICP)
                </h3>
                
                <div className="space-y-4">
                  {brainData?.icp_generation_status === "generating" ? (
                    <div className="p-8 bg-[#1a1a1a] rounded-xl border border-[hsl(var(--border-subtle))] flex flex-col items-center justify-center gap-4">
                      <div className="w-8 h-8 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin"></div>
                      <p className="text-sm text-gray-300 font-semibold animate-pulse">Generating ICP Segments...</p>
                      <p className="text-xs text-gray-500">This usually takes about 10 seconds.</p>
                    </div>
                  ) : brainData?.icp_segments && brainData.icp_segments.length > 0 ? (
                    brainData.icp_segments.map((icp: any, idx: number) => (
                      <div key={idx} className="p-4 bg-[#1a1a1a] rounded-xl border border-[hsl(var(--border-subtle))]">
                        <h4 className="font-semibold text-white">{idx + 1}. {icp.segment || "Unnamed ICP Segment"}</h4>
                        <div className="flex items-center gap-2 mt-1 mb-3">
                          <span className="text-xs text-gray-400">Confidence: {icp.confidence || 0}%</span>
                          <div className="w-16 h-1 bg-[#333] rounded-full overflow-hidden">
                             <div className="h-full bg-[#00F0FF]" style={{ width: `${icp.confidence || 0}%` }}></div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="text-sm">
                            <span className="text-gray-500 block text-xs uppercase">Rationale</span>
                            <span className="text-gray-300">{icp.rationale || "No rationale provided."}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-6 bg-[#1a1a1a] rounded-xl border border-[hsl(var(--border-subtle))] flex flex-col items-center justify-center text-center gap-4">
                      <p className="text-sm text-gray-400">No ICP Segments generated yet.</p>
                      {brainData?.icp_generation_status === "failed" && (
                        <p className="text-xs text-red-400">The generation process failed.</p>
                      )}
                      <button 
                        onClick={async () => {
                           // Trigger manual ICP generation
                           const res = await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
                             method: "POST",
                             headers: {
                               ...getAuthHeaders(),
                               "Content-Type": "application/json",
                             },
                             body: JSON.stringify(brainData)
                           });
                           if (res.ok) {
                             // Reload data after 1 sec
                             setTimeout(() => window.location.reload(), 1000);
                           }
                        }}
                        className="px-4 py-2 bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/30 rounded-lg hover:bg-[#00F0FF]/20 transition-colors text-sm font-semibold"
                      >
                        Generate ICP Now
                      </button>
                    </div>
                  )}

                  <div className="p-4 bg-white/5 rounded-xl border border-dashed border-gray-600 flex items-center justify-center cursor-pointer hover:bg-white/10 transition-colors">
                    <span className="text-sm font-semibold text-gray-400 flex items-center gap-2"><Plus className="w-4 h-4"/> Add New ICP</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6 shadow-md h-full">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[#10B981]" /> Knowledge Sources
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-[hsl(var(--border-subtle))]">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                      <span className="text-sm text-gray-200">Company Website</span>
                    </div>
                    <span className="text-xs text-gray-500">Synced 2h ago</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-[hsl(var(--border-subtle))]">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                      <span className="text-sm text-gray-200">HubSpot CRM Data</span>
                    </div>
                    <span className="text-xs text-gray-500">Synced 12h ago</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-[hsl(var(--border-subtle))] opacity-60">
                    <div className="flex items-center gap-3">
                      <span className="w-4 h-4 rounded-full border border-gray-500" />
                      <span className="text-sm text-gray-400">Past Call Transcripts</span>
                    </div>
                    <span className="text-xs text-gray-500">Missing</span>
                  </div>
                </div>
              </div>
            </div>

          </motion.div>
        ) : (
          <motion.div 
            key="memory"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Learning Engine Proposals */}
            <div className="bg-[#111] border border-[#00F0FF]/30 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(0,240,255,0.05)]">
              <div className="p-4 bg-[#00F0FF]/10 border-b border-[#00F0FF]/20 flex items-center gap-3">
                <GitPullRequest className="w-5 h-5 text-[#00F0FF]" />
                <h3 className="font-semibold text-[#00F0FF]">1 Pending Memory Update</h3>
              </div>
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">New Pattern Discovered: Pricing Objection</h4>
                    <p className="text-sm text-gray-400 max-w-2xl">
                      The Learning Engine observed a recurring pattern in the last 48 hours of sales calls. 
                      Prospects are directly comparing our service to Clay.com and citing budget constraints.
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-500 uppercase font-semibold">Confidence</span>
                    <div className="text-xl font-bold text-[#10B981]">91%</div>
                  </div>
                </div>

                <div className="bg-black border border-[hsl(var(--border-subtle))] rounded-xl p-4 mb-6">
                  <h5 className="text-xs font-semibold text-gray-500 uppercase mb-3">Proposed Addition to Business Brain (Objection Matrix)</h5>
                  <div className="text-sm text-gray-300 font-mono">
                    <span className="text-[#00F0FF]">Objection:</span> "You are more expensive than Clay."<br/><br/>
                    <span className="text-[#10B981]">Response:</span> "I understand we are more expensive than raw scraping tools like Clay. However, you aren't paying for raw data. You're paying for an AI workforce that autonomously actions that data, saving you 40+ hours a week in manual SDR work."
                  </div>
                </div>

                <div className="flex gap-3">
                  <button className="px-6 py-2 bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold rounded-lg hover:shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all">
                    Apply to v18.0
                  </button>
                  <button className="px-6 py-2 bg-white/5 text-gray-300 font-semibold rounded-lg hover:bg-white/10 transition-colors">
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Next Step Progression */}
      <div className="flex justify-end pt-8 mt-8 border-t border-[hsl(var(--border-subtle))]">
        <button 
          onClick={handleNextStep}
          className="px-8 py-3 bg-gradient-to-r from-[#00F0FF] to-[#0080FF] text-white font-bold rounded-xl shadow-[0_0_20px_rgba(0,240,255,0.3)] hover:shadow-[0_0_30px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2"
        >
          Continue to Playbooks
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
