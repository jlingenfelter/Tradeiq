import { useSyncExternalStore, useCallback } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  createdAt: number;
}

const MAX_TOASTS = 3;
const AUTO_DISMISS_MS = 4000;

let toasts: Toast[] = [];
let listeners: Array<() => void> = [];
const timers = new Map<string, ReturnType<typeof setTimeout>>();

function emitChange() {
  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void) {
  listeners = [...listeners, listener];
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

function getSnapshot(): Toast[] {
  return toasts;
}

function addToast(type: ToastType, title: string, description?: string) {
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const newToast: Toast = { id, type, title, description, createdAt: Date.now() };

  // Evict oldest if at max
  if (toasts.length >= MAX_TOASTS) {
    const oldest = toasts[0];
    removeToast(oldest.id);
  }

  toasts = [...toasts, newToast];
  emitChange();

  // Auto-dismiss
  const timer = setTimeout(() => {
    removeToast(id);
  }, AUTO_DISMISS_MS);
  timers.set(id, timer);

  return id;
}

function removeToast(id: string) {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
  toasts = toasts.filter((t) => t.id !== id);
  emitChange();
}

export function useToasts() {
  const currentToasts = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  const dismiss = useCallback((id: string) => removeToast(id), []);
  return { toasts: currentToasts, dismiss };
}

export const toast = {
  success: (title: string, description?: string) => addToast("success", title, description),
  error: (title: string, description?: string) => addToast("error", title, description),
  warning: (title: string, description?: string) => addToast("warning", title, description),
  info: (title: string, description?: string) => addToast("info", title, description),
  dismiss: removeToast,
};
