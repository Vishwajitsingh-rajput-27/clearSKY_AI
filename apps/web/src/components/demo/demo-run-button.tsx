"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { useInferenceStore } from "@/store/inference-store";

type DemoRunButtonProps = {
  redirectToDashboard?: boolean;
  variant?: "default" | "outline" | "secondary" | "ghost";
  size?: "default" | "sm" | "lg";
  className?: string;
};

export function DemoRunButton({
  redirectToDashboard = false,
  variant = "default",
  size = "default",
  className
}: DemoRunButtonProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const startDemoRun = useInferenceStore((state) => state.startDemoRun);
  const completeDemoRun = useInferenceStore((state) => state.completeDemoRun);
  const failRun = useInferenceStore((state) => state.failRun);

  const mutation = useMutation({
    mutationFn: apiClient.runDemo,
    onMutate: startDemoRun,
    onSuccess: (demo) => {
      completeDemoRun(demo);
      queryClient.invalidateQueries({ queryKey: ["benchmarks"] });

      if (redirectToDashboard) {
        router.push("/dashboard");
      }
    },
    onError: (error) => {
      failRun(error instanceof Error ? error.message : "Demo run failed.");
    }
  });

  return (
    <Button
      className={className}
      disabled={mutation.isPending}
      onClick={() => mutation.mutate()}
      size={size}
      type="button"
      variant={variant}
    >
      {mutation.isPending ? (
        <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
      ) : (
        <Play className="mr-2 h-4 w-4" aria-hidden="true" />
      )}
      {mutation.isPending ? "Running demo" : "Run sample demo"}
    </Button>
  );
}
