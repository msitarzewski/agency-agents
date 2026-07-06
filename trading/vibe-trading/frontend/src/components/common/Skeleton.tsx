import { cn } from "@/lib/utils";

export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={cn("animate-pulse rounded-md bg-muted/50", className)} style={style} />;
}

export function SkeletonMetrics() {
  return (
    <div className="grid grid-cols-3 gap-1.5 p-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex flex-col items-center gap-1.5 py-2">
          <Skeleton className="h-2 w-10" />
          <Skeleton className="h-4 w-14" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart({ height = 300 }: { height?: number }) {
  return <Skeleton className="w-full" style={{ height }} />;
}
