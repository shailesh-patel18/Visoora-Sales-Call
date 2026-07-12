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
  const state = useAuthStore.getState();
  if (state.token) {
    return {
      Authorization: `Bearer ${state.token}`,
      "X-Tenant-ID": state.user?.tenant_id || "anonymous"
    };
  }
  return {};
};

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (email: string, password?: string) => Promise<boolean>;
  logout: () => Promise<void>;
  signup: (name: string, email: string, password?: string) => Promise<{ success: boolean; error?: string }>;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: null,

  checkSession: async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.user && session.access_token) {
      const u: User = {
        id: session.user.id,
        email: session.user.email || "",
        name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0].toUpperCase() || "User",
        role: session.user.user_metadata?.role || "admin",
        tenant_id: session.user.user_metadata?.tenant_id || "",
      };
      set({ isAuthenticated: true, user: u, token: session.access_token });
    } else {
      set({ isAuthenticated: false, user: null, token: null });
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

      set({ isAuthenticated: true, user: u, token: data.session?.access_token || null });
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
      set({ isAuthenticated: false, user: null, token: null });
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
          }
        }
      });

      if (error) {
        console.error("AuthStore signup error:", error);
        let errorMsg = error.message || error.error_description;
        if (!errorMsg && typeof error === 'string') errorMsg = error;
        if (!errorMsg || errorMsg === "{}" || errorMsg === "[object Object]") {
          errorMsg = "Registration failed: User already registered or email unavailable.";
        }
        return { success: false, error: errorMsg };
      }

      return { success: true };
    } catch (err: any) {
      console.error("AuthStore signup exception:", err);
      return { success: false, error: err?.message || "An unexpected error occurred" };
    }
  },
}));
