"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Target, Search, ArrowRight, Play, CheckCircle2, Clock } from "lucide-react";
import Link from "next/link";
import { BACKEND_URL } from "../config";
import { getAuthHeaders, useAuthStore } from "../auth/store";

export default function MissionsPage() {
  const { isAuthenticated } = useAuthStore();
  const [missions, setMissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      fetchMissions();
    }
  }, [isAuthenticated]);

  const fetchMissions = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/analytics/missions`, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setMissions(data.missions || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-end border-b border-[hsl(var(--border-subtle))] pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Target className="w-8 h-8 text-[#00F0FF]" /> Missions
          </h1>
          <p className="text-[hsl(var(--text-secondary))] mt-2">
            View active and completed autonomous AI missions.
          </p>
        </div>
        <Link href="/campaigns/new" className="hidden md:flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#00F0FF] to-[#10B981] text-black font-bold rounded-xl hover:opacity-90 transition-opacity shadow-[0_0_20px_rgba(0,240,255,0.2)]">
          <Play className="w-4 h-4 fill-black" />
          Create Mission
        </Link>
      </div>

      <div className="space-y-4">
        <AnimatePresence>
          {loading ? (
             <div className="text-center py-20 text-gray-500">Loading missions...</div>
          ) : missions.length === 0 ? (
             <motion.div 
               initial={{ opacity: 0 }} animate={{ opacity: 1 }}
               className="text-center py-20 bg-[#111] rounded-2xl border border-[hsl(var(--border-subtle))]"
             >
                <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/10">
                  <Target className="w-8 h-8 text-gray-500" />
                </div>
                <h3 className="text-xl font-semibold text-white">No Missions Yet</h3>
                <p className="text-gray-400 mt-2">Create your first custom AI mission to start researching prospects.</p>
                <div className="flex gap-4 justify-center mt-6">
                    <Link href="/campaigns/new" className="inline-block px-6 py-2 bg-[#00F0FF] text-black font-bold rounded-lg hover:bg-white transition-colors">
                      Create Mission
                    </Link>
                    <Link href="/dashboard" className="inline-block px-6 py-2 bg-white/10 text-white font-semibold rounded-lg hover:bg-white/20 transition-colors">
                      Go to Command Center
                    </Link>
                </div>
             </motion.div>
          ) : (
            missions.map((mission) => (
              <motion.div 
                key={mission.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-xl p-6 hover:border-white/20 transition-colors flex items-center justify-between group cursor-pointer relative"
              >
                <Link href={`/campaigns/${mission.id}`} className="absolute inset-0 z-10"></Link>
                <div className="flex items-center gap-4">
                   <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      mission.status === "COMPLETED" ? "bg-[#10B981]/20" : "bg-[#00F0FF]/20"
                   }`}>
                      {mission.status === "COMPLETED" ? <CheckCircle2 className="w-5 h-5 text-[#10B981]" /> : <Clock className="w-5 h-5 text-[#00F0FF]" />}
                   </div>
                   <div>
                      <h3 className="text-lg font-bold text-white">{mission.name}</h3>
                      <p className="text-sm text-gray-500 flex items-center gap-2">
                         <span className="uppercase tracking-wider font-semibold text-xs">{mission.status}</span>
                         <span>•</span>
                         <span>Started {new Date(mission.created_at).toLocaleDateString()}</span>
                      </p>
                   </div>
                </div>
                
                <div className="flex items-center gap-4 z-20">
                   <Link href={`/campaigns/${mission.id}`} className="text-[#00F0FF] text-sm font-semibold hover:underline flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      View Details <ArrowRight className="w-4 h-4" />
                   </Link>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
