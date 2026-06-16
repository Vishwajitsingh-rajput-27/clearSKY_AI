"use client";

import { AlertCircle, CheckCircle2 } from "lucide-react";
import { DemoRunButton } from "@/components/demo/demo-run-button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { useInferenceStore } from "@/store/inference-store";

type DemoModeCardProps = {
  redirectToDashboard?: boolean;
  compact?: boolean;
  showButton?: boolean;
};

export function DemoModeCard({
  redirectToDashboard = false,
  compact = false,
  showButton = true
}: DemoModeCardProps) {
  const errorMessage = useInferenceStore((state) => state.errorMessage);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Judge demo mode</CardTitle>
            <CardDescription>
              Run a deterministic synthetic satellite-like sample through the CPU baseline.
            </CardDescription>
          </div>
          <Badge variant="secondary">synthetic sample</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!compact ? (
          <div className="grid gap-3 text-sm text-muted-foreground md:grid-cols-3">
            <div className="rounded-md border p-3">No upload required for public demos.</div>
            <div className="rounded-md border p-3">Uses OpenCV fallback on CPU.</div>
            <div className="rounded-md border p-3">Metrics are labeled as synthetic-demo metrics.</div>
          </div>
        ) : null}
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>No fake claims</AlertTitle>
          <AlertDescription>
            This sample is generated locally for workflow demonstration and is not presented as
            a real LISS-IV acquisition or trained-model benchmark.
          </AlertDescription>
        </Alert>
        {errorMessage ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Demo unavailable</AlertTitle>
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        ) : null}
        {showButton ? (
          <>
            <Separator />
            <DemoRunButton redirectToDashboard={redirectToDashboard} />
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function DashboardDemoState() {
  const hasMounted = useHasMounted();
  const history = useInferenceStore((state) => state.history);
  const currentRun = useInferenceStore((state) => state.currentRun);

  if (!hasMounted) {
    return null;
  }

  if (history.length === 0 && !currentRun) {
    return <DemoModeCard compact showButton={false} />;
  }

  return null;
}
