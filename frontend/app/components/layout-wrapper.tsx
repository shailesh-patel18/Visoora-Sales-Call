"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { useCRMStore } from "../store";
import { Menu, Zap } from "lucide-react";

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { mobileSidebarOpen, setMobileSidebarOpen } = useCRMStore();
  
  const authRoutes = ["/login", "/signup", "/forgotpass", "/resetpass"];
  const isAuthRoute = authRoutes.includes(pathname || "");
  const isOnboardingRoute = pathname === "/onboarding" || pathname?.startsWith("/onboarding/");
  
  const publicRoutes = ["/", "/about", "/contact"];
  const isPublicRoute = publicRoutes.includes(pathname || "") || pathname?.startsWith("/blog");

  // For authentication phases, onboarding, and public routes, bypass the sidebar layout structure
  if (isAuthRoute || isOnboardingRoute || isPublicRoute) {
    return (
      <main className="min-h-screen w-full overflow-y-auto bg-[hsl(var(--surface-0))]">
        {children}
      </main>
    );
  }

  // Dashboard layout configuration
  return (
    <div className="flex h-screen overflow-hidden bg-[hsl(var(--surface-0))] relative">
      {/* Mobile Sidebar Backdrop Overlay */}
      {mobileSidebarOpen && (
        <div 
          onClick={() => setMobileSidebarOpen(false)}
          className="fixed inset-0 bg-black/60 z-40 md:hidden transition-opacity duration-300"
        />
      )}

      {/* Renders the Sidebar */}
      <Sidebar />

      {/* Main Container Wrapper */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Mobile Header Bar */}
        <header 
          className="flex md:hidden items-center justify-between px-4 py-3 border-b flex-shrink-0"
          style={{ 
            background: "hsl(var(--surface-1))", 
            borderColor: "hsl(var(--border-subtle))" 
          }}
        >
          <button 
            onClick={() => setMobileSidebarOpen(true)}
            className="p-1.5 -ml-1.5 text-[hsl(var(--text-secondary))] hover:text-white rounded-lg hover:bg-white/5 active:bg-white/10"
            aria-label="Open sidebar"
          >
            <Menu className="w-5.5 h-5.5" />
          </button>
          
          <div className="flex items-center gap-2">
            <div 
              className="flex items-center justify-center w-7 h-7 rounded-lg"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
            >
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold text-[14px] tracking-tight text-white">Visoora</span>
          </div>

          <div 
            className="w-7 h-7 rounded-full flex items-center justify-center text-[10.5px] font-bold text-white uppercase shadow-inner"
            style={{
              background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
            }}
          >
            A
          </div>
        </header>

        {/* Scrollable Main content view */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
