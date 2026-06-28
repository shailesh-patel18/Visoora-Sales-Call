"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap, User, Mail, Lock, ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";
import { useAuthStore } from "../auth/store";

export default function SignupPage() {
  const router = useRouter();
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
        // Redirect to login after showing success state
        setTimeout(() => {
          router.push("/login");
        }, 1800);
      } else {
        setError("Registration failed. Please check credentials and try again.");
      }
    } catch (err: any) {
      setIsLoading(false);
      setError(err?.message || "Registration failed. Please try again.");
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden bg-[hsl(var(--surface-0))]">
      {/* Dynamic Glowing Ambient background blobs */}
      <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-[hsla(var(--brand-primary),0.08)] blur-[80px] pointer-events-none animate-pulse-live" style={{ animationDuration: "9s" }} />
      <div className="absolute bottom-1/4 right-1/4 w-[350px] h-[350px] rounded-full bg-[hsla(var(--brand-accent),0.06)] blur-[100px] pointer-events-none animate-pulse-live" style={{ animationDuration: "13s" }} />
      
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
            Join the Next-Gen AI Calling Ecosystem
          </p>
        </Link>

        {/* Card Panel */}
        <div className="glass rounded-2xl p-8 shadow-2xl border-[hsl(var(--border-default))] transition-all min-h-[380px] flex flex-col justify-center">
          {isSuccess ? (
            <div className="flex flex-col items-center justify-center text-center py-6 animate-pulse-live" style={{ animationDuration: "2.5s" }}>
              <div className="w-16 h-16 rounded-full bg-[hsla(var(--success),0.1)] border border-[hsla(var(--success),0.3)] flex items-center justify-center mb-4">
                <CheckCircle2 className="w-8 h-8 text-[hsl(var(--success))]" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Registration Complete!</h3>
              <p className="text-[14px] text-[hsl(var(--text-secondary))] max-w-[280px]">
                Welcome aboard. Redirecting you to sign in with your new credentials...
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-xl font-semibold text-[white]">
                  Create an account
                </h2>
                <Link
                  href="/login"
                  className="flex items-center gap-1 text-[12px] font-semibold text-[hsl(var(--text-secondary))] hover:text-white"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to login</span>
                </Link>
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
                {/* Full Name */}
                <div>
                  <label className="block text-[12.5px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[hsl(var(--text-muted))]">
                      <User className="w-4 h-4" />
                    </span>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="John Doe"
                      className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                    />
                  </div>
                </div>

                {/* Email Address */}
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
                      placeholder="john@company.com"
                      className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                    />
                  </div>
                </div>

                {/* Password Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[12.5px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                      Password
                    </label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[hsl(var(--text-muted))]">
                        <Lock className="w-4 h-4" />
                      </span>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••"
                        className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[12.5px] font-semibold text-[hsl(var(--text-secondary))] mb-1.5">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[hsl(var(--text-muted))]">
                        <Lock className="w-4 h-4" />
                      </span>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••"
                        className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-lg py-2.5 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))]"
                      />
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full relative flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-semibold text-[14px] text-white overflow-hidden shadow-lg transition-transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                  style={{
                    background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
                  }}
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <span>Create Account</span>
                  )}
                </button>
              </form>
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
  );
}
