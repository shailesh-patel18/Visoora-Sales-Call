"use client";

import React, { useEffect, useState } from "react";
import { Bot, Mail, Target, Phone, BrainCircuit, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

export function AITimelineFeed({ missionId }: { missionId?: string | null }) {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTimeline();
    const pollRate = missionId ? 3000 : 30000;
    const interval = setInterval(fetchTimeline, pollRate);
    return () => clearInterval(interval);
  }, [missionId]);

  const fetchTimeline = async () => {
    try {
      const endpoint = missionId 
        ? `${BACKEND_URL}/api/missions/${missionId}/events`
        : `${BACKEND_URL}/api/analytics/missions/timeline`;
        
      const res = await fetch(endpoint, {
        headers: getAuthHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.error("Timeline fetch error", err);
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (agentName: string) => {
    if (agentName.includes("Email") || agentName.includes("Outreach")) return Mail;
    if (agentName.includes("Strategy")) return BrainCircuit;
    if (agentName.includes("Research")) return Target;
    if (agentName.includes("Voice")) return Phone;
    return Bot;
  };

  return (
    <div className="bg-[#111] border border-[hsl(var(--border-subtle))] rounded-2xl p-6 shadow-lg h-full">
      <div className="flex items-center gap-2 mb-6">
        <Activity className="w-5 h-5 text-[#00F0FF]" />
        <h3 className="text-lg font-semibold text-white">Live AI Timeline</h3>
      </div>
      
      {loading && events.length === 0 ? (
        <div className="text-gray-500 text-sm">Loading events...</div>
      ) : events.length === 0 ? (
        <div className="text-gray-500 text-sm">No recent events. Launch a mission to see activity!</div>
      ) : (
        <div className="relative ml-4 space-y-0">
          {/* Vertical line through timeline */}
          <div className="absolute left-[11px] top-4 bottom-4 w-px bg-gradient-to-b from-[hsl(var(--border-subtle))] via-white/10 to-transparent"></div>
          
          {events.map((event, idx) => {
            const Icon = getIcon(event.agent);
            return (
              <motion.div 
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="relative pl-10 pb-6"
              >
                {/* Arrow connecting to next item, unless it's the last item */}
                {idx < events.length - 1 && (
                  <div className="absolute left-[8px] bottom-1 text-[hsl(var(--border-subtle))]">
                    ↓
                  </div>
                )}
                
                <div className={`absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center ${event.bg} border border-[hsl(var(--border-subtle))] bg-[#0a0a0a] z-10`}>
                  <Icon className={`w-3 h-3 ${event.color}`} />
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3">
                  <span className="text-xs font-mono text-gray-500 w-12">{event.time}</span>
                  <span className="text-sm font-semibold text-gray-200">{event.agent}</span>
                </div>
                
                <div className="mt-1">
                  <p className={`text-sm ${event.color === 'text-red-400' ? 'text-red-400 font-medium' : 'text-gray-300'}`}>
                    {event.action}
                  </p>
                  
                  {event.reason && (
                    <div className="mt-2 bg-[#111] border border-red-500/20 p-2 rounded text-xs text-gray-400">
                      <span className="text-red-400 font-semibold uppercase tracking-wider text-[10px]">Reason:</span> {event.reason}
                    </div>
                  )}
                  
                  {event.status === "Waiting Approval" && (
                    <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-yellow-400/20 text-yellow-400 border border-yellow-400/20">
                      Waiting Approval
                    </span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
