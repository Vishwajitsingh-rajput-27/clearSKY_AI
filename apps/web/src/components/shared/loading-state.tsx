import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {["a", "b", "c"].map((item) => (
        <div className="rounded-md border p-5" key={item}>
          <Skeleton className="h-4 w-24" />
          <Skeleton className="mt-4 h-8 w-32" />
          <Skeleton className="mt-3 h-3 w-full" />
        </div>
      ))}
    </div>
  );
}

