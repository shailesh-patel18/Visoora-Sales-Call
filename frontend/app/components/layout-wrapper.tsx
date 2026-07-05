"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { useCRMStore } from "../store";
import { Menu, Zap } from "lucide-react";

import { NotificationCenter } from "./notification-center";

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
        {/* Global Trust Top Bar (Desktop & Mobile) */}
        <div className="flex-shrink-0 border-b border-[hsl(var(--border-subtle))] bg-[#111] px-4 py-2 flex items-center justify-between z-20">
          <div className="flex items-center gap-4">
             {/* Mobile Sidebar Toggle (only visible on mobile) */}
             <button 
                onClick={() => setMobileSidebarOpen(true)}
                className="md:hidden p-1.5 -ml-1.5 text-[hsl(var(--text-secondary))] hover:text-white rounded-lg hover:bg-white/5"
              >
                <Menu className="w-5 h-5" />
              </button>
              
              {/* Environment Toggle */}
              <div className="flex items-center gap-2 bg-black border border-[hsl(var(--border-subtle))] rounded-lg p-1">
                 <button className="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 flex items-center gap-1.5 shadow-[0_0_10px_rgba(234,179,8,0.2)]">
                   <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" /> Sandbox
                 </button>
                 <button className="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider text-gray-500 hover:text-gray-300 transition-colors">
                   Production
                 </button>
              </div>
          </div>
          
          <div className="flex items-center gap-4">
             <span className="text-xs text-gray-400 hidden sm:inline-block">Safe Mode: No emails will be sent.</span>
             <NotificationCenter />
             <div 
              className="w-7 h-7 rounded-full flex items-center justify-center text-[10.5px] font-bold text-white uppercase shadow-inner"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
            >
              A
            </div>
          </div>
        </div>

        {/* Scrollable Main content view */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
