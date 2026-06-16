"use client";

import { Activity, Cloud, Gauge, Moon, ShieldCheck, type LucideIcon } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useHasMounted } from "@/hooks/use-has-mounted";
import type { InferenceHistoryItem } from "@/store/inference-store";
import { useInferenceStore } from "@/store/inference-store";

type InferenceMetricsPanelProps = {
  compact?: boolean;
  run?: InferenceHistoryItem | null;
};

export function InferenceMetricsPanel({ compact = false, run }: InferenceMetricsPanelProps) {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = run ?? (hasMounted ? currentRun : null);

  if (!selectedRun) {
    const placeholderMetrics: Array<{
      title: string;
      description: string;
      icon: LucideIcon;
    }> = [
      { title: "Cloud coverage", description: "Awaiting run", icon: Cloud },
      { title: "Shadow coverage", description: "Awaiting run", icon: Moon },
      { title: "Quality score", description: "Awaiting run", icon: Gauge },
      { title: "Processing time", description: "Awaiting run", icon: Activity }
    ];

    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {placeholderMetrics.map(({ title, description, icon }) => (
          <MetricCard
            key={title}
            title={title}
            value="-"
            description={description}
            icon={icon}
          />
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: "Cloud coverage",
      value: `${selectedRun.cloud_coverage_percent.toFixed(2)}%`,
      description: "Detected cloud pixels",
      icon: Cloud
    },
    {
      title: "Shadow coverage",
      value: `${selectedRun.shadow_coverage_percent.toFixed(2)}%`,
      description: "Detected cloud shadow pixels",
      icon: Moon
    },
    {
      title: "Quality score",
      value: selectedRun.quality_score.toFixed(1),
      description: "Baseline visual quality index",
      icon: Gauge
    },
    {
      title: "Confidence score",
      value:
        selectedRun.reconstruction_confidence_score?.toFixed(1) ??
        selectedRun.metrics.reconstruction_confidence_score?.toFixed(1) ??
        "n/a",
      description: "Reconstruction reliability proxy",
      icon: ShieldCheck
    },
    {
      title: "Processing time",
      value: `${selectedRun.processing_time_seconds.toFixed(2)}s`,
      description: "CPU endpoint runtime",
      icon: Activity
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((metric) => (
          <MetricCard key={metric.title} {...metric} />
        ))}
      </div>

      {!compact ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>Run metadata</CardTitle>
                <CardDescription>{selectedRun.file_name}</CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">requested: {selectedRun.requested_model}</Badge>
                <Badge variant="secondary">used: {selectedRun.used_model}</Badge>
                {selectedRun.fallback_used ? <Badge>fallback</Badge> : null}
              </div>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            {[
              ["Cloud", selectedRun.cloud_coverage_percent],
              ["Shadow", selectedRun.shadow_coverage_percent],
              ["Mask", selectedRun.metrics.mask_coverage_percent],
              [
                "Confidence",
                selectedRun.reconstruction_confidence_score ??
                  selectedRun.metrics.reconstruction_confidence_score ??
                  0
              ]
            ].map(([label, value]) => (
              <div className="space-y-2" key={String(label)}>
                <div className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="text-muted-foreground">{Number(value).toFixed(2)}%</span>
                </div>
                <Progress value={Number(value)} />
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
