"use client";

import {
  Activity,
  BarChart3,
  Cloud,
  Gauge,
  LineChart,
  Ruler,
  Target,
  Timer
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { MetricCard } from "@/components/shared/metric-card";
import { resolveAssetUrl } from "@/lib/api";
import { useInferenceStore } from "@/store/inference-store";

function formatMetric(value: number | null | undefined, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }

  return value.toFixed(digits);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }

  return `${value.toFixed(1)}%`;
}

export function EvaluationMetricCards() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = hasMounted ? currentRun : null;
  const evaluation = selectedRun?.evaluation;

  const cards = [
    {
      title: "SSIM",
      value: formatMetric(evaluation?.ssim, 4),
      description: selectedRun?.evaluation_mode ?? "Awaiting run",
      icon: Gauge
    },
    {
      title: "PSNR",
      value: formatMetric(evaluation?.psnr, 2),
      description: evaluation?.psnr === null ? "Requires ground truth" : "dB",
      icon: BarChart3
    },
    {
      title: "RMSE",
      value: formatMetric(evaluation?.rmse, 4),
      description: evaluation?.rmse === null ? "Requires ground truth" : "Normalized error",
      icon: Ruler
    },
    {
      title: "MAE",
      value: formatMetric(evaluation?.mae, 4),
      description: evaluation?.mae === null ? "Requires ground truth" : "Normalized error",
      icon: LineChart
    },
    {
      title: "SAM",
      value: formatMetric(evaluation?.sam, 4),
      description: evaluation?.sam === null ? "Requires ground truth" : "Radians",
      icon: Target
    },
    {
      title: "Spectral score",
      value: formatPercent(evaluation?.spectral_consistency_score),
      description: "Spectral preservation",
      icon: Activity
    },
    {
      title: "Cloud reduction",
      value: formatPercent(evaluation?.cloud_reduction_score),
      description: "Detected cloud suppression",
      icon: Cloud
    },
    {
      title: "Quality score",
      value: formatPercent(evaluation?.no_reference_quality_score),
      description: "No-reference proxy",
      icon: Timer
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((metric) => (
          <MetricCard key={metric.title} {...metric} />
        ))}
      </div>

      {selectedRun?.evaluation_report_url || selectedRun?.evaluation_report_markdown_url ? (
        <div className="flex flex-wrap gap-2">
          {selectedRun.evaluation_report_url ? (
            <Button variant="outline" asChild>
              <a href={resolveAssetUrl(selectedRun.evaluation_report_url)} target="_blank" rel="noreferrer">
                Download JSON report
              </a>
            </Button>
          ) : null}
          {selectedRun.evaluation_report_markdown_url ? (
            <Button variant="outline" asChild>
              <a
                href={resolveAssetUrl(selectedRun.evaluation_report_markdown_url)}
                target="_blank"
                rel="noreferrer"
              >
                Download Markdown report
              </a>
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
