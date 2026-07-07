"use client";

import React from "react";
import Link from "next/link";
import { Zap, Github } from "lucide-react";

export function PublicFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-zinc-900 bg-zinc-950/40 relative z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10">
          
          {/* Logo & Description */}
          <div className="col-span-2 flex flex-col gap-4">
            <Link href="/" className="flex items-center gap-2 group w-max">
              <div 
                className="flex items-center justify-center w-8 h-8 rounded-lg"
                style={{
                  background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                }}
              >
                <Zap className="w-4.5 h-4.5 text-white" />
              </div>
              <span className="font-extrabold text-[18px] tracking-tight text-white">
                Visoora
              </span>
            </Link>
            <p className="text-sm text-[hsl(var(--text-secondary))] max-w-sm leading-relaxed">
              An AI Revenue Operating System that researches prospects, drafts personalized outreach, and executes sales missions to build predictable pipeline.
            </p>
            {/* Status Dot */}
            <div className="flex items-center gap-2 mt-2 w-max px-3 py-1.5 rounded-full border border-emerald-950 bg-emerald-950/20 text-emerald-400 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-live" />
              All systems operational
            </div>
          </div>

          {/* Product Links */}
          <div className="flex flex-col gap-4">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Product</h4>
            <div className="flex flex-col gap-2.5">
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">Business Brain Builder</span>
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">AI Research Engine</span>
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">ICP Match Scoring</span>
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">Autonomous Email Outreach</span>
            </div>
          </div>

          {/* Compliance & Security Links */}
          <div className="flex flex-col gap-4">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Security & Trust</h4>
            <div className="flex flex-col gap-2.5">
              <Link href="/about#technology" className="text-sm text-[hsl(var(--text-secondary))] hover:text-white transition-colors">Telephony Stack</Link>
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">Security Roadmap</span>
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">TCPA Windows Gate</span>
              <span className="text-sm text-[hsl(var(--text-secondary))] hover:text-white cursor-pointer transition-colors">Data Isolation Policy</span>
            </div>
          </div>

          {/* Company Links */}
          <div className="flex flex-col gap-4">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Company</h4>
            <div className="flex flex-col gap-2.5">
              <Link href="/about" className="text-sm text-[hsl(var(--text-secondary))] hover:text-white transition-colors">About Us</Link>
              <Link href="/blog" className="text-sm text-[hsl(var(--text-secondary))] hover:text-white transition-colors">Resources</Link>
              <Link href="/contact" className="text-sm text-[hsl(var(--text-secondary))] hover:text-white transition-colors">Book a Demo</Link>
              <Link href="/login" className="text-sm text-[hsl(var(--text-secondary))] hover:text-white transition-colors">Log In</Link>
            </div>
          </div>

        </div>

        <div className="border-t border-zinc-900/60 mt-16 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-[hsl(var(--text-muted))]">
            &copy; {currentYear} Visoora. All rights reserved. Outbound calls are subject to local area code regulations.
          </p>
          <div className="flex items-center gap-6">
            <Link 
              href="https://github.com/shailesh-patel18/Visoora-Sales-Call" 
              target="_blank" 
              className="text-[hsl(var(--text-muted))] hover:text-white transition-colors"
              aria-label="GitHub Repository"
            >
              <Github className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
