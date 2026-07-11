"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
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
  Bot,
  BookOpen,
  FolderOpen,
  ShieldAlert,
  Target,
  Radio,
  LogOut,
  Mail,
  Sparkles,
  Activity,
  BrainCircuit,
} from "lucide-react";
import { useCRMStore } from "../store";
import { useAuthStore } from "../auth/store";
import { useRouter } from "next/navigation";
import { BACKEND_URL } from "../config";
import { getAuthHeaders } from "../auth/store";

const navGroups = [
  {
    title: "AI Workspace",
    items: [
      { href: "/dashboard", label: "Command Center", icon: Activity },
      { href: "/inbox", label: "Approvals Inbox", icon: ShieldAlert, badgeKey: "inbox" },
      { href: "/business-map", label: "Business Brain", icon: BrainCircuit },
      { href: "/agents", label: "AI Employees", icon: Bot },
    ]
  },
  {
    title: "Sales Execution",
    items: [
      { href: "/campaigns", label: "Missions", icon: Target },
      { href: "/contacts", label: "Leads", icon: Users },
      { href: "/pipeline", label: "Pipeline", icon: Kanban },
    ]
  },
  {
    title: "Knowledge",
    items: [
      { href: "/playbooks", label: "Playbooks", icon: BookOpen },
      { href: "/objections", label: "Objection Matrix", icon: FolderOpen },
    ]
  },
  {
    title: "Settings",
    items: [
      { href: "/settings/email", label: "Integrations", icon: Mail },
      { href: "/settings/billing", label: "Billing", icon: CreditCard },
    ]
  }
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, mobileSidebarOpen, setMobileSidebarOpen } = useCRMStore();
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [mounted, setMounted] = React.useState(false);
  const [inboxCount, setInboxCount] = React.useState(0);

  // Poll inbox badge count every 45 seconds
  React.useEffect(() => {
    const fetchCount = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/analytics/inbox/count`, { headers: getAuthHeaders() });
        if (res.ok) { const d = await res.json(); setInboxCount(d.count ?? 0); }
      } catch { /* silent */ }
    };
    if (useAuthStore.getState().isAuthenticated) {
        fetchCount();
    }
    const interval = setInterval(() => {
        if (useAuthStore.getState().isAuthenticated) {
            fetchCount();
        }
    }, 45000);
    return () => clearInterval(interval);
  }, []);

  // Automatically close mobile sidebar drawer upon page routing navigation
  React.useEffect(() => {
    setMounted(true);
    setMobileSidebarOpen(false);
  }, [pathname, setMobileSidebarOpen]);

  const handleLogout = () => {
    logout();
    router.push("/");
    router.refresh();
  };

  if (pathname === "/onboarding" || pathname?.startsWith("/onboarding/")) {
    return null;
  }

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r transition-all duration-300 ease-in-out md:relative ${
        mobileSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      } ${
        sidebarCollapsed ? "md:w-[68px]" : "md:w-[240px]"
      } w-[240px]`}
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
          <Zap className="w-4 h-4 text-black" />
        </div>
        {!sidebarCollapsed && (
          <span className="font-bold text-[15px] tracking-tight" style={{ color: "hsl(var(--text-primary))" }}>
            Visoora AI
          </span>
        )}
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto py-4 px-2 space-y-6 custom-scrollbar">
        {navGroups.map((group, groupIndex) => (
          <div key={groupIndex} className="space-y-1">
            {!sidebarCollapsed && (
              <h4 className="px-3 text-[10px] font-bold uppercase tracking-wider text-gray-500 mb-2">
                {group.title}
              </h4>
            )}
            
            {group.items.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
              const Icon = item.icon;
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group relative
                    ${
                      isActive
                        ? "bg-white/10 text-white shadow-sm"
                        : "text-[hsl(var(--text-secondary))] hover:bg-white/5 hover:text-white"
                    }
                  `}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon
                    className={`w-4.5 h-4.5 flex-shrink-0 transition-colors ${
                      isActive ? "text-[#00F0FF]" : "text-gray-400 group-hover:text-gray-300"
                    }`}
                  />
                  {!sidebarCollapsed && (
                    <div className="flex flex-1 items-center justify-between">
                      <span className="text-[13px] font-medium leading-tight">
                        {item.label}
                      </span>
                      {(item as any).badgeKey === "inbox" && inboxCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/20">
                          {inboxCount}
                        </span>
                      )}
                      {!(item as any).badgeKey && (item as any).badge && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/20">
                          {(item as any).badge}
                        </span>
                      )}
                    </div>
                  )}
                  {/* Active Indicator Strip */}
                  {isActive && (
                    <motion.div
                      layoutId="activeNavIndicator"
                      className="absolute left-0 top-1 bottom-1 w-0.5 rounded-r-full bg-[#00F0FF]"
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* User profile & Logout */}
      <div className="p-3 border-t mt-auto" style={{ borderColor: "hsl(var(--border-subtle))" }}>
        {!mounted ? (
          <div className="flex items-center justify-center py-2 h-10">
            <div className="w-8 h-8 rounded-full bg-white/10 animate-pulse" />
          </div>
        ) : sidebarCollapsed ? (
          <div className="flex flex-col items-center gap-3 py-2">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white uppercase shadow-inner"
              style={{
                background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
              }}
              title={user?.name || "User"}
            >
              {(user?.name || "U").charAt(0)}
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md text-[hsl(var(--text-secondary))] hover:text-white hover:bg-[hsl(var(--surface-3))]"
              title="Sign Out"
            >
              <LogOut className="w-4.5 h-4.5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-3 py-1">
            <div className="flex items-center gap-2.5 min-w-0">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white uppercase flex-shrink-0 shadow-inner"
                style={{
                  background: "linear-gradient(135deg, hsl(var(--brand-primary)), hsl(var(--brand-accent)))"
                }}
              >
                {(user?.name || "U").charAt(0)}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">
                  {user?.name || "Admin User"}
                </p>
                <p className="text-xs text-[hsl(var(--text-muted))] truncate">
                  {user?.email || "admin@visoora.com"}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md text-[hsl(var(--text-secondary))] hover:text-white hover:bg-[hsl(var(--surface-3))] flex-shrink-0"
              title="Sign Out"
            >
              <LogOut className="w-4.5 h-4.5" />
            </button>
          </div>
        )}
      </div>

      {/* Collapse toggle - Desktop only */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full items-center justify-center border transition-colors hidden md:flex"
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
