import { Skeleton, SkeletonCard, SkeletonTable, SkeletonChart, SkeletonText } from "./skeleton";

/* ── DashboardSkeleton ── */

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Skeleton className="h-7 w-48 mb-2" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Top row: Value + Health Score cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Risks + Holdings cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm space-y-3">
          <Skeleton className="h-4 w-1/4" />
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-3.5 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm space-y-3">
          <Skeleton className="h-4 w-1/4" />
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <Skeleton className="h-3.5 w-1/3" />
              <Skeleton className="h-3.5 w-1/5" />
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonChart />
        <SkeletonChart />
      </div>

      {/* AI Summary */}
      <div className="rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm space-y-3">
        <Skeleton className="h-4 w-1/5" />
        <SkeletonText lines={4} />
      </div>
    </div>
  );
}

/* ── HoldingsSkeleton ── */

export function HoldingsSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-7 w-32 mb-2" />
        <Skeleton className="h-4 w-56" />
      </div>
      <SkeletonTable rows={8} columns={5} />
    </div>
  );
}

/* ── WealthSkeleton ── */

export function WealthSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Skeleton className="h-7 w-48 mb-2" />
        <Skeleton className="h-4 w-72" />
      </div>

      {/* Net Worth Hero */}
      <div className="rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm">
        <div className="flex items-baseline justify-between">
          <div className="space-y-2">
            <Skeleton className="h-3.5 w-20" />
            <Skeleton className="h-9 w-48" />
            <Skeleton className="h-3.5 w-40" />
          </div>
          <div className="space-y-2 text-right">
            <Skeleton className="h-3.5 w-28 ml-auto" />
            <Skeleton className="h-3.5 w-32 ml-auto" />
          </div>
        </div>
      </div>

      {/* Summary cards row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>

      {/* Goals + Weekly Recap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Chart */}
      <SkeletonChart />

      {/* Allocation + Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonChart />
        <SkeletonCard />
      </div>

      {/* AI Insights */}
      <div className="rounded-xl border border-slate-200/60 bg-white p-6 shadow-sm space-y-3">
        <Skeleton className="h-4 w-1/5" />
        <SkeletonText lines={4} />
      </div>
    </div>
  );
}
