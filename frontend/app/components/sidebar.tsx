"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Kanban,
  Phone,
  Shield,
  ChevronLeft,
  ChevronRight,
  Zap,
  CreditCard,
} from "lucide-react";
import { useCRMStore } from "../store";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/contacts", label: "Contacts", icon: Users },
  { href: "/pipeline", label: "Pipeline", icon: Kanban },
  { href: "/calls", label: "Calls", icon: Phone },
  { href: "/settings/compliance", label: "Compliance", icon: Shield },
  { href: "/settings/billing", label: "Billing", icon: CreditCard },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useCRMStore();

  if (pathname === "/onboarding" || pathname?.startsWith("/onboarding/")) {
    return null;
  }

  return (
    <aside
      className={`relative flex flex-col border-r transition-all duration-300 ease-in-out ${
        sidebarCollapsed ? "w-[68px]" : "w-[240px]"
      }`}
      style={{
        background: "hsl(var(--surface-1))",
        borderColor: "hsl(var(--border-subtle))",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5 border-b" style={{ borderColor: "hsl(var(--border-subtle))" }}>
        <div
          className="flex items-center justify-center w-8 h-8 rounded-lg"
          style={{
            background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))",
          }}
        >
          <Zap className="w-4 h-4 text-white" />
        </div>
        {!sidebarCollapsed && (
          <span className="font-bold text-[15px] tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Visoora
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 flex flex-col gap-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all ${
                isActive
                  ? "text-white"
                  : ""
              }`}
              style={{
                color: isActive ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))",
                background: isActive ? "hsl(var(--surface-3))" : "transparent",
              }}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full flex items-center justify-center border transition-colors"
        style={{
          background: "hsl(var(--surface-2))",
          borderColor: "hsl(var(--border-default))",
          color: "hsl(var(--text-secondary))",
        }}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="w-3 h-3" />
        ) : (
          <ChevronLeft className="w-3 h-3" />
        )}
      </button>
    </aside>
  );
}
