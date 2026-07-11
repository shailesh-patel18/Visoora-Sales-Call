"use client";
import React, { useState, useEffect } from "react";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";
import { motion } from "framer-motion";
import { AITimelineFeed } from "../components/AITimelineFeed";
import { WorkspaceHealth } from "../components/WorkspaceHealth";
import { DashboardChatbot } from "../components/DashboardChatbot";
import Link from "next/link";

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
            } else {
                console.warn("Backend returned error, falling back to local demo state.");
            }
        } catch (err) {
            console.warn("Backend fetch failed, falling back to local demo state.", err);
        } finally {
            // Always transition after animation completes so the UI doesn't get permanently stuck
            setTimeout(() => {
                setMissionState(prev => prev === "LAUNCHING" ? "RUNNING" : prev);
            }, 5000);
        }
    };

    return (
        <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-[#111] p-6 rounded-2xl border border-[hsl(var(--border-subtle))] shadow-lg relative overflow-hidden">
                    <div className="text-gray-400 font-medium tracking-wide uppercase text-xs mb-4">Pipeline Generated</div>
                    <div className="text-3xl font-bold text-white">${revenueData.pipeline_value.toLocaleString()}</div>
                </div>
                <div className="bg-[#111] p-6 rounded-2xl border border-[hsl(var(--border-subtle))] shadow-lg relative overflow-hidden">
                    <div className="text-gray-400 font-medium tracking-wide uppercase text-xs mb-4">Meetings Booked</div>
                    <div className="text-3xl font-bold text-[#10B981]">0</div>
                </div>
                <div className="bg-[#111] p-6 rounded-2xl border border-[hsl(var(--border-subtle))] shadow-lg relative overflow-hidden">
                    <div className="text-gray-400 font-medium tracking-wide uppercase text-xs mb-4">Active Missions</div>
                    <div className="text-3xl font-bold text-white">{revenueData.active_missions_count || (missionState === 'RUNNING' ? 1 : 0)}</div>
                </div>
                <div className="bg-[#111] p-6 rounded-2xl border border-[hsl(var(--border-subtle))] shadow-lg relative overflow-hidden">
                    <div className="text-gray-400 font-medium tracking-wide uppercase text-xs mb-4">Leads Researched</div>
                    <div className="text-3xl font-bold text-white">{revenueData.leads_researched_count}</div>
                </div>
            </div>

            {/* Pending Approvals Banner */}
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                    
                    {/* Mission Health / Active Mission */}
                    {missionState === "READY_TO_LAUNCH" ? (
                        <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-white">Recommended Mission</h2>
                                <span className="text-xs font-bold uppercase tracking-wider text-[#00F0FF] bg-[#00F0FF]/10 px-3 py-1 rounded-full">Ready</span>
                            </div>
                            <p className="text-gray-400 mb-4 text-sm leading-relaxed">You have no active prospects. Upload a CSV of leads for Visoora to research, score against your ICP, and begin outreach.</p>
                            
                            <div className="bg-[#222] border border-[#333] p-4 rounded-xl flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                                    </div>
                                    <div>
                                        <h4 className="text-white font-semibold text-sm">Execution Engine</h4>
                                        <p className="text-xs text-gray-400">Visoora does not buy leads. You provide the data.</p>
                                    </div>
                                </div>
                            </div>
                            
                            <Link href="/contacts" className="w-full py-3 bg-white/5 border border-white/10 text-white font-bold rounded-xl hover:bg-white/10 transition-colors flex items-center justify-center">
                                Upload Prospects
                            </Link>
                        </div>
                    ) : (
                        <div className="bg-[#111] border border-[#00F0FF]/30 rounded-2xl p-6 relative overflow-hidden shadow-[0_0_40px_rgba(0,240,255,0.1)]">
                            <div className="absolute top-0 left-0 w-1 h-full bg-[#00F0FF] animate-pulse"></div>
                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="relative flex h-2 w-2">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00F0FF]"></span>
                                        </span>
                                        <span className="text-[#00F0FF] font-bold tracking-wider uppercase text-xs">Mission Active</span>
                                    </div>
                                    <h2 className="text-xl font-bold text-white">Find Healthcare Prospects</h2>
                                </div>
                                <div className="w-full md:w-auto bg-black/50 border border-white/10 rounded-xl p-4 min-w-[250px]">
                                    <div className="flex justify-between text-xs mb-2">
                                        <span className="text-white">Progress</span>
                                        <span className="text-[#00F0FF]">{missionProgress.pct}%</span>
                                    </div>
                                    <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                                        <motion.div initial={{ width: "0%" }} animate={{ width: `${missionProgress.pct}%` }} className="bg-[#00F0FF] h-full rounded-full"></motion.div>
                                    </div>
                                    <p className="text-[10px] text-gray-400 mt-2 uppercase tracking-wider">{missionProgress.stage === 'PLANNING' ? 'Researching...' : 'Executing...'}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Timeline Feed */}
                    <AITimelineFeed missionId={currentMissionId} />
                </div>
                
                <div className="lg:col-span-1 space-y-8">
                    {/* Business Brain Status */}
                    <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4">Business Brain & ICP</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-400">Industry</span>
                                <span className="text-white font-medium">{brain?.icp_industries?.[0] || 'Loading...'}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-400">Status</span>
                                <span className="text-[#10B981] font-medium">Trained</span>
                            </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-6 leading-relaxed border-t border-[hsl(var(--border-subtle))] pt-4">
                            Your Ideal Customer Profile (ICP) was generated during onboarding. It lives inside your tenant's secure Vector Knowledge Base.
                            <br/><br/>
                            To review or interact with your ICP, click the Chat button in the bottom right corner to talk to the Business Brain.
                        </p>
                    </div>
                    
                    <WorkspaceHealth />
                </div>
            </div>
            
            <DashboardChatbot />
        </div>
    );
}
