"use client";

import { create } from "zustand";
import { BACKEND_URL } from "../config";

interface User {
  id?: string;
  email: string;
  name: string;
  role: string;
  tenant_id: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  signup: (name: string, email: string, password?: string) => Promise<boolean>;
}

// Client-side cookie management helpers
export function setCookie(name: string, value: string, days = 7) {
  if (typeof document === "undefined") return;
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${encodeURIComponent(value)};path=/;expires=${expires.toUTCString()};SameSite=Lax;Secure=${process.env.NODE_ENV === "production" ? "true" : "false"}`;
}

export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const nameEQ = name + "=";
  const ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i].trim();
    if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length));
  }
  return null;
}

export function eraseCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT;SameSite=Lax`;
}

// Helper to fetch authorization header
export function getAuthHeaders(): Record<string, string> {
  const token = getCookie("visoora_session_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const useAuthStore = create<AuthState>((set) => {
  const isServer = typeof window === "undefined";
  const loggedIn = !isServer && getCookie("visoora_logged_in") === "true";
  let initialUser: User | null = null;

  if (loggedIn && !isServer) {
    try {
      const stored = localStorage.getItem("visoora_user");
      if (stored) {
        initialUser = JSON.parse(stored);
      }
    } catch {
      // Fallback
    }
  }

  return {
    isAuthenticated: loggedIn,
    user: initialUser,

    login: async (email, password) => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password: password || "" }),
        });

        if (!response.ok) {
          return false;
        }

        const data = await response.json();
        if (data.access_token) {
          const u: User = {
            id: data.user.id,
            email: data.user.email,
            name: data.user.name || data.user.email.split("@")[0].toUpperCase(),
            role: data.user.role,
            tenant_id: data.user.tenant_id,
          };

          setCookie("visoora_logged_in", "true", 7);
          setCookie("visoora_session_token", data.access_token, 7);
          localStorage.setItem("visoora_user", JSON.stringify(u));
          set({ isAuthenticated: true, user: u });
          return true;
        }
        return false;
      } catch (err) {
        console.error("AuthStore login error:", err);
        return false;
      }
    },

    logout: async () => {
      try {
        const headers = getAuthHeaders();
        await fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
          method: "POST",
          headers,
        });
      } catch (err) {
        console.error("AuthStore logout error:", err);
      } finally {
        eraseCookie("visoora_logged_in");
        eraseCookie("visoora_session_token");
        if (typeof window !== "undefined") {
          localStorage.removeItem("visoora_user");
        }
        set({ isAuthenticated: false, user: null });
      }
    },

    signup: async (name, email, password) => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password: password || "Visoora@2024",
            full_name: name,
            role: "admin",
          }),
        });

        if (!response.ok) {
          return false;
        }

        const data = await response.json();
        return data.success === true;
      } catch (err) {
        console.error("AuthStore signup error:", err);
        return false;
      }
    },
  };
});
