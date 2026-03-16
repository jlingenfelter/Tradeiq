import { FileQuestion, LayoutDashboard, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-8">
      <div className="mx-auto max-w-md text-center">
        <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-neutral-100">
          <FileQuestion className="h-12 w-12 text-neutral-400" />
        </div>
        <h1 className="text-4xl font-bold text-neutral-900">404</h1>
        <h2 className="mt-1 text-lg font-medium text-neutral-600">
          Page Not Found
        </h2>
        <p className="mt-2 text-sm text-neutral-500">
          The page you're looking for doesn't exist or may have been moved.
        </p>
        <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button asChild>
            <Link href="/dashboard">
              <LayoutDashboard className="mr-1.5 h-4 w-4" />
              Go to Dashboard
            </Link>
          </Button>
        </div>
        <div className="mt-8 rounded-lg border border-neutral-200 bg-white p-4">
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <Search className="h-4 w-4" />
            <span>Try navigating from the sidebar or check the URL</span>
          </div>
        </div>
      </div>
    </div>
  );
}
