"use client";
import React from "react";
import { CheckCircle2, CircleDashed, Rocket, Clock, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
    const router = useRouter();

    return (
        <div className="p-6 md:p-12 max-w-4xl mx-auto space-y-12">
            <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-2"
            >
                <h1 className="text-4xl font-bold text-white tracking-tight">Mission Control</h1>
                <p className="text-[hsl(var(--text-secondary))] text-lg">Your sales engine is powering up.</p>
            </motion.div>

            <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-3xl p-8 shadow-2xl relative overflow-hidden">
                {/* Subtle gradient background */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-[hsl(var(--brand-primary))]/5 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="space-y-0 relative z-10">
                    
                    {/* Step 1: Done */}
                    <div className="flex items-start gap-6 pb-10 relative">
                        <div className="absolute left-[15px] top-8 bottom-0 w-[2px] bg-[#10B981]/30"></div>
                        <div className="w-8 h-8 rounded-full bg-[#10B981]/20 border border-[#10B981] flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(16,185,129,0.3)] z-10">
                            <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
                        </div>
                        <div className="pt-1 w-full group">
                            <div className="flex justify-between items-center mb-1">
                                <h3 className="text-lg font-bold text-white group-hover:text-[#10B981] transition-colors">Business Knowledge</h3>
                                <span className="text-xs font-bold uppercase tracking-wider text-[#10B981] bg-[#10B981]/10 px-3 py-1 rounded-full flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse"></span>
                                    Ready
                                </span>
                            </div>
                            <p className="text-sm text-gray-400">Visoora has mapped your industry, positioning, and evidence.</p>
                        </div>
                    </div>

                    {/* Step 2: Active / Next */}
                    <div className="flex items-start gap-6 pb-10 relative">
                        <div className="absolute left-[15px] top-8 bottom-0 w-[2px] bg-white/10 border-l-2 border-dashed border-gray-600"></div>
                        <div className="w-8 h-8 rounded-full bg-[hsl(var(--brand-primary))]/20 border border-[hsl(var(--brand-primary))] flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(0,240,255,0.2)] z-10">
                            <span className="w-2.5 h-2.5 rounded-full bg-[hsl(var(--brand-primary))] animate-ping absolute"></span>
                            <span className="w-2.5 h-2.5 rounded-full bg-[hsl(var(--brand-primary))]"></span>
                        </div>
                        <div className="pt-1 w-full bg-white/5 border border-[hsl(var(--border-subtle))] p-6 rounded-2xl -mt-5 hover:-translate-y-[2px] transition-transform cursor-pointer group" onClick={() => router.push('/business-map')}>
                            <div className="flex justify-between items-center mb-2">
                                <h3 className="text-lg font-bold text-white group-hover:text-[hsl(var(--brand-primary))] transition-colors">Next mission: Generate ICP</h3>
                                <div className="flex items-center gap-2 text-gray-400 text-xs font-semibold bg-black/40 px-3 py-1 rounded-full">
                                    <Clock className="w-3 h-3" /> 45 sec
                                </div>
                            </div>
                            <p className="text-sm text-gray-400 mb-4">We need to define exactly who we are selling to.</p>
                            <button className="text-sm font-bold text-black bg-[hsl(var(--brand-primary))] hover:bg-white px-5 py-2.5 rounded-xl transition-colors flex items-center gap-2">
                                <Zap className="w-4 h-4 fill-current" /> Start Mission
                            </button>
                        </div>
                    </div>

                    {/* Step 3: Locked */}
                    <div className="flex items-start gap-6 pb-10 relative opacity-50">
                        <div className="absolute left-[15px] top-8 bottom-0 w-[2px] bg-white/10 border-l-2 border-dashed border-gray-600"></div>
                        <div className="w-8 h-8 rounded-full border border-gray-600 flex items-center justify-center shrink-0 bg-[#111] z-10">
                            <CircleDashed className="w-5 h-5 text-gray-500" />
                        </div>
                        <div className="pt-1 w-full flex justify-between items-center">
                            <div>
                                <h3 className="text-lg font-bold text-gray-300 mb-1">After that: Import Contacts</h3>
                                <p className="text-sm text-gray-500">Provide the leads you want to reach.</p>
                            </div>
                            <div className="flex items-center gap-2 text-gray-500 text-xs font-semibold">
                                <Clock className="w-3 h-3" /> 2 min
                            </div>
                        </div>
                    </div>

                    {/* Step 4: Locked */}
                    <div className="flex items-start gap-6 pb-10 relative opacity-50">
                        <div className="absolute left-[15px] top-8 bottom-0 w-[2px] bg-white/10 border-l-2 border-dashed border-gray-600"></div>
                        <div className="w-8 h-8 rounded-full border border-gray-600 flex items-center justify-center shrink-0 bg-[#111] z-10">
                            <CircleDashed className="w-5 h-5 text-gray-500" />
                        </div>
                        <div className="pt-1 w-full flex justify-between items-center">
                            <div>
                                <h3 className="text-lg font-bold text-gray-300 mb-1">Then: Generate Emails</h3>
                                <p className="text-sm text-gray-500">AI researches and drafts personalized outreach.</p>
                            </div>
                            <div className="flex items-center gap-2 text-gray-500 text-xs font-semibold">
                                <Clock className="w-3 h-3" /> 3 min
                            </div>
                        </div>
                    </div>

                    {/* Goal */}
                    <div className="flex items-start gap-6 relative">
                        <div className="w-8 h-8 rounded-full bg-white/5 border border-white/20 flex items-center justify-center shrink-0 z-10 mt-1">
                            <Rocket className="w-4 h-4 text-white" />
                        </div>
                        <div className="pt-1 w-full flex justify-between items-center">
                            <h3 className="text-xl font-bold text-white">Ready to launch</h3>
                            <div className="flex items-center gap-2 text-[hsl(var(--brand-primary))] text-sm font-bold bg-[hsl(var(--brand-primary))]/10 px-4 py-2 rounded-full border border-[hsl(var(--brand-primary))]/20">
                                Estimated 8 min total
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
