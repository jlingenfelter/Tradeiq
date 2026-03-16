"use client";

import { useEffect, useState } from "react";
import { useToasts, type Toast, type ToastType } from "@/hooks/use-toast";
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from "lucide-react";

const iconMap: Record<ToastType, React.ElementType> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const colorMap: Record<ToastType, { bg: string; border: string; icon: string; progress: string }> = {
  success: {
    bg: "bg-green-50",
    border: "border-green-200",
    icon: "text-green-600",
    progress: "bg-green-500",
  },
  error: {
    bg: "bg-red-50",
    border: "border-red-200",
    icon: "text-red-600",
    progress: "bg-red-500",
  },
  warning: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    icon: "text-amber-600",
    progress: "bg-amber-500",
  },
  info: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    icon: "text-blue-600",
    progress: "bg-blue-500",
  },
};

const AUTO_DISMISS_MS = 4000;

function ToastItem({ toast: t, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [mounted, setMounted] = useState(false);
  const [exiting, setExiting] = useState(false);
  const Icon = iconMap[t.type];
  const colors = colorMap[t.type];

  useEffect(() => {
    // Trigger enter animation
    const frame = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  function handleDismiss() {
    setExiting(true);
    setTimeout(() => onDismiss(t.id), 200);
  }

  return (
    <div
      className={`
        relative overflow-hidden rounded-lg border shadow-lg
        ${colors.bg} ${colors.border}
        transition-all duration-200 ease-out
        ${mounted && !exiting ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"}
        w-full max-w-sm
      `}
      role="alert"
    >
      <div className="flex items-start gap-3 p-4">
        <Icon className={`h-5 w-5 shrink-0 mt-0.5 ${colors.icon}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-900">{t.title}</p>
          {t.description && (
            <p className="text-xs text-slate-600 mt-0.5">{t.description}</p>
          )}
        </div>
        <button
          onClick={handleDismiss}
          className="shrink-0 rounded-md p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      {/* Progress bar */}
      <div className="h-1 w-full bg-black/5">
        <div
          className={`h-full ${colors.progress} transition-none`}
          style={{
            animation: `toast-progress ${AUTO_DISMISS_MS}ms linear forwards`,
          }}
        />
      </div>
    </div>
  );
}

export function Toaster() {
  const { toasts, dismiss } = useToasts();

  return (
    <>
      {/* Keyframes for the progress bar */}
      <style>{`
        @keyframes toast-progress {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
      {/* Container: bottom-right on desktop, bottom-center on mobile */}
      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 items-end max-sm:right-0 max-sm:left-0 max-sm:items-center max-sm:px-4"
      >
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={dismiss} />
        ))}
      </div>
    </>
  );
}
