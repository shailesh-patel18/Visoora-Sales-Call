"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  Zap, 
  CheckCircle2, 
  AlertCircle,
  Calendar,
  ShieldAlert,
  ArrowLeft,
  Loader2
} from "lucide-react";
import Link from "next/link";
import { PublicNavbar } from "../components/public-navbar";
import { PublicFooter } from "../components/public-footer";

export default function Contact() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    volume: "<10k",
    crm: "None"
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Basic domain validation (corporate email requirement)
    const emailParts = formData.email.split("@");
    if (emailParts.length < 2) {
      setError("Please input a valid email address.");
      setLoading(false);
      return;
    }

    const domain = emailParts[1].toLowerCase();
    const publicDomains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"];
    if (publicDomains.includes(domain)) {
      setError("Please use your corporate work email address.");
      setLoading(false);
      return;
    }

    // Simulate submission API call
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-[hsl(var(--surface-0))] text-white selection:bg-[hsl(var(--brand-primary))]/30 relative overflow-hidden flex flex-col justify-between">
      <div>
        <PublicNavbar />

        {/* Background decorative blur */}
        <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-[hsl(var(--brand-primary))]/5 rounded-full blur-[120px] pointer-events-none -z-10" />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-24">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            
            {/* LEFT COLUMN: TRUST BUILDER */}
            <div className="lg:col-span-5 flex flex-col gap-6 lg:sticky lg:top-32">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white via-zinc-200 to-zinc-500">
                Book a Compliant Sales Call Demo.
              </h1>
              <p className="text-base text-[hsl(var(--text-secondary))] leading-relaxed">
                Schedule a 15-minute technical walkthrough. We'll show you how to configure a sandbox calling agent, build playbooks, and run test campaigns.
              </p>

              <div className="flex flex-col gap-4 mt-4">
                <div className="flex gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-[hsl(var(--text-secondary))]">Observe G.711 $\mu$-law streaming latency live</span>
                </div>
                <div className="flex gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-[hsl(var(--text-secondary))]">Verify timezone-gated compliance behavior</span>
                </div>
                <div className="flex gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-[hsl(var(--text-secondary))]">Review bi-directional CRM integration logs</span>
                </div>
              </div>

              {/* Legal Warning Badge */}
              <div className="p-4 rounded-xl border border-zinc-900 bg-zinc-900/10 flex gap-3 text-xs text-[hsl(var(--text-secondary))] mt-2">
                <ShieldAlert className="w-5 h-5 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
                <p>
                  <strong>Compliance Note:</strong> Visoora strictly checks federal Do-Not-Call (DNC) lists. Phone numbers entered in our form are only used to trigger sandbox test calls during the live demonstration.
                </p>
              </div>
            </div>

            {/* RIGHT COLUMN: DEMO FORM */}
            <div className="lg:col-span-7">
              <div className="p-6 sm:p-10 rounded-2xl border border-zinc-800 bg-zinc-950/40 relative">
                {success ? (
                  // Success State
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-center text-center py-10 gap-5"
                  >
                    <div className="w-16 h-16 rounded-2xl bg-[hsl(var(--brand-primary))]/10 flex items-center justify-center text-[hsl(var(--brand-primary))] shadow-xl">
                      <Calendar className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-bold">Demo Requested Successfully</h2>
                    <p className="text-sm text-[hsl(var(--text-secondary))] max-w-sm leading-relaxed">
                      Thank you for scheduling. Check your inbox at <span className="text-white font-semibold">{formData.email}</span> for a calendar invite and sandbox access token.
                    </p>
                    <Link
                      href="/"
                      className="mt-4 px-6 py-2.5 rounded-xl text-xs font-bold border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-900 transition-colors flex items-center gap-1.5"
                    >
                      <ArrowLeft className="w-4 h-4" /> Return Home
                    </Link>
                  </motion.div>
                ) : (
                  // Form State
                  <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="name" className="text-xs font-bold uppercase text-[hsl(var(--text-secondary))]">
                        First & Last Name
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        required
                        value={formData.name}
                        onChange={handleInputChange}
                        placeholder="Sarah Connor"
                        className="w-full px-4 py-3 bg-zinc-900/40 rounded-xl border border-zinc-800 focus:border-[hsl(var(--brand-primary))] focus:outline-none text-sm"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="email" className="text-xs font-bold uppercase text-[hsl(var(--text-secondary))]">
                        Corporate Email Address
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        required
                        value={formData.email}
                        onChange={handleInputChange}
                        placeholder="sconnor@cyberdyne.corp"
                        className="w-full px-4 py-3 bg-zinc-900/40 rounded-xl border border-zinc-800 focus:border-[hsl(var(--brand-primary))] focus:outline-none text-sm"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex flex-col gap-1.5">
                        <label htmlFor="volume" className="text-xs font-bold uppercase text-[hsl(var(--text-secondary))]">
                          Outbound Call Volume
                        </label>
                        <select
                          id="volume"
                          name="volume"
                          value={formData.volume}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-zinc-900 rounded-xl border border-zinc-800 focus:border-[hsl(var(--brand-primary))] focus:outline-none text-sm text-white"
                        >
                          <option value="<10k">&lt; 10,000 / mo</option>
                          <option value="10k-50k">10,000 - 50,000 / mo</option>
                          <option value="50k-250k">50,000 - 250,000 / mo</option>
                          <option value="250k+">&gt; 250,000 / mo</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label htmlFor="crm" className="text-xs font-bold uppercase text-[hsl(var(--text-secondary))]">
                          Primary CRM System
                        </label>
                        <select
                          id="crm"
                          name="crm"
                          value={formData.crm}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-zinc-900 rounded-xl border border-zinc-800 focus:border-[hsl(var(--brand-primary))] focus:outline-none text-sm text-white"
                        >
                          <option value="None">None / Custom REST API</option>
                          <option value="HubSpot">HubSpot CRM</option>
                          <option value="Salesforce">Salesforce CRM</option>
                          <option value="Pipedrive">Pipedrive CRM</option>
                        </select>
                      </div>
                    </div>

                    {/* Display Error Message */}
                    {error && (
                      <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex gap-2 items-center">
                        <AlertCircle className="w-4.5 h-4.5 flex-shrink-0" />
                        <span>{error}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full py-4 rounded-xl font-bold text-white shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:scale-100 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
                      style={{
                        background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                      }}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" /> Scheduling Walkthrough...
                        </>
                      ) : (
                        "Request Telephony Demo"
                      )}
                    </button>

                    <p className="text-[10px] text-[hsl(var(--text-muted))] text-center leading-relaxed mt-2">
                      By submitting this request, you agree to receive follow-up emails and compliance scheduling notifications regarding your Visoora sandbox setup.
                    </p>
                  </form>
                )}
              </div>
            </div>

          </div>
        </main>
      </div>

      <PublicFooter />
    </div>
  );
}
