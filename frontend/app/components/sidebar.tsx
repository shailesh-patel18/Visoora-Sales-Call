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
  Bot,
  BookOpen,
  FolderOpen,
  ShieldAlert,
  Target,
  Radio,
  LogOut,
  Mail,
} from "lucide-react";
import { useCRMStore } from "../store";
import { useAuthStore } from "../auth/store";
import { useRouter } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "AI Employees", icon: Bot },
  { href: "/playbooks", label: "Playbooks", icon: BookOpen },
  { href: "/knowledge", label: "Knowledge Base", icon: FolderOpen },
  { href: "/objections", label: "Objection Center", icon: ShieldAlert },
  { href: "/campaigns", label: "Campaigns", icon: Target },
  { href: "/contacts", label: "Contacts", icon: Users },
  { href: "/pipeline", label: "Pipeline", icon: Kanban },
  { href: "/calls", label: "Calls", icon: Phone },
  { href: "/settings/compliance", label: "Compliance", icon: Shield },
  { href: "/settings/email", label: "Email Accounts", icon: Mail },
  { href: "/settings/billing", label: "Billing", icon: CreditCard },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, mobileSidebarOpen, setMobileSidebarOpen } = useCRMStore();
  const { user, logout } = useAuthStore();
  const router = useRouter();

  // Automatically close mobile sidebar drawer upon page routing navigation
  React.useEffect(() => {
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
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
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

      {/* User profile & Logout */}
      <div className="p-3 border-t mt-auto" style={{ borderColor: "hsl(var(--border-subtle))" }}>
        {sidebarCollapsed ? (
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
