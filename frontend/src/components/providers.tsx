"use client";

import React, { useState, useEffect, useCallback } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContext, User, getStoredToken, setStoredToken, removeStoredToken } from "@/lib/auth";
import { api } from "@/lib/api";
import { initNativePlugins } from "@/lib/capacitor";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/theme-provider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initNativePlugins();
  }, []);

  useEffect(() => {
    const stored = getStoredToken();
    if (stored) {
      setToken(stored);
      api.get<User>("/auth/me").then(setUser).catch(() => {
        removeStoredToken();
        setToken(null);
      }).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback((newToken: string, newUser: User) => {
    setStoredToken(newToken);
    setToken(newToken);
    setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    removeStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-neutral-500">Loading...</div>
      </div>
    );
  }

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!user }}>
          {children}
          <Toaster />
        </AuthContext.Provider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
