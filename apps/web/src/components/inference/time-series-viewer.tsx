"use client";

/* eslint-disable @next/next/no-img-element */

import { useMemo, useState } from "react";
import { CalendarDays, GitCompareArrows } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { resolveAssetUrl } from "@/lib/api";
import type { InferenceHistoryItem } from "@/store/inference-store";
import { useInferenceStore } from "@/store/inference-store";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function confidence(run: InferenceHistoryItem) {
  return run.reconstruction_confidence_score ?? run.metrics.reconstruction_confidence_score ?? null;
}

function RunPreview({ run, label }: { run: InferenceHistoryItem; label: string }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-muted-foreground">{formatDate(run.created_at)}</p>
        </div>
        <Badge variant="outline">{run.used_model}</Badge>
      </div>
      <div className="aspect-[4/3] overflow-hidden rounded-md border bg-muted/30">
        <img
          alt={`${label} reconstruction for ${run.file_name}`}
          className="h-full w-full object-contain"
          src={resolveAssetUrl(run.reconstructed_image_url)}
        />
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="rounded-md border p-2">
          <p className="text-muted-foreground">Cloud</p>
          <p className="font-medium">{run.cloud_coverage_percent.toFixed(1)}%</p>
        </div>
        <div className="rounded-md border p-2">
          <p className="text-muted-foreground">Quality</p>
          <p className="font-medium">{run.quality_score.toFixed(1)}</p>
        </div>
        <div className="rounded-md border p-2">
          <p className="text-muted-foreground">Confidence</p>
          <p className="font-medium">{confidence(run)?.toFixed(1) ?? "n/a"}</p>
        </div>
      </div>
    </div>
  );
}

export function TimeSeriesViewer() {
  const hasMounted = useHasMounted();
  const history = useInferenceStore((state) => state.history);
  const runs = useMemo(
    () =>
      [...history].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      ),
    [history]
  );
  const [primaryIndex, setPrimaryIndex] = useState(0);
  const [compareIndex, setCompareIndex] = useState(Math.max(0, runs.length - 1));

  if (!hasMounted || runs.length === 0) {
    return (
      <EmptyState
        title="No time-series data"
        description="Run multiple reconstructions or the sample demo to compare dates and outputs."
      />
    );
  }

  const maxIndex = Math.max(0, runs.length - 1);
  const safePrimaryIndex = Math.min(primaryIndex, maxIndex);
  const safeCompareIndex = Math.min(compareIndex, maxIndex);
  const primary = runs[safePrimaryIndex];
  const comparison = runs[safeCompareIndex];
  const confidenceDelta =
    confidence(primary) !== null && confidence(comparison) !== null
      ? Number(confidence(primary)) - Number(confidence(comparison))
      : null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
            Interactive time-series viewer
          </CardTitle>
          <CardDescription>Select a processed date and inspect reconstruction confidence over time.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Selected date</span>
              <span className="text-muted-foreground">{formatDate(primary.created_at)}</span>
            </div>
            <input
              aria-label="Selected time-series date"
              className="w-full accent-primary"
              max={maxIndex}
              min={0}
              type="range"
              value={safePrimaryIndex}
              onChange={(event) => setPrimaryIndex(Number(event.target.value))}
            />
          </div>
          <RunPreview label="Selected reconstruction" run={primary} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompareArrows className="h-4 w-4 text-muted-foreground" />
            Multi-date comparison slider
          </CardTitle>
          <CardDescription>Compare two processed dates side-by-side for model and confidence review.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Comparison date</span>
              <span className="text-muted-foreground">{formatDate(comparison.created_at)}</span>
            </div>
            <input
              aria-label="Comparison time-series date"
              className="w-full accent-primary"
              max={maxIndex}
              min={0}
              type="range"
              value={safeCompareIndex}
              onChange={(event) => setCompareIndex(Number(event.target.value))}
            />
          </div>
          <Separator />
          <div className="grid gap-4 lg:grid-cols-2">
            <RunPreview label="Primary" run={primary} />
            <RunPreview label="Comparison" run={comparison} />
          </div>
          <div className="rounded-md border p-3 text-sm">
            <span className="text-muted-foreground">Confidence delta: </span>
            <span className="font-medium">
              {confidenceDelta === null ? "n/a" : `${confidenceDelta.toFixed(1)} points`}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
