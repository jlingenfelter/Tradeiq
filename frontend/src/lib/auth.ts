"use client";

import { createContext, useContext } from "react";

export interface User {
  id: string;
  email: string;
  base_currency: string;
  timezone: string;
  created_at: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function useAuth() {
  return useContext(AuthContext);
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setStoredToken(token: string): void {
  localStorage.setItem("token", token);
}

export function removeStoredToken(): void {
  localStorage.removeItem("token");
}
