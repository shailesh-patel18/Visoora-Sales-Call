"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  Brain,
  Target,
  BarChart3,
  CheckCircle2,
} from "lucide-react";
import { useAuthStore } from "../auth/store";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reportId = searchParams.get("report_id");
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState("admin@visoora.com");
  const [password, setPassword] = useState("Visoora@2024");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email) {
      setError("Please enter your email address.");
      return;
    }
    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setIsLoading(true);

    try {
      // Simulate premium micro-animation delay
      await new Promise((resolve) => setTimeout(resolve, 500));
      const success = await login(email, password);
      setIsLoading(false);
      if (success) {
        if (reportId) {
          router.push(`/activation?report_id=${reportId}`);
        } else {
          router.push("/dashboard");
        }
        // Ensure Next.js refreshes page cookies
        router.refresh();
      } else {
        setError("Invalid email or password credentials.");
      }
    } catch (err: any) {
      setIsLoading(false);
      setError(err?.message || "Authentication failed. Please try again.");
    }
  };

  const benefits = [
    {
      icon: Brain,
      title: "Understands your business deeply",
      desc: "AI Business Brain builds a knowledge graph of your company before any outreach",
    },
    {
      icon: Target,
      title: "Finds qualified buyers automatically",
      desc: "Prospect research, scoring, and ranking with explainable reasoning",
    },
    {
      icon: BarChart3,
      title: "Explains every recommendation",
      desc: "Confidence scores, data sources, and transparent AI decision-making",
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
              "linear-gradient(135deg, hsla(var(--brand-primary), 0.08) 0%, hsla(var(--surface-0), 1) 40%, hsla(var(--brand-accent), 0.06) 100%)",
          }}
        />
        {/* Decorative Orbs */}
        <div className="absolute top-1/4 right-1/4 w-[300px] h-[300px] rounded-full bg-[hsla(var(--brand-primary),0.08)] blur-[100px] pointer-events-none animate-float-slow" />
        <div className="absolute bottom-1/3 left-1/4 w-[250px] h-[250px] rounded-full bg-[hsla(var(--brand-accent),0.06)] blur-[80px] pointer-events-none animate-float-delayed" />

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
            Your AI Growth
            <br />
            <span className="text-gradient">Strategist</span>
          </h2>
          <p className="text-base text-[hsl(var(--text-secondary))] max-w-md leading-relaxed mb-12">
            Visoora doesn&apos;t just automate sales — it first understands your
            business, then continuously identifies where and how you should grow.
          </p>

          {/* Benefits */}
          <div className="flex flex-col gap-6">
            {benefits.map((b) => (
              <div key={b.title} className="flex gap-4">
                <div className="w-10 h-10 rounded-xl bg-[hsla(var(--brand-primary),0.1)] border border-[hsla(var(--brand-primary),0.15)] flex items-center justify-center flex-shrink-0">
                  <b.icon className="w-5 h-5 text-[hsl(var(--brand-primary))]" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white mb-0.5">
                    {b.title}
                  </h4>
                  <p className="text-[12px] text-[hsl(var(--text-muted))] leading-relaxed">
                    {b.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Tagline */}
        <p className="relative z-10 text-[11px] text-[hsl(var(--text-muted))] mt-8">
          Trusted by growth teams at high-growth B2B companies
        </p>
      </div>

      {/* ====== RIGHT PANEL — Auth Form ====== */}
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
          {/* Mobile Logo (hidden on desktop) */}
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

          <h1 className="text-2xl font-bold text-white mb-1.5">Welcome back</h1>
          <p className="text-[14px] text-[hsl(var(--text-secondary))] mb-7">
            Sign in to continue to your growth console
          </p>

          {/* Demo Info Alert */}
          <div
            className="flex items-start gap-3 rounded-xl p-3.5 text-[12px] border mb-6"
            style={{
              background: "hsla(var(--brand-primary), 0.04)",
              borderColor: "hsla(var(--brand-primary), 0.15)",
              color: "hsl(var(--text-secondary))",
            }}
          >
            <AlertCircle className="w-4 h-4 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-white mb-0.5">
                Demo credentials pre-filled
              </p>
              <p>
                Click{" "}
                <strong className="text-white">Sign In</strong> to
                explore the dashboard instantly.
              </p>
            </div>
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
            {/* Email Input */}
            <div>
              <label className="block text-[12px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[hsl(var(--text-muted))]">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@visoora.com"
                  className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[12px] font-semibold text-[hsl(var(--text-secondary))]">
                  Password
                </label>
                <Link
                  href="/forgotpass"
                  className="text-[11px] font-medium text-[hsl(var(--brand-primary))] hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-[hsl(var(--text-muted))]">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-10 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-[hsl(var(--text-muted))] hover:text-white"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                defaultChecked
                className="w-3.5 h-3.5 rounded bg-[hsl(var(--surface-2))] border-[hsl(var(--border-default))] text-[hsl(var(--brand-primary))] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <label
                htmlFor="remember-me"
                className="ml-2 text-[12px] text-[hsl(var(--text-secondary))] cursor-pointer select-none font-medium"
              >
                Keep me signed in
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full relative flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-semibold text-[14px] text-white overflow-hidden shadow-lg transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_4px_20px_hsla(var(--brand-primary),0.3)]"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Google OAuth (future-ready) */}
          <div className="mt-5">
            <div className="flex items-center gap-3 mb-5">
              <div className="flex-1 h-px bg-zinc-800" />
              <span className="text-[11px] text-[hsl(var(--text-muted))] font-medium">
                or
              </span>
              <div className="flex-1 h-px bg-zinc-800" />
            </div>
            <button
              disabled
              className="w-full flex items-center justify-center gap-2.5 py-2.5 px-4 rounded-xl text-[13px] font-medium bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] text-[hsl(var(--text-muted))] cursor-not-allowed opacity-60 hover:opacity-70 transition-opacity"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google
              <span className="text-[10px] ml-1 text-[hsl(var(--text-muted))]">(Coming Soon)</span>
            </button>
          </div>

          {/* Footer Redirect */}
          <p className="text-center text-[13px] text-[hsl(var(--text-secondary))] mt-7 font-medium">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="text-[hsl(var(--brand-primary))] font-semibold hover:underline"
            >
              Start free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black flex items-center justify-center text-white">Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
