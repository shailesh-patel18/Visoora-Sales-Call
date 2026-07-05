"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Zap,
  Mail,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email) {
      setError("Please enter your email address.");
      return;
    }
    if (!email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    setIsLoading(true);

    // Simulated network latency
    setTimeout(() => {
      setIsLoading(false);
      setIsSuccess(true);
    }, 800);
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden bg-[hsl(var(--surface-0))]">
      {/* Decorative Background */}
      <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-[hsla(var(--brand-primary),0.06)] blur-[100px] pointer-events-none animate-float-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-[350px] h-[350px] rounded-full bg-[hsla(var(--brand-accent),0.05)] blur-[90px] pointer-events-none animate-float-delayed" />

      {/* Grid Pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.015] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle, hsl(var(--text-secondary)) 1px, transparent 1px)`,
          backgroundSize: "24px 24px",
        }}
      />

      <div className="w-full max-w-[420px] z-10">
        {/* Logo */}
        <Link
          href="/"
          className="flex flex-col items-center mb-8 text-center group cursor-pointer"
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

        {/* Card */}
        <div className="glass rounded-2xl p-8 shadow-2xl min-h-[280px] flex flex-col justify-center">
          {isSuccess ? (
            <div className="flex flex-col items-center justify-center text-center py-4">
              <div className="w-14 h-14 rounded-full bg-[hsla(var(--success),0.1)] border border-[hsla(var(--success),0.3)] flex items-center justify-center mb-4 animate-scale-pulse">
                <CheckCircle2 className="w-7 h-7 text-[hsl(var(--success))]" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">
                Check Your Email
              </h3>
              <p className="text-[13px] text-[hsl(var(--text-secondary))] max-w-[280px] mb-6">
                If an account exists for{" "}
                <strong className="text-white">{email}</strong>, you&apos;ll
                receive a password reset link shortly.
              </p>
              <Link
                href="/login"
                className="flex items-center gap-1.5 text-[13px] font-semibold text-[hsl(var(--brand-primary))] hover:underline"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h1 className="text-xl font-bold text-white mb-1">
                    Reset your password
                  </h1>
                  <p className="text-[13px] text-[hsl(var(--text-secondary))]">
                    Enter your email to receive a reset link
                  </p>
                </div>
                <Link
                  href="/login"
                  className="flex items-center gap-1 text-[11px] font-medium text-[hsl(var(--text-muted))] hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-3 h-3" />
                  <span>Back</span>
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
                      placeholder="john@company.com"
                      className="w-full bg-[hsl(var(--surface-2))] border border-[hsl(var(--border-default))] rounded-xl py-3 pl-10 pr-4 text-[13.5px] text-white focus:outline-none focus:border-[hsl(var(--brand-primary))] focus:ring-1 focus:ring-[hsl(var(--brand-primary))] placeholder-[hsl(var(--text-muted))] transition-all"
                    />
                  </div>
                </div>

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
                    <span>Send Reset Link</span>
                  )}
                </button>
              </form>
            </>
          )}
        </div>

        {/* Footer */}
        {!isSuccess && (
          <p className="text-center text-[13px] text-[hsl(var(--text-secondary))] mt-6 font-medium">
            Remember your password?{" "}
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
