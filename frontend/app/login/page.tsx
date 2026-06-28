"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap, Mail, Lock, Eye, EyeOff, AlertCircle, ArrowRight } from "lucide-react";
import { useAuthStore } from "../auth/store";

export default function LoginPage() {
  const router = useRouter();
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
        router.push("/dashboard");
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

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden bg-[hsl(var(--surface-0))]">
      {/* Dynamic Glowing Ambient background blobs */}
      <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-[hsla(var(--brand-primary),0.1)] blur-[80px] pointer-events-none animate-pulse-live" style={{ animationDuration: "8s" }} />
      <div className="absolute bottom-1/4 right-1/4 w-[350px] h-[350px] rounded-full bg-[hsla(var(--brand-accent),0.08)] blur-[100px] pointer-events-none animate-pulse-live" style={{ animationDuration: "12s" }} />
      
      {/* Grid Pattern overlay */}
      <div 
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle, hsl(var(--text-secondary)) 1px, transparent 1px)`,
          backgroundSize: "24px 24px"
        }}
      />

      <div className="w-full max-w-[440px] z-10">
        {/* Header Branding */}
        <Link href="/" className="flex flex-col items-center mb-8 text-center group cursor-pointer">
          <div
            className="flex items-center justify-center w-12 h-12 rounded-xl mb-4 shadow-lg transition-transform group-hover:scale-105"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
            }}
          >
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[white] mb-1 bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-400 group-hover:text-white transition-colors">
            Visoora
          </h1>
          <p className="text-[14px] text-[hsl(var(--text-secondary))] font-medium">
            AI Employee Call Center Operating System
          </p>
        </Link>

        {/* Form Container (Glassmorphism Card) */}
        <div className="glass rounded-2xl p-8 shadow-2xl border-[hsl(var(--border-default))] transition-all duration-300 hover:border-[hsla(var(--brand-primary),0.3)]">
          <h2 className="text-xl font-semibold text-[white] mb-5">
            Sign in to your console
          </h2>

          {/* Quick Demo Info Alert */}
          <div 
            className="flex items-start gap-3 rounded-lg p-3 text-[12.5px] border mb-6"
            style={{
              background: "hsla(var(--brand-primary), 0.04)",
              borderColor: "hsla(var(--brand-primary), 0.2)",
              color: "hsl(var(--text-secondary))"
            }}
          >
            <AlertCircle className="w-4 h-4 text-[hsl(var(--brand-primary))] flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-white mb-0.5">Demo Admin Account Pre-filled</p>
              <p>Skip signing up! Click <strong className="text-[white]">Sign In</strong> directly to test dashboard and playbooks.</p>
            </div>
          </div>

          {error && (
            <div 
              className="flex items-center gap-2.5 rounded-lg p-3 text-[13px] border mb-5"
              style={{
                background: "hsla(var(--danger), 0.05)",
                borderColor: "hsla(var(--danger), 0.2)",
                color: "hsl(var(--danger))"
              }}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Input */}
            <div>
              <label className="block text-[12.5px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[hsl(var(--text-muted))]">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@visoora.com"
                  className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[12.5px] font-semibold text-[hsl(var(--text-secondary))]">
                  Password
                </label>
                <Link
                  href="/forgotpass"
                  className="text-[12px] font-medium text-[hsl(var(--brand-primary))] hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[hsl(var(--text-muted))]">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 pl-10 pr-10 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[hsl(var(--text-muted))] hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me checkbox */}
            <div className="flex items-center mt-1">
              <input
                id="remember-me"
                type="checkbox"
                defaultChecked
                className="w-3.5 h-3.5 rounded bg-[hsl(var(--surface-2))] border-[hsl(var(--border-default))] text-[hsl(var(--brand-primary))] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <label
                htmlFor="remember-me"
                className="ml-2 text-[12.5px] text-[hsl(var(--text-secondary))] cursor-pointer select-none font-medium"
              >
                Keep me signed in
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full relative flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-semibold text-[14px] text-white overflow-hidden shadow-lg transition-transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
              }}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer Redirect */}
        <p className="text-center text-[13px] text-[hsl(var(--text-secondary))] mt-6 font-medium">
          Don't have an account?{" "}
          <Link
            href="/signup"
            className="text-[hsl(var(--brand-primary))] font-semibold hover:underline"
          >
            Create one free
          </Link>
        </p>
      </div>
    </div>
  );
}
