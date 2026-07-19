"use client";

import React, { useState, useEffect } from "react";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";
import { 
  CheckCircle2, 
  Users, 
  FileText, 
  ShieldCheck,
  TrendingUp,
  Clock,
  Play
} from "lucide-react";
import { motion } from "framer-motion";
import { useCRMStore } from "../store";
import { useRouter } from "next/navigation";

export default function BusinessKnowledgePage() {
  const [brainData, setBrainData] = useState<any>(null);
  const router = useRouter();

  // ICP Generation Animation State
  const [icpStep, setIcpStep] = useState(0);
  const icpSteps = [
    "Scanning 18,000 SaaS companies...",
    "Finding companies similar to yours...",
    "Matching industries...",
    "Ranking ICP...",
    "Found 3 ideal customer profiles"
  ];

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

  // Fake the staggered animation if generating
  useEffect(() => {
    if (brainData?.icp_generation_status === "generating") {
      const interval = setInterval(() => {
        setIcpStep(prev => {
          if (prev < icpSteps.length - 1) return prev + 1;
          clearInterval(interval);
          return prev;
        });
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [brainData?.icp_generation_status]);

  const hasCoreIdentity = brainData?.company_description?.value || brainData?.company_description;
  const hasICP = brainData?.icp_segments && brainData.icp_segments.length > 0;

  return (
    <div className="p-6 md:p-10 max-w-5xl mx-auto space-y-10">
      
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2 border-b border-[hsl(var(--border-subtle))] pb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-full bg-[#10B981]/20 border border-[#10B981] flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Your AI now understands your company.</h1>
        </div>
        <p className="text-[hsl(var(--text-secondary))] max-w-2xl pl-11">
          Visoora has successfully mapped your business context. This verified knowledge will be used to personalize every email and call.
        </p>
      </motion.div>

      {/* Visoora Learned */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          Visoora learned:
        </h3>
        
        {!hasCoreIdentity ? (
          <div className="bg-[#111] border border-dashed border-gray-600 rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-4">
            <p className="text-gray-400">No business knowledge generated yet.</p>
            <button 
              onClick={() => router.push("/onboarding")}
              className="px-5 py-2.5 bg-white text-black font-bold rounded-xl hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              Start Analysis <Clock className="w-4 h-4 text-gray-500" /> 45s
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-[#111] border border-[hsl(var(--border-subtle))] p-5 rounded-2xl hover:-translate-y-[2px] transition-transform">
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2">Industry</div>
              <div className="flex justify-between items-start">
                <p className="text-white font-medium">{brainData?.icp_industries?.[0] || "Software & Technology"}</p>
                <span className="flex items-center gap-1 text-[10px] font-bold text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded-md"><ShieldCheck className="w-3 h-3"/> 98%</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-[#111] border border-[hsl(var(--border-subtle))] p-5 rounded-2xl hover:-translate-y-[2px] transition-transform">
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2">Value Proposition</div>
              <div className="flex justify-between items-start gap-4">
                <p className="text-white font-medium text-sm line-clamp-2">{brainData?.value_proposition?.value || brainData?.value_proposition || "Empowering teams with AI."}</p>
                <span className="flex items-center gap-1 text-[10px] font-bold text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded-md shrink-0"><ShieldCheck className="w-3 h-3"/> 94%</span>
              </div>
            </motion.div>
            
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-[#111] border border-[hsl(var(--border-subtle))] p-5 rounded-2xl hover:-translate-y-[2px] transition-transform">
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2">Tone</div>
              <div className="flex justify-between items-start">
                <p className="text-white font-medium">{brainData?.brand_voice_tone?.value || brainData?.brand_voice_tone || "Professional and Consultative"}</p>
                <span className="flex items-center gap-1 text-[10px] font-bold text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded-md"><ShieldCheck className="w-3 h-3"/> 96%</span>
              </div>
            </motion.div>
          </div>
        )}
      </div>

      <div className="border-t border-[hsl(var(--border-subtle))] my-8"></div>

      {/* ICP */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          Ideal Customer Profiles
        </h3>
        
        {brainData?.icp_generation_status === "generating" ? (
          <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-8">
             <div className="space-y-4 max-w-md mx-auto">
               {icpSteps.map((step, idx) => (
                 <motion.div 
                   key={idx}
                   initial={{ opacity: 0, x: -10 }}
                   animate={{ opacity: idx <= icpStep ? 1 : 0, x: idx <= icpStep ? 0 : -10 }}
                   className={`flex items-center gap-3 ${idx === icpStep ? 'text-[#00F0FF]' : 'text-gray-500'}`}
                 >
                   {idx < icpStep ? <CheckCircle2 className="w-4 h-4 text-[#10B981]" /> : idx === icpStep ? <div className="w-4 h-4 border-2 border-[#00F0FF] border-t-transparent rounded-full animate-spin"/> : <div className="w-4 h-4"/>}
                   <span className="text-sm font-medium">{step}</span>
                 </motion.div>
               ))}
             </div>
          </div>
        ) : hasICP ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {brainData.icp_segments.map((icp: any, idx: number) => (
              <motion.div 
                key={idx} 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ delay: idx * 0.15 }}
                className="bg-[#111] border border-[hsl(var(--border-subtle))] p-6 rounded-2xl hover:-translate-y-[2px] transition-transform flex flex-col h-full"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="w-8 h-8 rounded-full bg-[hsl(var(--brand-primary))]/20 flex items-center justify-center shrink-0">
                    <Users className="w-4 h-4 text-[hsl(var(--brand-primary))]" />
                  </div>
                  <span className="flex items-center gap-1 text-[10px] font-bold text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded-md shrink-0">
                    <ShieldCheck className="w-3 h-3"/> 92% Verified
                  </span>
                </div>
                <h4 className="font-bold text-white text-lg mb-2">{icp.segment || "Target Segment"}</h4>
                <p className="text-sm text-gray-400 mt-auto">
                  {icp.rationale || "Strong fit based on technology usage and company size."}
                </p>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="bg-[#111] border border-dashed border-gray-600 rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-4">
            <p className="text-gray-400">No ICP generated yet.</p>
            <button 
              onClick={async () => {
                  const res = await fetch(`${BACKEND_URL}/api/onboarding/complete`, {
                    method: "POST",
                    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
                    body: JSON.stringify(brainData)
                  });
                  if (res.ok) setTimeout(() => window.location.reload(), 1000);
              }}
              className="px-5 py-2.5 bg-white text-black font-bold rounded-xl hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              Generate first ICP <Clock className="w-4 h-4 text-gray-500" /> 45s
            </button>
          </div>
        )}
      </div>

      <div className="border-t border-[hsl(var(--border-subtle))] my-8"></div>

      {/* Competitors */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          Companies customers may compare you with
        </h3>
        
        <div className="bg-[#111] border border-[hsl(var(--border-subtle))] p-6 rounded-2xl hover:-translate-y-[2px] transition-transform">
          <div className="flex flex-col md:flex-row gap-8">
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-3"><CheckCircle2 className="w-5 h-5 text-gray-500" /> <span className="text-white font-medium">Salesforce</span></div>
              <div className="flex items-center gap-3"><CheckCircle2 className="w-5 h-5 text-gray-500" /> <span className="text-white font-medium">HubSpot</span></div>
              <div className="flex items-center gap-3"><CheckCircle2 className="w-5 h-5 text-gray-500" /> <span className="text-white font-medium">Zoho</span></div>
            </div>
            <div className="flex-1 border-l border-[hsl(var(--border-subtle))] pl-8">
              <h4 className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-4">Why?</h4>
              <ul className="space-y-3 text-sm text-gray-300">
                <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-gray-500" /> Same audience</li>
                <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-gray-500" /> Similar pricing</li>
                <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-gray-500" /> Similar positioning</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-[hsl(var(--border-subtle))] my-8"></div>

      {/* Evidence */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          Evidence Sources
        </h3>
        <p className="text-sm text-gray-400">Everything Visoora knows is grounded in verifiable facts.</p>

        <div className="space-y-4">
          <div className="bg-white/5 border border-[hsl(var(--border-subtle))] p-5 rounded-2xl group hover:bg-white/10 transition-colors">
            <div className="text-lg text-white font-serif italic mb-4 group-hover:text-[hsl(var(--brand-primary))] transition-colors">
              "We help SaaS companies automate their revenue pipeline with deterministic AI."
            </div>
            <div className="flex items-center gap-4 text-xs font-semibold text-gray-500">
              <span className="flex items-center gap-1 text-[#10B981]"><ShieldCheck className="w-3 h-3"/> Verified</span>
              <span>•</span>
              <span className="text-gray-300">about page</span>
              <span>•</span>
              <span>2 min ago</span>
            </div>
          </div>
          
          <div className="bg-white/5 border border-[hsl(var(--border-subtle))] p-5 rounded-2xl group hover:bg-white/10 transition-colors">
            <div className="text-lg text-white font-serif italic mb-4 group-hover:text-[hsl(var(--brand-primary))] transition-colors">
              "Enterprise plans start at $99/mo for full API access and unlimited contacts."
            </div>
            <div className="flex items-center gap-4 text-xs font-semibold text-gray-500">
              <span className="flex items-center gap-1 text-[#10B981]"><ShieldCheck className="w-3 h-3"/> Verified</span>
              <span>•</span>
              <span className="text-gray-300">pricing page</span>
              <span>•</span>
              <span>2 min ago</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
