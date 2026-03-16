import { cn } from "@/lib/utils";

/* ── Base Skeleton ── */

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ className, width, height, style, ...props }: SkeletonProps) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-neutral-200", className)}
      style={{ width, height, ...style }}
      {...props}
    />
  );
}

/* ── SkeletonText ── */

interface SkeletonTextProps {
  lines?: number;
  className?: string;
}

export function SkeletonText({ lines = 3, className }: SkeletonTextProps) {
  const widths = ["100%", "92%", "78%", "85%", "65%"];
  return (
    <div className={cn("space-y-2.5", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-3.5" style={{ width: widths[i % widths.length] }} />
      ))}
    </div>
  );
}

/* ── SkeletonCard ── */

interface SkeletonCardProps {
  className?: string;
}

export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div className={cn("rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm space-y-4", className)}>
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <SkeletonText lines={2} />
    </div>
  );
}

/* ── SkeletonTable ── */

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function SkeletonTable({ rows = 5, columns = 4, className }: SkeletonTableProps) {
  return (
    <div className={cn("rounded-xl border border-slate-200/60 bg-white shadow-sm overflow-hidden", className)}>
      {/* Header */}
      <div className="flex gap-4 px-6 py-3 border-b bg-slate-50/50">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-3.5 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={rowIdx} className="flex gap-4 px-6 py-3.5 border-b last:border-0">
          {Array.from({ length: columns }).map((_, colIdx) => (
            <Skeleton
              key={colIdx}
              className="h-3.5 flex-1"
              style={{ opacity: 0.6 + (colIdx % 3) * 0.15 }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/* ── SkeletonChart ── */

interface SkeletonChartProps {
  className?: string;
}

export function SkeletonChart({ className }: SkeletonChartProps) {
  return (
    <div className={cn("rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm space-y-4", className)}>
      <Skeleton className="h-4 w-1/4" />
      <div className="flex items-end gap-2 h-40">
        {[40, 65, 50, 80, 60, 72, 55, 90, 45, 70].map((h, i) => (
          <Skeleton key={i} className="flex-1 rounded-sm" style={{ height: `${h}%` }} />
        ))}
      </div>
    </div>
  );
}
