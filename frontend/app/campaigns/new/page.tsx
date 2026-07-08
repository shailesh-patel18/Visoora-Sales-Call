"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, ArrowLeft, Target, Rocket, Users, Briefcase } from "lucide-react";
import { useRouter } from "next/navigation";
import { getAuthHeaders } from "../../auth/store";
import { BACKEND_URL } from "../../config";

export default function NewMissionPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    
    // Form State
    const [missionName, setMissionName] = useState("");
    const [objective, setObjective] = useState("");
    const [audience, setAudience] = useState("");

    const handleNext = () => setStep(prev => prev + 1);
    const handleBack = () => setStep(prev => prev - 1);

    const handleLaunch = async () => {
        if (!missionName || !objective || !audience) return;
        setLoading(true);
        try {
            const res = await fetch(`${BACKEND_URL}/api/analytics/missions/launch`, {
                method: "POST",
                headers: {
                    ...getAuthHeaders(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    mission_name: missionName,
                    goal: objective,
                    audience: audience
                })
            });
            if (res.ok) {
                await res.json();
                router.push("/dashboard");
            } else {
                console.error("Failed to launch mission");
                setLoading(false);
            }
        } catch (error) {
            console.error("Launch error:", error);
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen p-6 md:p-12 max-w-4xl mx-auto flex flex-col justify-center relative">
            
            <div className="absolute top-8 left-8">
                <button onClick={() => router.push("/campaigns")} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                    <ArrowLeft className="w-5 h-5" /> Back to Missions
                </button>
            </div>

            <div className="mb-12 text-center">
                <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">
                    Create New Mission
                </h1>
                <p className="text-gray-500 mt-3 text-lg">Configure your autonomous AI research and outreach agent.</p>
                
                {/* Progress Bar */}
                <div className="flex justify-center items-center mt-10 gap-4">
                    {[1, 2, 3].map(s => (
                        <div key={s} className="flex items-center gap-4">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-colors ${step >= s ? 'bg-[#00F0FF] text-black shadow-[0_0_15px_rgba(0,240,255,0.4)]' : 'bg-[#222] text-gray-500'}`}>
                                {s}
                            </div>
                            {s < 3 && <div className={`w-12 h-1 rounded-full ${step > s ? 'bg-[#00F0FF]' : 'bg-[#222]'}`} />}
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-[#0a0a0a] border border-white/10 rounded-3xl p-8 shadow-2xl relative overflow-hidden min-h-[400px]">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#00F0FF] to-[#10B981] opacity-50" />
                
                <AnimatePresence mode="wait">
                    {step === 1 && (
                        <motion.div
                            key="step1"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Target className="w-6 h-6 text-[#00F0FF]" /> Step 1: Mission Objective
                            </h2>
                            <p className="text-gray-400">Give your mission a name and select its primary goal.</p>
                            
                            <div className="space-y-4 pt-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Mission Name</label>
                                    <input 
                                        type="text" 
                                        value={missionName}
                                        onChange={(e) => setMissionName(e.target.value)}
                                        placeholder="e.g. Q4 Healthcare Outreach"
                                        className="w-full bg-[#111] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00F0FF] transition-colors"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2 mt-6">Select Objective</label>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {[
                                            { id: "cold_outreach", label: "Cold Outbound", icon: Briefcase, desc: "Research net-new accounts and draft personalized introductions." },
                                            { id: "inbound_followup", label: "Inbound Follow-up", icon: Users, desc: "Instantly research inbound leads and draft relevant responses." }
                                        ].map(obj => (
                                            <div 
                                                key={obj.id}
                                                onClick={() => setObjective(obj.id)}
                                                className={`p-4 rounded-xl border cursor-pointer transition-all ${objective === obj.id ? 'bg-[#00F0FF]/10 border-[#00F0FF]' : 'bg-[#111] border-white/5 hover:border-white/20'}`}
                                            >
                                                <obj.icon className={`w-6 h-6 mb-3 ${objective === obj.id ? 'text-[#00F0FF]' : 'text-gray-500'}`} />
                                                <div className="font-semibold text-white">{obj.label}</div>
                                                <div className="text-xs text-gray-400 mt-1">{obj.desc}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end pt-8">
                                <button 
                                    onClick={handleNext} 
                                    disabled={!missionName || !objective}
                                    className="px-6 py-3 bg-white text-black font-bold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 transition-colors flex items-center gap-2"
                                >
                                    Continue <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 2 && (
                        <motion.div
                            key="step2"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Users className="w-6 h-6 text-[#00F0FF]" /> Step 2: Target Audience (ICP)
                            </h2>
                            <p className="text-gray-400">Describe the ideal customer profile for this specific mission.</p>
                            
                            <div className="pt-4">
                                <label className="block text-sm font-medium text-gray-300 mb-2">Audience Description</label>
                                <textarea 
                                    value={audience}
                                    onChange={(e) => setAudience(e.target.value)}
                                    placeholder="e.g. Founders and CEOs of B2B SaaS companies in the healthcare sector with 50-200 employees."
                                    className="w-full bg-[#111] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00F0FF] transition-colors h-40 resize-none"
                                />
                                <p className="text-xs text-gray-500 mt-2">Visoora will use this profile to filter leads and personalize outreach angles.</p>
                            </div>

                            <div className="flex justify-between pt-8">
                                <button onClick={handleBack} className="px-6 py-3 text-gray-400 hover:text-white transition-colors flex items-center gap-2">
                                    <ArrowLeft className="w-4 h-4" /> Back
                                </button>
                                <button 
                                    onClick={handleNext} 
                                    disabled={!audience}
                                    className="px-6 py-3 bg-white text-black font-bold rounded-lg disabled:opacity-50 hover:bg-gray-200 transition-colors flex items-center gap-2"
                                >
                                    Review Mission <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 3 && (
                        <motion.div
                            key="step3"
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Rocket className="w-6 h-6 text-[#00F0FF]" /> Step 3: Launch Mission
                            </h2>
                            <p className="text-gray-400">Review your mission parameters before deploying the AI.</p>
                            
                            <div className="bg-[#111] border border-white/10 rounded-xl p-6 space-y-4 mt-6">
                                <div className="grid grid-cols-3 gap-4 border-b border-white/5 pb-4">
                                    <div className="text-gray-500 text-sm font-medium">Mission Name</div>
                                    <div className="col-span-2 text-white font-semibold">{missionName}</div>
                                </div>
                                <div className="grid grid-cols-3 gap-4 border-b border-white/5 pb-4">
                                    <div className="text-gray-500 text-sm font-medium">Objective</div>
                                    <div className="col-span-2 text-white font-semibold">
                                        {objective === 'cold_outreach' ? 'Cold Outbound' : 'Inbound Follow-up'}
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="text-gray-500 text-sm font-medium">Target Audience</div>
                                    <div className="col-span-2 text-white text-sm leading-relaxed">{audience}</div>
                                </div>
                            </div>

                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex items-center gap-3 mt-6">
                                <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                                <span className="text-yellow-500 text-sm">
                                    In Sandbox mode, Visoora will generate drafts in the Approval Cockpit but will <strong>not</strong> send live emails.
                                </span>
                            </div>

                            <div className="flex justify-between pt-8">
                                <button onClick={handleBack} disabled={loading} className="px-6 py-3 text-gray-400 hover:text-white transition-colors flex items-center gap-2">
                                    <ArrowLeft className="w-4 h-4" /> Edit Details
                                </button>
                                <button 
                                    onClick={handleLaunch} 
                                    disabled={loading}
                                    className="px-8 py-3 bg-gradient-to-r from-[#00F0FF] to-[#10B981] text-black font-bold rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2 shadow-[0_0_20px_rgba(0,240,255,0.3)] disabled:opacity-50"
                                >
                                    {loading ? (
                                        <div className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                                    ) : (
                                        <><Rocket className="w-5 h-5" /> Deploy Mission</>
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
