"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Globe, Search, Target, Briefcase, BarChart3, Users, 
  AlertTriangle, Shield, CheckCircle2, ArrowRight, TrendingUp, Zap, Clock, FileText
} from "lucide-react";
import Link from "next/link";

export default function DemoReport({ 
  analysisData, 
  demoPhase, 
  demoError 
}: { 
  analysisData: any; 
  demoPhase: number; 
  demoError: string | null; 
}) {
  const [activeTab, setActiveTab] = useState("overview");
  const [isPrinting, setIsPrinting] = useState(false);

  const handlePrint = () => {
    setIsPrinting(true);
    setTimeout(() => {
      window.print();
      setIsPrinting(false);
    }, 150);
  };

  // Premium loading sequence steps
  const loadingSteps = [
    "Initializing Strategic Analysis...",
    "Reading Website & Metadata...",
    "Detecting Industry & Business Model...",
    "Understanding Products & Services...",
    "Identifying Ideal Customer Profile (ICP)...",
    "Researching Competitors...",
    "Building Buyer Personas...",
    "Calculating Revenue Opportunities...",
    "Generating 90-Day Growth Strategy...",
    "Finalizing Report..."
  ];

  const isLoading = demoPhase > 0 && !analysisData && !demoError;

  if (demoPhase === 0) {
    return (
      <div className="p-12 text-center">
        <Search className="w-10 h-10 text-[hsl(var(--text-muted))] mx-auto mb-4 opacity-40" />
        <p className="text-sm text-[hsl(var(--text-muted))]">
          Enter a website URL above to generate your AI Growth Strategy Report.
        </p>
      </div>
    );
  }

  if (demoError) {
    return (
      <div className="p-12 text-center text-rose-400">
        <AlertTriangle className="w-10 h-10 mx-auto mb-4 opacity-80" />
        <p className="font-semibold mb-2">Analysis Failed</p>
        <p className="text-sm">{demoError}</p>
      </div>
    );
  }

  if (isLoading) {
    // Show premium loading sequence based on demoPhase (1 to 10)
    const currentStepIndex = Math.min(demoPhase - 1, loadingSteps.length - 1);
    
    return (
      <div className="p-8 sm:p-12">
        <div className="max-w-md mx-auto space-y-4">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-lg font-bold text-white tracking-tight">AI Strategy Engine</h3>
            <div className="text-sm text-[hsl(var(--brand-primary))] font-mono">
              {Math.round(((currentStepIndex + 1) / loadingSteps.length) * 100)}%
            </div>
          </div>
          
          <div className="space-y-3">
            {loadingSteps.map((step, index) => {
              const isPast = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;
              const isFuture = index > currentStepIndex;
              
              return (
                <div 
                  key={index} 
                  className={`flex items-center gap-3 text-sm transition-all duration-300 ${
                    isPast ? "text-emerald-400" : 
                    isCurrent ? "text-white font-medium scale-105 origin-left" : 
                    "text-zinc-600"
                  }`}
                >
                  {isPast ? (
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  ) : isCurrent ? (
                    <div className="w-4 h-4 rounded-full border-2 border-[hsl(var(--brand-primary))] border-t-transparent animate-spin flex-shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-zinc-700 flex-shrink-0" />
                  )}
                  {step}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  if (!analysisData) return null;

  const data = analysisData;
  const exec = data.executive_summary || {};
  const biz = data.business_intelligence || {};
  const health = data.website_health || {};
  const ai = data.ai_understanding || {};

  const tabs = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "business", label: "Business", icon: Briefcase },
    { id: "customers", label: "Customers", icon: Users },
    { id: "competition", label: "Competition", icon: Shield },
    { id: "growth", label: "Growth", icon: TrendingUp },
  ];

  // Helper to handle both string and object formats returned by LLM
  const getVal = (obj: any) => {
    if (!obj) return 'N/A';
    if (typeof obj === 'string') return obj;
    return obj.value || 'N/A';
  };
  const getSource = (obj: any) => {
    if (!obj) return 'ESTIMATED';
    if (typeof obj === 'string') return 'ESTIMATED';
    return obj.source_type || 'ESTIMATED';
  };
  const getArray = (arr: any) => Array.isArray(arr) ? arr : [];

  return (
    <div className={`flex flex-col overflow-hidden bg-zinc-950/40 relative ${isPrinting ? 'h-auto print:bg-black' : 'h-[600px]'}`}>
      {/* PRINT ONLY VISUORA MARKETING HEADER */}
      <div className="hidden print:flex flex-col items-center justify-center py-8 border-b border-zinc-800 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-[hsl(var(--brand-primary))] flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-white">Visoora</span>
        </div>
        <p className="text-[hsl(var(--text-muted))] text-sm">Automating growth for B2B teams. Start your free trial at visoora.com</p>
      </div>

      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-800/60 bg-zinc-900/40 flex items-center justify-between print:border-none print:bg-transparent">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">AI Growth Strategy Report</h3>
          <p className="text-xs text-[hsl(var(--text-muted))] mt-1">Generated by Visoora Strategic Engine</p>
        </div>
        <div className="flex items-center gap-3 print:hidden">
          <span className="text-xs font-semibold px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded border border-emerald-500/20">Confidence: {exec.ai_confidence || '92%'}</span>
          <Link
            href="/"
            className="px-3 py-1.5 text-xs font-bold bg-zinc-800 text-white hover:bg-zinc-700 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <Search className="w-3.5 h-3.5" />
            New Analysis
          </Link>
          <button 
            onClick={handlePrint} 
            className="px-3 py-1.5 text-xs font-bold bg-[hsl(var(--brand-primary))] text-white hover:opacity-90 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            Download PDF
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto border-b border-zinc-800/60 px-4 py-2 scrollbar-none shrink-0 print:hidden">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
              activeTab === tab.id 
                ? "bg-zinc-800 text-white" 
                : "text-[hsl(var(--text-muted))] hover:text-white hover:bg-zinc-800/50"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar print:overflow-visible print:h-auto print:space-y-12">
        
        {/* OVERVIEW TAB */}
        {(activeTab === "overview" || isPrinting) && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPrinting && <h3 className="text-xl font-bold text-white mb-2 pb-2 border-b border-zinc-800">1. Executive Overview</h3>}
            {/* The WOW Moment */}
            <div className="p-5 rounded-xl border border-[hsl(var(--brand-primary))]/30 bg-[hsl(var(--brand-primary))]/5">
              <h4 className="text-sm font-bold text-[hsl(var(--brand-primary))] uppercase tracking-wider mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4" /> Strategic Conclusion
              </h4>
              <p className="text-lg text-white font-medium leading-relaxed">
                "{exec.wow_statement || "After analyzing your business, Visoora believes your biggest opportunity is expanding your focus where buying intent is significantly higher than your current positioning."}"
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                <p className="text-xs text-[hsl(var(--text-muted))] mb-1">Growth Score</p>
                <p className="text-2xl font-bold text-emerald-400">{exec.overall_growth_score || 84}<span className="text-sm text-zinc-500">/100</span></p>
              </div>
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                <p className="text-xs text-[hsl(var(--text-muted))] mb-1">Potential</p>
                <p className="text-2xl font-bold text-white">{exec.growth_potential || "High"}</p>
              </div>
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                <p className="text-xs text-[hsl(var(--text-muted))] mb-1">Revenue Opp</p>
                <p className="text-xl font-bold text-emerald-400">{exec.revenue_opportunity || "$200k+"}</p>
              </div>
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                <p className="text-xs text-[hsl(var(--text-muted))] mb-1">Time to Results</p>
                <p className="text-lg font-bold text-white mt-1">{exec.time_to_results || "30-60 Days"}</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-zinc-800 pb-2">Website Health</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Messaging", score: health.messaging?.score || 85 },
                  { label: "Trust", score: health.trust?.score || 60 },
                  { label: "Conversion", score: health.conversion?.score || 72 },
                  { label: "UX", score: health.ux?.score || 90 },
                ].map((h, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/30 border border-zinc-800/30">
                    <span className="text-sm text-[hsl(var(--text-secondary))]">{h.label}</span>
                    <span className={`text-sm font-bold ${h.score > 80 ? 'text-emerald-400' : h.score > 60 ? 'text-amber-400' : 'text-rose-400'}`}>
                      {h.score}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* BUSINESS TAB */}
        {(activeTab === "business" || isPrinting) && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPrinting && <h3 className="text-xl font-bold text-white mb-2 mt-8 pb-2 border-b border-zinc-800">2. Business Intelligence</h3>}
            {!isPrinting && <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-zinc-800 pb-2">Business Intelligence</h4>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              {[
                { label: "Industry", val: biz.industry },
                { label: "Business Model", val: biz.business_model },
                { label: "Target Market", val: biz.target_market },
                { label: "Estimated ACV", val: biz.estimated_acv },
                { label: "Sales Cycle", val: biz.estimated_sales_cycle },
                { label: "Buying Committee", val: biz.buying_committee },
              ].map((item, i) => (
                <div key={i} className="flex flex-col p-3 rounded-lg bg-zinc-900/30 border border-zinc-800/30">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-xs text-[hsl(var(--text-muted))]">{item.label}</span>
                    <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded ${
                      getSource(item.val) === 'Observed' || getSource(item.val) === 'OBSERVED' ? 'bg-emerald-500/10 text-emerald-400' :
                      'bg-amber-500/10 text-amber-400'
                    }`}>
                      {getSource(item.val)}
                    </span>
                  </div>
                  <span className="text-sm text-white font-medium">{getVal(item.val)}</span>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 rounded-xl bg-violet-500/5 border border-violet-500/20">
              <h4 className="text-xs font-bold text-violet-400 uppercase tracking-wider mb-3">AI Understanding: The Value Proposition</h4>
              <div className="space-y-3 text-sm">
                <p><span className="text-[hsl(var(--text-muted))]">Problem Solved:</span> <span className="text-white">{ai.problem_solved}</span></p>
                <p><span className="text-[hsl(var(--text-muted))]">Why Buy Now:</span> <span className="text-white">{ai.why_buy_now}</span></p>
                <p><span className="text-[hsl(var(--text-muted))]">Emotional Outcome:</span> <span className="text-white">{ai.emotional_outcome}</span></p>
              </div>
            </div>
          </div>
        )}

        {/* CUSTOMERS TAB */}
        {(activeTab === "customers" || isPrinting) && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPrinting && <h3 className="text-xl font-bold text-white mb-2 mt-8 pb-2 border-b border-zinc-800">3. Customers & Personas</h3>}
            {!isPrinting && <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-zinc-800 pb-2">Ranked ICP (Ideal Customer Profile)</h4>}
            <div className="space-y-3">
              {getArray(data.icp_discovery).length === 0 && <p className="text-sm text-[hsl(var(--text-muted))]">Loading ICP data...</p>}
              {getArray(data.icp_discovery).map((icp: any, i: number) => (
                <div key={i} className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg font-bold text-white">{icp.name}</span>
                      <span className="text-xs font-bold px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded-full">{icp.match_percentage} Match</span>
                    </div>
                    <p className="text-sm text-[hsl(var(--text-secondary))]">{icp.pain}</p>
                  </div>
                  <div className="flex gap-4 text-xs text-[hsl(var(--text-muted))] md:text-right">
                    <div>
                      <p className="uppercase mb-0.5">Deal Size</p>
                      <p className="text-white font-medium">{icp.expected_deal_size}</p>
                    </div>
                    <div>
                      <p className="uppercase mb-0.5">Urgency</p>
                      <p className="text-white font-medium">{icp.urgency}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* COMPETITION TAB */}
        {(activeTab === "competition" || isPrinting) && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPrinting && <h3 className="text-xl font-bold text-white mb-2 mt-8 pb-2 border-b border-zinc-800">4. Competitor Intelligence</h3>}
            {!isPrinting && <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-zinc-800 pb-2">Competitor Intelligence</h4>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {getArray(data.competitors?.known_competitors || data.competitor_intelligence?.known_competitors).length === 0 && <p className="text-sm text-[hsl(var(--text-muted))]">Loading competitor data...</p>}
              {getArray(data.competitors?.known_competitors || data.competitor_intelligence?.known_competitors).map((comp: any, i: number) => (
                <div key={i} className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                  <h5 className="font-bold text-white text-base mb-2">{comp.name}</h5>
                  <div className="space-y-2 text-sm">
                    <p><span className="text-emerald-400 font-medium">Strength:</span> <span className="text-[hsl(var(--text-secondary))]">{comp.strength}</span></p>
                    <p><span className="text-rose-400 font-medium">Weakness:</span> <span className="text-[hsl(var(--text-secondary))]">{comp.weakness}</span></p>
                    <p><span className="text-amber-400 font-medium">Opportunity Gap:</span> <span className="text-[hsl(var(--text-secondary))]">{comp.opportunity}</span></p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 p-4 rounded-xl bg-[hsl(var(--brand-primary))]/5 border border-[hsl(var(--brand-primary))]/20">
              <h4 className="text-xs font-bold text-[hsl(var(--brand-primary))] uppercase tracking-wider mb-2">Positioning Recommendation</h4>
              <p className="text-sm text-[hsl(var(--text-secondary))] mb-2">Current Perception: <span className="text-white">{data.positioning?.brand_perception || (data.competitors?.positioning?.brand_perception) || (data.competitor_intelligence?.positioning?.brand_perception)}</span></p>
              <p className="text-sm text-white font-medium border-l-2 border-[hsl(var(--brand-primary))] pl-3 py-1">
                {data.positioning?.recommended_positioning_statement || (data.competitors?.positioning?.recommended_positioning_statement) || (data.competitor_intelligence?.positioning?.recommended_positioning_statement)}
              </p>
            </div>
          </div>
        )}

        {/* GROWTH TAB */}
        {(activeTab === "growth" || isPrinting) && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPrinting && <h3 className="text-xl font-bold text-white mb-2 mt-8 pb-2 border-b border-zinc-800">5. Revenue Expansion</h3>}
            {!isPrinting && <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-zinc-800 pb-2">Revenue Expansion Opportunities</h4>}
            <div className="space-y-3">
              {getArray(data.revenue_opportunities).length === 0 && <p className="text-sm text-[hsl(var(--text-muted))]">Loading revenue opportunities...</p>}
              {getArray(data.revenue_opportunities).map((opp: any, i: number) => (
                <div key={i} className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50 flex justify-between items-center">
                  <div>
                    <h5 className="font-bold text-white">{opp.opportunity_name}</h5>
                    <p className="text-sm text-[hsl(var(--text-secondary))]">ROI: {opp.roi} • Time: {opp.time_required}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-[hsl(var(--text-muted))] uppercase mb-1">Expected Revenue</p>
                    <p className="text-lg font-bold text-emerald-400">{opp.expected_revenue}</p>
                  </div>
                </div>
              ))}
            </div>

            <h4 className="text-sm font-bold text-white uppercase tracking-wider mt-8 mb-4 border-b border-zinc-800 pb-2">90-Day Roadmap</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
               <div className="p-4 rounded-xl bg-zinc-900/30 border border-zinc-800/50">
                  <p className="text-xs text-amber-400 font-bold mb-1">Week 1-2</p>
                  <p className="text-sm text-[hsl(var(--text-secondary))]">{data.growth_roadmap?.week_1 || "Fix website messaging"}</p>
               </div>
               <div className="p-4 rounded-xl bg-zinc-900/30 border border-zinc-800/50">
                  <p className="text-xs text-emerald-400 font-bold mb-1">Week 3-4</p>
                  <p className="text-sm text-[hsl(var(--text-secondary))]">{data.growth_roadmap?.week_3 || data.growth_roadmap?.week_4 || "Launch outbound campaigns"}</p>
               </div>
               <div className="p-4 rounded-xl bg-zinc-900/30 border border-zinc-800/50">
                  <p className="text-xs text-violet-400 font-bold mb-1">Month 2-3</p>
                  <p className="text-sm text-[hsl(var(--text-secondary))]">{data.growth_roadmap?.month_2 || data.growth_roadmap?.month_3 || "Scale sales automation"}</p>
               </div>
            </div>
          </div>
        )}

      </div>

      {/* FINAL CTA FOOTER */}
      <div className="p-5 border-t border-zinc-800/60 bg-gradient-to-r from-[hsl(var(--brand-primary))]/10 to-transparent flex flex-col sm:flex-row items-center justify-between gap-4 shrink-0 print:hidden">
        <div>
          <p className="text-sm font-bold text-white mb-1">We've built your Business Brain.</p>
          <p className="text-xs text-[hsl(var(--text-secondary))]">With one click, Visoora can now find companies matching your ICP and book meetings automatically.</p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <button onClick={handlePrint} className="px-4 py-2 text-sm font-bold bg-zinc-800 text-white hover:bg-zinc-700 rounded-lg transition-colors whitespace-nowrap flex items-center gap-2">
            <FileText className="w-4 h-4" /> Download PDF
          </button>
          <Link href={data.report_id ? `/signup?report_id=${data.report_id}` : "/signup"} className="px-4 py-2 text-sm font-bold bg-zinc-800 text-white hover:bg-zinc-700 rounded-lg transition-colors whitespace-nowrap flex items-center gap-2">
            <Target className="w-4 h-4" /> Import to CRM
          </Link>
          <Link href={data.report_id ? `/signup?report_id=${data.report_id}` : "/signup"} className="px-4 py-2 text-sm font-bold bg-white text-black hover:bg-zinc-200 rounded-lg transition-colors whitespace-nowrap flex items-center gap-2">
            <Zap className="w-4 h-4" /> Launch AI SDR
          </Link>
        </div>
      </div>
    </div>
  );
}
