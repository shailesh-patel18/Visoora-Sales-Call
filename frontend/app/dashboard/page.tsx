"use client";
import React, { useState, useEffect } from "react";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";
import { motion } from "framer-motion";
import { AITimelineFeed } from "../components/AITimelineFeed";
import { WorkspaceHealth } from "../components/WorkspaceHealth";

export default function DashboardPage() {
    const [missionState, setMissionState] = useState("READY_TO_LAUNCH");
    const [brain, setBrain] = useState<any>(null);
    const [missionProgress, setMissionProgress] = useState({ stage: "PLANNING", pct: 10 });
    const [currentMissionId, setCurrentMissionId] = useState<string | null>(null);
    const [revenueData, setRevenueData] = useState({
        active_missions_count: 0,
        leads_researched_count: 0,
        pipeline_value: 0,
        drafts_pending_count: 0
    });

    useEffect(() => {
        async function loadRevenue() {
            try {
                const res = await fetch(`${BACKEND_URL}/api/analytics/dashboard/revenue`, {
                    headers: getAuthHeaders()
                });
                if (res.ok) {
                    const data = await res.json();
                    setRevenueData(data);
                }
            } catch (err) {
                console.error("Failed to fetch revenue data:", err);
            }
        }
        loadRevenue();
        // Poll revenue data every 10 seconds to keep dashboard fresh
        const interval = setInterval(loadRevenue, 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        async function loadBrain() {
            try {
                const res = await fetch(`${BACKEND_URL}/api/analytics/business-map`, {
                    headers: getAuthHeaders()
                });
                if (res.ok) {
                    const data = await res.json();
                    setBrain(data.agent_config);
                }
            } catch (err) {
                console.error("Failed to fetch brain data:", err);
            }
        }
        loadBrain();
    }, []);

    useEffect(() => {
        let interval: any;
        if (missionState === "LAUNCHING" || missionState === "RUNNING") {
            interval = setInterval(async () => {
                try {
                    // Make sure currentMissionId is used if available, otherwise just general status
                    const res = await fetch(`${BACKEND_URL}/api/analytics/missions/status`, {
                        headers: getAuthHeaders()
                    });
                    if (res.ok) {
                        const data = await res.json();
                        if (data && data.stage) {
                            setMissionProgress(data);
                            if (missionState === "LAUNCHING" && data.pct > 0) {
                                setMissionState("RUNNING");
                            }
                        }
                    }
                } catch (err) {
                    console.error("Failed to fetch mission status:", err);
                }
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [missionState, currentMissionId]);

    const handleLaunch = async () => {
        setMissionState("LAUNCHING");
        try {
            const res = await fetch(`${BACKEND_URL}/api/analytics/missions/launch`, {
                method: "POST",
                headers: {
                    ...getAuthHeaders(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    mission_name: "Find Healthcare Prospects",
                    goal: "Prospecting and automated email drafting based on the newly created Business Brain."
                })
            });
            if (res.ok) {
                const data = await res.json();
                setCurrentMissionId(data.mission_id);
                // In a real flow, the backend starting the task would immediately push pct > 0
                // but if we don't have a real worker connected yet, we manually advance after a few seconds
                // so the user can still see the UI during this test if the backend isn't returning data yet.
                // We'll leave a fallback just in case the backend polling doesn't return data.
                setTimeout(() => {
                    setMissionState(prev => prev === "LAUNCHING" ? "RUNNING" : prev);
                }, 5000);
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
            {missionState === "READY_TO_LAUNCH" && (
                <motion.div 
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl overflow-hidden shadow-2xl max-w-3xl mx-auto"
                >
                    <div className="p-8 border-b border-white/5 relative">
                        <div className="absolute top-4 right-4 bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-2">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-yellow-500"></span>
                            </span>
                            SANDBOX
                        </div>
                        <div className="text-[#00F0FF] text-sm font-bold tracking-widest uppercase mb-2">Recommended Mission</div>
                        <h1 className="text-3xl font-bold text-white mb-2">Find Ideal Customers</h1>
                        <p className="text-gray-400">
                            Based on your Business Brain, we found <strong className="text-white">321 companies</strong> matching your ICP.
                        </p>
                    </div>
                    <div className="p-8 bg-[#0a0a0a]">
                        <h3 className="text-lg font-semibold text-white mb-6">AI Estimate</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                            <div>
                                <label className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1 block">Expected Meetings</label>
                                <div className="text-3xl font-bold text-[#10B981]">5</div>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1 block">Expected Pipeline</label>
                                <div className="text-3xl font-bold text-white">$68,000</div>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1 block">AI Confidence</label>
                                <div className="text-3xl font-bold text-white">91%</div>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1 block">Expected Cost</label>
                                <div className="text-3xl font-bold text-white">$8.40</div>
                            </div>
                        </div>
                        <div className="text-sm text-gray-500 bg-white/5 p-4 rounded-xl border border-white/10">
                            <strong>Based on:</strong>
                            <ul className="list-disc list-inside mt-2 space-y-1">
                                <li>41 similar companies in our network</li>
                                <li>{brain?.icp_industries?.[0] || 'Software'} benchmark metrics</li>
                                <li>Previous successful campaigns matching your profile</li>
                            </ul>
                        </div>
                    </div>
                    <div className="p-8 border-t border-white/5 flex flex-col items-center">
                        <button onClick={handleLaunch} className="w-full max-w-md py-4 bg-gradient-to-r from-[hsl(var(--brand-primary))] to-[hsl(var(--brand-accent))] text-black font-bold text-lg rounded-xl hover:opacity-90 transition-opacity shadow-[0_0_30px_rgba(0,240,255,0.2)]">
                            Launch Mission
                        </button>
                        <p className="text-xs text-gray-500 mt-4">Sandbox mode: No emails will be sent. Safe to test.</p>
                    </div>
                </motion.div>
            )}

            {missionState === "LAUNCHING" && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-20 space-y-8">
                    <div className="w-24 h-24 border-4 border-[#00F0FF]/20 border-t-[#00F0FF] rounded-full animate-spin"></div>
                    <div className="h-12 flex items-center justify-center relative w-full max-w-md">
                        <motion.p initial={{ opacity: 1, y: 0 }} animate={{ opacity: 0, y: -20 }} transition={{ delay: 1 }} className="text-xl text-[#00F0FF] font-medium absolute">
                            Waking up Research Agent...
                        </motion.p>
                        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2, duration: 0.5 }} className="text-xl text-[#00F0FF] font-medium absolute">
                            Planning Agent building ICP...
                        </motion.p>
                        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2.4, duration: 0.5 }} className="text-xl text-white font-bold absolute">
                            Mission Dispatched.
                        </motion.p>
                    </div>
                </motion.div>
            )}

            {missionState === "RUNNING" && (
                <>
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-[#111] border border-[#00F0FF]/30 rounded-2xl p-8 relative overflow-hidden shadow-[0_0_40px_rgba(0,240,255,0.1)]">
                        <div className="absolute top-0 left-0 w-1 h-full bg-[#00F0FF] animate-pulse"></div>
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="relative flex h-3 w-3">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-[#00F0FF]"></span>
                                    </span>
                                    <span className="text-[#00F0FF] font-semibold tracking-wider uppercase text-sm">Live System</span>
                                </div>
                                <h1 className="text-3xl font-bold text-white mb-2">Your AI team is working.</h1>
                                <p className="text-[hsl(var(--text-secondary))]">The mission is actively running in sandbox mode.</p>
                            </div>
                            <div className="w-full md:w-auto bg-black/50 border border-white/10 rounded-xl p-4 min-w-[300px]">
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-white font-medium flex items-center gap-2">Find Ideal Customers</span>
                                    <span className="text-[#00F0FF]">{missionProgress.pct}% complete</span>
                                </div>
                                <p className="text-xs text-gray-400 mb-3">{missionProgress.stage === 'PLANNING' ? 'Research Agent is scanning companies...' : 'Drafting prospect emails...'}</p>
                                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                                    <motion.div initial={{ width: "0%" }} animate={{ width: `${missionProgress.pct}%` }} className="bg-[#00F0FF] h-2 rounded-full"></motion.div>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 space-y-8">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-[#111] p-6 rounded-2xl border border-[hsl(var(--border-subtle))] shadow-lg relative overflow-hidden">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-[hsl(var(--brand-primary))]/5 rounded-bl-full border-b border-l border-[hsl(var(--brand-primary))]/10"></div>
                                    <div className="flex justify-between items-start mb-4 relative z-10">
                                        <div className="text-gray-400 font-medium tracking-wide uppercase text-xs">Pipeline Generated</div>
                                    </div>
                                    <div className="text-4xl font-bold text-white mb-2 relative z-10">
                                        ${revenueData.pipeline_value.toLocaleString()}
                                    </div>
                                </div>
                                <div className="bg-[#111] p-6 rounded-2xl border border-[hsl(var(--border-subtle))] shadow-lg relative overflow-hidden">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-[hsl(var(--brand-primary))]/5 rounded-bl-full border-b border-l border-[hsl(var(--brand-primary))]/10"></div>
                                    <div className="flex justify-between items-start mb-4 relative z-10">
                                        <div className="text-gray-400 font-medium tracking-wide uppercase text-xs">Leads Researched</div>
                                    </div>
                                    <div className="text-4xl font-bold text-white mb-2 relative z-10">
                                        {revenueData.leads_researched_count}
                                    </div>
                                </div>
                            </div>
                            
                            {revenueData.drafts_pending_count > 0 && (
                                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                                        <span className="text-yellow-500 font-medium text-sm">
                                            {revenueData.drafts_pending_count} drafts await your approval.
                                        </span>
                                    </div>
                                    <a href="/cockpit" className="text-xs font-bold uppercase tracking-wider bg-yellow-500 text-black px-4 py-2 rounded-lg hover:opacity-90 transition-opacity">
                                        Review Drafts
                                    </a>
                                </div>
                            )}
                            
                            <AITimelineFeed missionId={currentMissionId} />
                        </div>
                        <div className="lg:col-span-1">
                            <WorkspaceHealth />
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
