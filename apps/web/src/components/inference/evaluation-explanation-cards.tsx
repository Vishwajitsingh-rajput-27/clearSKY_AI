"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { useInferenceStore } from "@/store/inference-store";

const metricLabels: Record<string, string> = {
  metric_mode: "Metric mode",
  psnr: "PSNR",
  ssim: "SSIM",
  rmse: "RMSE",
  mae: "MAE",
  sam: "SAM",
  spectral_consistency_score: "Spectral consistency",
  cloud_reduction_score: "Cloud reduction",
  no_reference_quality_score: "No-reference quality"
};

export function EvaluationExplanationCards() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = hasMounted ? currentRun : null;
  const explanation = selectedRun?.evaluation_explanation ?? {};
  const entries = Object.entries(explanation).filter(([key]) => key !== "metric_mode");

  if (!selectedRun || entries.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {entries.map(([key, value]) => (
        <Card key={key}>
          <CardHeader>
            <CardTitle className="text-sm">{metricLabels[key] ?? key}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">{value}</CardContent>
        </Card>
      ))}
    </div>
  );
}
