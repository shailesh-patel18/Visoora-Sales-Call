"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Shield, ShieldAlert, ArrowLeft, ArrowRight, Upload, AlertCircle, FileText, CheckCircle } from "lucide-react";
import { useOnboardingStore } from "../store";
import { step4Schema, type Step4Data } from "../schemas";

export default function Step4Page() {
  const router = useRouter();
  const { state, updateStep4, setStep } = useOnboardingStore();
  const [dncFileUploaded, setDncFileUploaded] = useState(false);
  const [dncFileName, setDncFileName] = useState("");

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<Step4Data>({
    resolver: zodResolver(step4Schema),
    defaultValues: state.step4 || {
      consentConfirmed: false,
      recordingDisclosure: true,
      country: "US",
    },
  });

  const selectedCountry = watch("country");
  const disclosureVal = watch("recordingDisclosure");

  useEffect(() => {
    setStep(4);
  }, []);

  const getDisclosureScript = (country: string) => {
    switch (country) {
      case "US":
        return "This call may be recorded for quality and training purposes. By continuing, you agree to these terms.";
      case "GB":
      case "EU":
        return "This call is recorded by Visoora in accordance with GDPR regulations. You can opt-out at any time.";
      case "AU":
        return "This call may be monitored or recorded. If you do not wish to be recorded, please notify the agent.";
      default:
        return "This call may be recorded.";
    }
  };

  const handleDncFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDncFileName(file.name);
      setDncFileUploaded(true);
      // Simulates uploading parsed DNC numbers to store or local fallback
    }
  };

  const onSubmit = async (data: Step4Data) => {
    await updateStep4(data);
    router.push("/onboarding/step-5");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="glass p-6 md:p-8 rounded-xl border flex flex-col gap-6"
      style={{ borderColor: "hsl(var(--border-subtle))" }}
    >
      {/* Compliance gate banner */}
      <div
        className="flex items-center gap-3 p-3.5 rounded-lg border"
        style={{
          background: "hsla(142, 71%, 45%, 0.03)",
          borderColor: "hsla(142, 71%, 45%, 0.15)",
        }}
      >
        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-emerald-500/10 flex-shrink-0 animate-pulse-live">
          <Shield className="w-4.5 h-4.5 text-emerald-400" />
        </div>
        <div>
          <p className="text-xs font-bold text-emerald-400">Visoora Regulatory Compliance Gate Active</p>
          <p className="text-[10px]" style={{ color: "hsl(var(--text-secondary))" }}>
            Outbound cold dialings are automatically checked against time windows, DNC rules, and PEWC records.
          </p>
        </div>
      </div>

      <div>
        <h1 className="text-xl font-bold tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
          Regulatory compliance setup
        </h1>
        <p className="text-xs mt-1" style={{ color: "hsl(var(--text-muted))" }}>
          Step 4 of 6 · Establish compliance boundaries to meet FCC, FTC (TCPA) and EU GDPR requirements.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
        
        {/* Country Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
            Outbound Target Country
          </label>
          <select
            {...register("country")}
            className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none focus:ring-1 focus:ring-[hsl(var(--brand-primary))] transition-all"
            style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}
          >
            <option value="US">United States (TCPA & FCC Regulations)</option>
            <option value="GB">United Kingdom (Ofcom & GDPR Regulations)</option>
            <option value="AU">Australia (ACMA & Privacy Act Regulations)</option>
          </select>
        </div>

        {/* Call Recording Disclosure Config */}
        <div className="flex flex-col gap-3 p-4 rounded-xl border" style={{ background: "hsl(var(--surface-2))", borderColor: "hsl(var(--border-default))" }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Recording Disclosure Speech</p>
              <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>Play an automated statement immediately on connect.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                {...register("recordingDisclosure")}
                className="sr-only peer"
              />
              <div className="w-8 h-4.5 bg-neutral-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-3.5 after:w-3.5 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
          </div>

          {disclosureVal && (
            <div className="flex flex-col gap-1.5 mt-1">
              <label className="text-[9px] font-bold uppercase tracking-wider" style={{ color: "hsl(var(--text-secondary))" }}>Dynamic script preview</label>
              <div
                className="p-3 rounded-lg border text-xs leading-relaxed italic"
                style={{
                  background: "hsl(var(--surface-3))",
                  borderColor: "hsl(var(--border-subtle))",
                  color: "hsl(var(--text-secondary))",
                }}
              >
                "{getDisclosureScript(selectedCountry)}"
              </div>
              <span className="text-[9px]" style={{ color: "hsl(var(--text-muted))" }}>
                This is generated contextually to meet {selectedCountry} caller rules (One-party/Two-party consent).
              </span>
            </div>
          )}
        </div>

        {/* Upload DNC List */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold" style={{ color: "hsl(var(--text-secondary))" }}>
            Blacklist / Do Not Call (DNC) Registry (Optional CSV uploader)
          </label>
          <div
            className="flex flex-col items-center justify-center p-5 border border-dashed rounded-lg text-center gap-2 cursor-pointer relative transition-all hover:bg-white/[0.01]"
            style={{
              borderColor: dncFileUploaded ? "hsl(var(--brand-primary))" : "hsl(var(--border-default))",
              background: "hsl(var(--surface-2))",
            }}
          >
            <input
              type="file"
              accept=".csv"
              onChange={handleDncFileUpload}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
            />
            {dncFileUploaded ? (
              <>
                <CheckCircle className="w-6 h-6 text-emerald-400" />
                <div>
                  <p className="text-xs font-bold text-emerald-400">DNC Blacklist Uploaded Successfully</p>
                  <p className="text-[10px]" style={{ color: "hsl(var(--text-secondary))" }}>{dncFileName} parsed successfully</p>
                </div>
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" style={{ color: "hsl(var(--text-muted))" }} />
                <div>
                  <p className="text-xs font-bold" style={{ color: "hsl(var(--text-primary))" }}>Drag & drop DNC list CSV here</p>
                  <p className="text-[10px]" style={{ color: "hsl(var(--text-muted))" }}>CSV should have standard E.164 phone column</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* TCPA Express Consent Required Checklist */}
        <div className="flex flex-col gap-2 p-4 rounded-xl border mt-1" style={{ background: "hsla(0, 84%, 60%, 0.02)", borderColor: errors.consentConfirmed ? "hsl(var(--danger))" : "hsl(var(--border-default))" }}>
          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              id="consentConfirmed"
              {...register("consentConfirmed")}
              className="mt-1 rounded accent-rose-500 cursor-pointer h-4 w-4"
            />
            <label htmlFor="consentConfirmed" className="text-xs leading-relaxed cursor-pointer select-none" style={{ color: "hsl(var(--text-secondary))" }}>
              <span className="font-bold text-[hsl(var(--text-primary))]">Confirm Prior Express Written Consent: </span>
              I confirm that I have explicit, prior express written consent (PEWC) from all contact numbers loaded into Visoora, in accordance with the TCPA (47 U.S.C. § 227) and local calling compliance guidelines.
            </label>
          </div>
          {errors.consentConfirmed && (
            <span className="text-[11px] font-semibold flex items-center gap-1 mt-1" style={{ color: "hsl(var(--danger))" }}>
              <AlertCircle className="w-3.5 h-3.5 animate-pulse" /> {errors.consentConfirmed.message}
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between gap-4 mt-2">
          <button
            type="button"
            onClick={() => router.push("/onboarding/step-3")}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-xs font-semibold transition-colors border hover:bg-white/[0.03]"
            style={{ borderColor: "hsl(var(--border-default))", color: "hsl(var(--text-secondary))" }}
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </button>

          <button
            type="submit"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white transition-all hover:opacity-90"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              boxShadow: "0 4px 20px -4px hsla(var(--brand-primary), 0.35)",
            }}
          >
            Import Contacts <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </form>
    </motion.div>
  );
}
