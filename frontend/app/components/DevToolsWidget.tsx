"use client";

import React, { useState, useEffect } from "react";
import { Wrench, X, Database, Play, Beaker } from "lucide-react";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";
import { useRouter } from "next/navigation";

export function DevToolsWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isDev, setIsDev] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV === "development") {
      setIsDev(true);
    }
  }, []);

  if (!isDev) return null;

  const handleSeed = async (profile: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/dev/seed?profile=${profile}`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        alert(`Seeded ${profile} profile successfully!`);
        router.refresh();
      } else {
        const err = await res.json();
        alert(`Seed failed: ${err.detail}`);
      }
    } catch (e) {
      alert(`Error seeding ${profile}`);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isOpen ? (
        <div className="bg-[#111] border border-white/20 rounded-xl shadow-2xl p-4 w-80 text-white font-sans animate-in slide-in-from-bottom-2 fade-in duration-200">
          <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-2">
            <h3 className="font-bold flex items-center gap-2 text-sm text-[hsl(var(--brand-primary))]">
              <Wrench className="w-4 h-4" /> Dev Tools
            </h3>
            <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Fast Setup (Seed DB)</h4>
              <div className="grid grid-cols-2 gap-2">
                <button 
                  onClick={() => handleSeed("stripe")}
                  className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-3 py-2 rounded-lg text-sm transition-colors"
                >
                  <Database className="w-3 h-3 text-indigo-400" /> Stripe
                </button>
                <button 
                  onClick={() => handleSeed("shopify")}
                  className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-3 py-2 rounded-lg text-sm transition-colors"
                >
                  <Database className="w-3 h-3 text-emerald-400" /> Shopify
                </button>
                <button 
                  onClick={() => handleSeed("hubspot")}
                  className="flex items-center gap-2 bg-white/5 hover:bg-white/10 px-3 py-2 rounded-lg text-sm transition-colors"
                >
                  <Database className="w-3 h-3 text-orange-400" /> HubSpot
                </button>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-white/10">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center justify-between">
                <span>Environment Flags</span>
              </h4>
              <p className="text-xs text-gray-400 italic">
                Set these in backend/.env:
              </p>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>DEV_MODE</span>
                  <span className="font-mono bg-white/10 px-1 rounded text-gray-300 text-xs">true</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>MOCK_AI</span>
                  <span className="font-mono bg-white/10 px-1 rounded text-gray-300 text-xs">true</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>MOCK_RESEARCH</span>
                  <span className="font-mono bg-white/10 px-1 rounded text-gray-300 text-xs">true</span>
                </div>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-white/10">
               <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Navigation</h4>
               <button 
                  onClick={() => router.push("/health")}
                  className="w-full flex items-center justify-center gap-2 bg-[hsl(var(--brand-primary))] text-black hover:bg-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <Beaker className="w-4 h-4" /> View Health Dashboard
                </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-black/50 backdrop-blur-md border border-[hsl(var(--brand-primary))] text-[hsl(var(--brand-primary))] hover:bg-[hsl(var(--brand-primary))] hover:text-black p-3 rounded-full shadow-lg shadow-[#00F0FF]/20 transition-all group"
        >
          <Wrench className="w-5 h-5 group-hover:scale-110 transition-transform" />
        </button>
      )}
    </div>
  );
}
