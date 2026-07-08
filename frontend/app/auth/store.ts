"use client";

import { create } from "zustand";
import { createClient } from "../../utils/supabase/client";

interface User {
  id?: string;
  email: string;
  name: string;
  role: string;
  tenant_id: string;
}

export const getAuthHeaders = (): Record<string, string> => {
  let token = "";
  if (typeof window !== "undefined") {
    const key = Object.keys(localStorage).find(k => k.startsWith("sb-") && k.endsWith("-auth-token"));
    if (key) {
      try {
        const session = JSON.parse(localStorage.getItem(key) || "{}");
        token = session.access_token || "";
      } catch (e) {}
    }
  }
  return token ? { Authorization: `Bearer ${token}` } : {};
};

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  signup: (name: string, email: string, password?: string) => Promise<boolean>;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,

  checkSession: async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.user) {
      const u: User = {
        id: session.user.id,
        email: session.user.email || "",
        name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0].toUpperCase() || "User",
        role: session.user.user_metadata?.role || "admin",
        tenant_id: session.user.user_metadata?.tenant_id || "",
      };
      set({ isAuthenticated: true, user: u });
    } else {
      set({ isAuthenticated: false, user: null });
    }
  },

  login: async (email, password) => {
    try {
      const supabase = createClient();
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password: password || "",
      });

      if (error || !data.user) {
        console.error("AuthStore login error:", error);
        return false;
      }

      const u: User = {
        id: data.user.id,
        email: data.user.email || "",
        name: data.user.user_metadata?.full_name || data.user.email?.split("@")[0].toUpperCase() || "User",
        role: data.user.user_metadata?.role || "admin",
        tenant_id: data.user.user_metadata?.tenant_id || "",
      };

      set({ isAuthenticated: true, user: u });
      return true;
    } catch (err) {
      console.error("AuthStore login exception:", err);
      return false;
    }
  },

  logout: async () => {
    try {
      const supabase = createClient();
      await supabase.auth.signOut();
    } catch (err) {
      console.error("AuthStore logout error:", err);
    } finally {
      set({ isAuthenticated: false, user: null });
    }
  },

  signup: async (name, email, password) => {
    try {
      const supabase = createClient();
      const { data, error } = await supabase.auth.signUp({
        email,
        password: password || "Visoora@2024",
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
          data: {
            full_name: name,
            role: "admin",
            // Note: in a real app, tenant_id should be securely assigned by the backend
            // after email verification, not directly accepted from client.
          }
        }
      });

      if (error) {
        console.error("AuthStore signup error:", error);
        return false;
      }

      return true;
    } catch (err) {
      console.error("AuthStore signup exception:", err);
      return false;
    }
  },
}));
