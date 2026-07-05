"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Target, ArrowUpRight, DollarSign, Users, ShieldAlert, Sparkles, Activity, Clock, CheckCircle2, ChevronRight, Zap, Play, Search } from "lucide-react";
import Link from "next/link";
import { BACKEND_URL } from "../../config";
import { getAuthHeaders } from "../../auth/store";

export default function MissionDetailsPage() {
  const { id } = useParams();
  const [mission, setMission] = useState<any>(null);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMissionDetails();
  }, [id]);

  const fetchMissionDetails = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/analytics/missions/${id}/results`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setResults(data);
        setMission({ id, name: "Find Healthcare Prospects", status: "COMPLETED" });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading mission details...</div>;
  }

  if (!results) {
    return <div className="p-8 text-center text-red-500">Failed to load mission results.</div>;
  }

  const { funnel, recent_wins, learnings } = results;

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 pb-20">
      
      {/* Header */}
      <div className="flex justify-between items-end border-b border-[hsl(var(--border-subtle))] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link href="/campaigns" className="text-gray-500 hover:text-white transition-colors text-sm">Missions</Link>
            <ChevronRight className="w-4 h-4 text-gray-700" />
            <span className="text-sm font-semibold text-gray-300">{mission.name}</span>
          </div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Target className="w-8 h-8 text-[#00F0FF]" /> {mission.name}
          </h1>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs bg-[#10B981]/10 text-[#10B981] px-2 py-1 rounded-full border border-[#10B981]/20 font-bold tracking-wider uppercase">
              {mission.status}
            </span>
          </div>
        </div>
      </div>

      {/* Hero Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
         <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10"><DollarSign className="w-16 h-16 text-[#00F0FF]" /></div>
            <h4 className="text-sm font-medium text-gray-400 mb-1">Pipeline Generated</h4>
            <div className="text-4xl font-bold text-white">${funnel.pipeline.toLocaleString()}</div>
         </div>
         <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6">
            <h4 className="text-sm font-medium text-gray-400 mb-1">Meetings Booked</h4>
            <div className="text-4xl font-bold text-white">{funnel.meetings}</div>
         </div>
         <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6">
            <h4 className="text-sm font-medium text-gray-400 mb-1">Total Cost</h4>
            <div className="text-4xl font-bold text-white">{funnel.cost}</div>
         </div>
         <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6 bg-gradient-to-br from-[#111] to-[#10B981]/10">
            <h4 className="text-sm font-medium text-[#10B981] mb-1 flex items-center gap-2"><Activity className="w-4 h-4"/> ROI</h4>
            <div className="text-4xl font-bold text-white">
              {funnel.pipeline > 0 && parseFloat(funnel.cost.replace('$', '')) > 0 
                ? `${Math.round(funnel.pipeline / parseFloat(funnel.cost.replace('$', '')))}x` 
                : '0x'}
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* Main Content Area */}
         <div className="lg:col-span-2 space-y-12">
            
            {/* Section 1: Executive Summary */}
            <div className="space-y-6">
               <h3 className="text-xl font-bold text-white border-b border-[hsl(var(--border-subtle))] pb-2">Section 1: Executive Summary</h3>
               
               <div className="space-y-3">
                  <FunnelStep title="Research" value={funnel.research} icon={<Search className="w-5 h-5 text-blue-400" />} color="bg-blue-400" />
                  <FunnelStep title="Qualified Target" value={funnel.qualified} icon={<Target className="w-5 h-5 text-[#00F0FF]" />} color="bg-[#00F0FF]" />
                  <FunnelStep title="Drafts Generated" value={funnel.drafts} icon={<Sparkles className="w-5 h-5 text-purple-400" />} color="bg-purple-400" />
                  <FunnelStep title="CEO Approvals" value={funnel.approvals} icon={<ShieldAlert className="w-5 h-5 text-yellow-400" />} color="bg-yellow-400" />
                  <FunnelStep title="Outreach Sent" value={funnel.sent} icon={<Zap className="w-5 h-5 text-orange-400" />} color="bg-orange-400" />
                  <FunnelStep title="Replies" value={funnel.replies} icon={<Users className="w-5 h-5 text-pink-400" />} color="bg-pink-400" />
                  <FunnelStep title="Meetings Booked" value={funnel.meetings} icon={<CheckCircle2 className="w-5 h-5 text-[#10B981]" />} color="bg-[#10B981]" />
               </div>
            </div>

            {/* Section 2: Mission Replay */}
            <div className="space-y-6">
               <h3 className="text-xl font-bold text-white border-b border-[hsl(var(--border-subtle))] pb-2">Section 2: Mission Replay</h3>
               
               <div className="space-y-4 border-l border-white/10 ml-4 pl-6 relative">
                  
                  {/* Replay Node 1 */}
                  <div className="relative">
                     <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-blue-500 ring-4 ring-[#111]"></div>
                     <div className="text-xs text-gray-500 font-bold mb-1">09:21 AM • RESEARCH AGENT</div>
                     <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-4 shadow-sm">
                        <div className="font-semibold text-white mb-2">Found 2,143 potential companies</div>
                        <p className="text-sm text-gray-400 mb-3">Scanned Apollo and LinkedIn for companies matching 'Healthcare SaaS'.</p>
                        <div className="flex gap-4 text-xs">
                           <span className="text-gray-500">Cost: <span className="text-white">$0.42</span></span>
                           <span className="text-gray-500">Confidence: <span className="text-white">99%</span></span>
                        </div>
                     </div>
                  </div>

                  {/* Replay Node 2 */}
                  <div className="relative">
                     <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-amber-500 ring-4 ring-[#111]"></div>
                     <div className="text-xs text-gray-500 font-bold mb-1">09:24 AM • QUALIFICATION AGENT</div>
                     <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-4 shadow-sm">
                        <div className="font-semibold text-white mb-2">Removed 1,827 companies</div>
                        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-500 p-2 rounded-lg text-sm mb-3">
                           <strong>Reason:</strong> Outside geographical ICP or company size exceeded 500 employees.
                        </div>
                        <div className="flex gap-4 text-xs">
                           <span className="text-gray-500">Remaining: <span className="text-white">316</span></span>
                           <span className="text-gray-500">Confidence: <span className="text-white">96%</span></span>
                        </div>
                     </div>
                  </div>

                  {/* Replay Node 3 */}
                  <div className="relative">
                     <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-purple-500 ring-4 ring-[#111]"></div>
                     <div className="text-xs text-gray-500 font-bold mb-1">09:28 AM • EMAIL DRAFTER</div>
                     <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-4 shadow-sm">
                        <div className="font-semibold text-white mb-2">Drafted 84 personalized emails</div>
                        <p className="text-sm text-gray-400 mb-3">Mapped pain points (HIPAA compliance, manual scheduling) to value props.</p>
                        <div className="flex gap-4 text-xs">
                           <span className="text-gray-500">Evidence: <span className="text-white">Found 'HIPAA' in 84 job listings</span></span>
                           <span className="text-gray-500">Cost: <span className="text-white">$1.12</span></span>
                        </div>
                     </div>
                  </div>

               </div>
            </div>
         </div>

         {/* Sidebar: Recent Wins & Learnings */}
         <div className="space-y-6">
            
            <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6">
               <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
                  <ArrowUpRight className="w-5 h-5 text-[#10B981]" /> Substantiated Pipeline
               </h3>
               <div className="space-y-4">
                 {recent_wins.length === 0 ? (
                    <p className="text-sm text-gray-500">No meetings booked yet.</p>
                 ) : (
                    recent_wins.map((win: any, idx: number) => (
                       <div key={idx} className="p-3 bg-white/5 border border-white/10 rounded-lg">
                          <div className="flex justify-between items-start mb-1">
                             <div className="text-white font-medium">{win.prospect}</div>
                             <div className="text-[#10B981] font-bold">{win.value}</div>
                          </div>
                          <div className="text-xs text-gray-400">{win.company} • Booked {win.date}</div>
                       </div>
                    ))
                 )}
               </div>
            </div>

            <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6">
               <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
                  <Sparkles className="w-5 h-5 text-purple-400" /> Mission Learnings
               </h3>
               <div className="space-y-4">
                  <div>
                     <div className="text-xs text-gray-500 font-bold uppercase mb-1">Highest Reply Rate</div>
                     <div className="text-sm text-gray-300">{learnings.best_segment}</div>
                  </div>
                  <div>
                     <div className="text-xs text-gray-500 font-bold uppercase mb-1">Best Subject Line</div>
                     <div className="text-sm text-gray-300">{learnings.best_subject}</div>
                  </div>
               </div>
            </div>

            <div className="bg-[#00F0FF]/10 border border-[#00F0FF]/30 rounded-xl p-6 text-center shadow-[0_0_20px_rgba(0,240,255,0.1)]">
               <div className="w-12 h-12 bg-[#00F0FF]/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Play className="w-6 h-6 text-[#00F0FF]" />
               </div>
               <h3 className="text-lg font-bold text-[#00F0FF] mb-2">Recommended Next Mission</h3>
               <p className="text-sm text-gray-300 mb-4">{learnings.recommendation}</p>
               <button className="w-full py-3 bg-[#00F0FF] text-black font-bold rounded-lg hover:opacity-90 transition-opacity">
                  Launch Mission Beta
               </button>
               <div className="flex justify-between items-center text-xs text-gray-500 mt-4">
                  <span>Est. Cost: $8.10</span>
                  <span>Confidence: 94%</span>
               </div>
            </div>

         </div>
      </div>
    </div>
  );
}

function FunnelStep({ title, value, icon, color }: { title: string, value: number, icon: any, color: string }) {
   return (
      <div className="flex items-center gap-4 group">
         <div className="w-12 h-12 rounded-xl bg-[#111] border border-[hsl(var(--border-subtle))] flex items-center justify-center shrink-0 z-10 group-hover:border-white/30 transition-colors">
            {icon}
         </div>
         <div className="flex-1 bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-4 flex items-center justify-between group-hover:border-white/20 transition-colors relative overflow-hidden">
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${color} opacity-50`}></div>
            <span className="text-gray-300 font-medium ml-2">{title}</span>
            <span className="text-white font-bold text-xl">{value}</span>
         </div>
      </div>
   )
}
