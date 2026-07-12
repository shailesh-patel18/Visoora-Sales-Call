"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  User,
  Mail,
  Lock,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Brain,
  Globe,
  Search,
  Target,
  Sparkles,
} from "lucide-react";
import { useAuthStore } from "../auth/store";

function SignupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reportId = searchParams.get("report_id");
  const signup = useAuthStore((s) => s.signup);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name || !email || !password || !confirmPassword) {
      setError("Please fill out all fields.");
      return;
    }
    if (!email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);

    try {
      // Simulate premium micro-animation delay
      await new Promise((resolve) => setTimeout(resolve, 500));
      const success = await signup(name, email, password);
      setIsLoading(false);
      if (success) {
        setIsSuccess(true);
        // Redirect to onboarding after showing success state
        setTimeout(() => {
          if (reportId) {
            router.push(`/onboarding?report_id=${reportId}`);
          } else {
            router.push("/onboarding");
          }
        }, 1800);
      } else {
        setError(
          "Registration failed. Please check credentials and try again."
        );
      }
    } catch (err: any) {
      setIsLoading(false);
      setError(err?.message || "Registration failed. Please try again.");
    }
  };

  const steps = [
    {
      icon: Globe,
      label: "Enter your website",
      desc: "We'll analyze it automatically",
    },
    {
      icon: Brain,
      label: "AI builds your Business Brain",
      desc: "Products, customers, competitors",
    },
    {
      icon: Search,
      label: "Import your prospects",
      desc: "AI researches each company",
    },
    {
      icon: Target,
      label: "Get scored, qualified leads",
      desc: "With full explainable reasoning",
    },
  ];

  return (
    <div className="relative min-h-screen flex overflow-hidden bg-[hsl(var(--surface-0))]">
      {/* ====== LEFT PANEL — Brand Story (hidden on mobile) ====== */}
      <div className="hidden lg:flex lg:w-[52%] relative flex-col justify-between p-12 xl:p-16 overflow-hidden">
        {/* Background Gradient */}
        <div
          className="absolute inset-0 animate-gradient"
          style={{
            background:
              "linear-gradient(135deg, hsla(var(--brand-accent), 0.06) 0%, hsla(var(--surface-0), 1) 40%, hsla(var(--brand-primary), 0.06) 100%)",
          }}
        />
        {/* Decorative Orbs */}
        <div className="absolute top-1/3 right-1/4 w-[280px] h-[280px] rounded-full bg-[hsla(var(--brand-accent),0.07)] blur-[90px] pointer-events-none animate-float-slow" />
        <div className="absolute bottom-1/4 left-1/3 w-[220px] h-[220px] rounded-full bg-[hsla(var(--brand-primary),0.06)] blur-[80px] pointer-events-none animate-float-delayed" />

        {/* Content */}
        <div className="relative z-10">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 mb-16 group">
            <div
              className="flex items-center justify-center w-9 h-9 rounded-xl transition-transform group-hover:scale-105"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            >
              <Zap className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="font-extrabold text-[20px] tracking-tight text-white">
              Visoora
            </span>
          </Link>

          <h2 className="text-3xl xl:text-4xl font-extrabold tracking-tight text-white leading-tight mb-4">
            Start growing
            <br />
            <span className="text-gradient">smarter today</span>
          </h2>
          <p className="text-base text-[hsl(var(--text-secondary))] max-w-md leading-relaxed mb-12">
            Set up your AI Growth Strategist in 4 simple steps. No credit card
            required. Start seeing results in minutes.
          </p>

          {/* Steps */}
          <div className="flex flex-col gap-5">
            {steps.map((step, i) => (
              <div key={step.label} className="flex gap-4 items-start">
                <div className="relative">
                  <div className="w-10 h-10 rounded-xl bg-[hsla(var(--brand-primary),0.1)] border border-[hsla(var(--brand-primary),0.15)] flex items-center justify-center flex-shrink-0">
                    <step.icon className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
                  </div>
                  {i < steps.length - 1 && (
                    <div className="absolute top-10 left-1/2 -translate-x-px h-5 w-px bg-zinc-800" />
                  )}
                </div>
                <div className="pt-1">
                  <h4 className="text-sm font-semibold text-white mb-0.5">
                    {step.label}
                  </h4>
                  <p className="text-[12px] text-[hsl(var(--text-muted))] leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom */}
        <div className="relative z-10 flex items-center gap-2 mt-8">
          <Sparkles className="w-3.5 h-3.5 text-[hsl(var(--brand-primary))]" />
          <p className="text-[11px] text-[hsl(var(--text-muted))]">
            Free to start · No credit card · Cancel anytime
          </p>
        </div>
      </div>

      {/* ====== RIGHT PANEL — Signup Form ====== */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-8 lg:p-12">
        {/* Grid Pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.015] pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle, hsl(var(--text-secondary)) 1px, transparent 1px)`,
            backgroundSize: "24px 24px",
          }}
        />

        <div className="w-full max-w-[420px] z-10">
          {/* Mobile Logo */}
          <Link
            href="/"
            className="flex lg:hidden flex-col items-center mb-8 text-center group"
          >
            <div
              className="flex items-center justify-center w-11 h-11 rounded-xl mb-3 shadow-lg transition-transform group-hover:scale-105"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            >
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold text-xl tracking-tight text-white">
              Visoora
            </span>
          </Link>

          {/* Card Panel */}
          <div className="min-h-[420px] flex flex-col justify-center">
            {isSuccess ? (
              <div className="flex flex-col items-center justify-center text-center py-8">
                <div className="w-16 h-16 rounded-full bg-[hsla(var(--success),0.1)] border border-[hsla(var(--success),0.3)] flex items-center justify-center mb-5 animate-scale-pulse">
                  <CheckCircle2 className="w-8 h-8 text-[hsl(var(--success))]" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">
                  Welcome to Visoora!
                </h3>
                <p className="text-[14px] text-[hsl(var(--text-secondary))] max-w-[280px]">
                  Your account is ready. Redirecting you to sign in...
                </p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h1 className="text-2xl font-bold text-white mb-1">
                      Create your account
                    </h1>
                    <p className="text-[13px] text-[hsl(var(--text-secondary))]">
                      Start your free AI Growth Strategist
                    </p>
                  </div>
                  <Link
                    href="/login"
                    className="flex items-center gap-1 text-[11px] font-medium text-[hsl(var(--text-muted))] hover:text-white transition-colors"
                  >
                    <ArrowLeft className="w-3 h-3" />
                    <span>Login</span>
                  </Link>
                </div>

                {error && (
                  <div
                    className="flex items-center gap-2.5 rounded-xl p-3 text-[13px] border mb-5"
                    style={{
                      background: "hsla(var(--danger), 0.05)",
                      borderColor: "hsla(var(--danger), 0.2)",
                      color: "hsl(var(--danger))",
                    }}
                  >
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Full Name */}
                  <div>
                    <label className="block text-[12px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                      Full Name
                    </label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[hsl(var(--text-muted))]">
                        <User className="w-4 h-4" />
                      </span>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="John Doe"
                        className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                      />
                    </div>
                  </div>

                  {/* Email Address */}
                  <div>
                    <label className="block text-[12px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                      Work Email
                    </label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[hsl(var(--text-muted))]">
                        <Mail className="w-4 h-4" />
                      </span>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="john@company.com"
                        className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                      />
                    </div>
                  </div>

                  {/* Password Fields */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[12px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                        Password
                      </label>
                      <div className="relative">
                        <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[hsl(var(--text-muted))]">
                          <Lock className="w-4 h-4" />
                        </span>
                        <input
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••"
                          className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[12px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                        Confirm
                      </label>
                      <div className="relative">
                        <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[hsl(var(--text-muted))]">
                          <Lock className="w-4 h-4" />
                        </span>
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="••••••"
                          className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full relative flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-[14px] text-white overflow-hidden shadow-lg transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_4px_20px_hsla(var(--brand-primary),0.3)] mt-2"
                    style={{
                      background:
                        "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
                    }}
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <span>Create Account</span>
                    )}
                  </button>
                </form>

                {/* Terms */}
                <p className="text-[11px] text-[hsl(var(--text-muted))] text-center mt-4 leading-relaxed">
                  By creating an account, you agree to our{" "}
                  <Link href="/about" className="text-[hsl(var(--text-secondary))] hover:underline">
                    Terms
                  </Link>{" "}
                  and{" "}
                  <Link href="/about" className="text-[hsl(var(--text-secondary))] hover:underline">
                    Privacy Policy
                  </Link>
                </p>
              </>
            )}
          </div>

          {/* Redirect Footer */}
          {!isSuccess && (
            <p className="text-center text-[13px] text-[hsl(var(--text-secondary))] mt-6 font-medium">
              Already have an account?{" "}
              <Link
                href="/login"
                className="text-[hsl(var(--brand-primary))] font-semibold hover:underline"
              >
                Sign in
              </Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black flex items-center justify-center text-white">Loading...</div>}>
      <SignupContent />
    </Suspense>
  );
}
