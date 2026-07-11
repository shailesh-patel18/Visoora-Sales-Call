"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, Menu, X, ArrowRight } from "lucide-react";

export function PublicNavbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    // Hydration-safe check for authentication status
    setIsLoggedIn(document.cookie.includes("visoora_logged_in=true"));
  }, []);

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        <div className="bg-zinc-950/60 backdrop-blur-xl border border-white/10 rounded-2xl px-6 py-4 flex items-center justify-between shadow-2xl relative">
          {/* Logo Brand */}
          <Link href="/" className="flex items-center gap-2 group">
            <div 
              className="flex items-center justify-center w-9 h-9 rounded-xl transition-transform duration-300 group-hover:scale-105"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
            >
              <Zap className="w-5 h-5 text-white animate-pulse-live" />
            </div>
            <span className="font-extrabold text-[20px] tracking-tight text-white bg-clip-text bg-gradient-to-r from-white via-zinc-200 to-zinc-400">
              Visoora
            </span>
          </Link>

          {/* Navigation Links - Desktop */}
          <div className="hidden md:flex items-center gap-8">
            <Link 
              href="/" 
              className={`text-sm font-medium transition-colors hover:text-white ${
                isActive("/") ? "text-white font-semibold" : "text-[hsl(var(--text-secondary))]"
              }`}
            >
              Platform
            </Link>
            <Link 
              href="/about" 
              className={`text-sm font-medium transition-colors hover:text-white ${
                isActive("/about") ? "text-white font-semibold" : "text-[hsl(var(--text-secondary))]"
              }`}
            >
              About
            </Link>
            <Link 
              href="/contact" 
              className={`text-sm font-medium transition-colors hover:text-white ${
                isActive("/contact") ? "text-white font-semibold" : "text-[hsl(var(--text-secondary))]"
              }`}
            >
              Book Demo
            </Link>
            <Link 
              href="/blog" 
              className={`text-sm font-medium transition-colors hover:text-white ${
                pathname?.startsWith("/blog") ? "text-white font-semibold" : "text-[hsl(var(--text-secondary))]"
              }`}
            >
              Blog
            </Link>
          </div>

          {/* Action CTAs - Desktop */}
          <div className="hidden md:flex items-center gap-4">
            {isLoggedIn ? (
              <Link 
                href="/dashboard" 
                className="text-sm font-medium text-white px-4 py-2 rounded-xl hover:bg-white/5 border border-zinc-800 transition-all duration-200 flex items-center gap-1.5"
              >
                Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link 
                  href="/login" 
                  className="text-sm font-medium text-[hsl(var(--text-secondary))] hover:text-white px-3 py-2 transition-colors"
                >
                  Log In
                </Link>
                <Link 
                  href="/contact" 
                  className="text-sm font-semibold text-white px-5 py-2.5 rounded-xl transition-all duration-300 shadow-lg relative overflow-hidden group hover:scale-[1.02] active:scale-[0.98]"
                  style={{
                    background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                  }}
                >
                  <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  Book a Demo
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="flex md:hidden">
            <button 
              onClick={() => setIsOpen(!isOpen)}
              className="p-1.5 text-[hsl(var(--text-secondary))] hover:text-white rounded-lg hover:bg-white/5"
              aria-label="Toggle menu"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 mx-4 mt-2 p-6 bg-zinc-950 rounded-2xl shadow-2xl flex flex-col gap-5 border border-zinc-800/80 animate-in fade-in slide-in-from-top-4 duration-200">
          <Link 
            href="/" 
            onClick={() => setIsOpen(false)}
            className={`text-base font-semibold py-1.5 border-b border-zinc-900 ${
              isActive("/") ? "text-white" : "text-[hsl(var(--text-secondary))]"
            }`}
          >
            Platform
          </Link>
          <Link 
            href="/about" 
            onClick={() => setIsOpen(false)}
            className={`text-base font-semibold py-1.5 border-b border-zinc-900 ${
              isActive("/about") ? "text-white" : "text-[hsl(var(--text-secondary))]"
            }`}
          >
            About
          </Link>
          <Link 
            href="/contact" 
            onClick={() => setIsOpen(false)}
            className={`text-base font-semibold py-1.5 border-b border-zinc-900 ${
              isActive("/contact") ? "text-white" : "text-[hsl(var(--text-secondary))]"
            }`}
          >
            Book Demo
          </Link>
          <Link 
            href="/blog" 
            onClick={() => setIsOpen(false)}
            className={`text-base font-semibold py-1.5 border-b border-zinc-900 ${
              pathname?.startsWith("/blog") ? "text-white" : "text-[hsl(var(--text-secondary))]"
            }`}
          >
            Blog
          </Link>
          
          <div className="flex flex-col gap-3 mt-2">
            {isLoggedIn ? (
              <Link 
                href="/dashboard"
                onClick={() => setIsOpen(false)}
                className="w-full text-center font-bold text-white px-5 py-3 rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-850 flex items-center justify-center gap-2"
              >
                Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link 
                  href="/login"
                  onClick={() => setIsOpen(false)}
                  className="w-full text-center font-semibold text-[hsl(var(--text-secondary))] hover:text-white py-2"
                >
                  Log In
                </Link>
                <Link 
                  href="/contact"
                  onClick={() => setIsOpen(false)}
                  className="w-full text-center font-bold text-white px-5 py-3 rounded-xl text-sm"
                  style={{
                    background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                  }}
                >
                  Book a Demo
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
