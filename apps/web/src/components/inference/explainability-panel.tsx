"use client";

/* eslint-disable @next/next/no-img-element */

import { BrainCircuit, Download, Lightbulb, ShieldCheck } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { MetricCard } from "@/components/shared/metric-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { resolveAssetUrl } from "@/lib/api";
import type { InferenceHistoryItem } from "@/store/inference-store";
import { useInferenceStore } from "@/store/inference-store";

type ExplainabilityPanelProps = {
  run?: InferenceHistoryItem | null;
};

function confidenceValue(run: InferenceHistoryItem) {
  return run.reconstruction_confidence_score ?? run.metrics.reconstruction_confidence_score ?? null;
}

function severityVariant(severity: string) {
  return severity === "high" ? "destructive" : severity === "medium" ? "secondary" : "outline";
}

export function ExplainabilityPanel({ run }: ExplainabilityPanelProps) {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = run ?? (hasMounted ? currentRun : null);

  if (!selectedRun) {
    return (
      <EmptyState
        title="No explainability output"
        description="Run reconstruction to generate attention maps, confidence maps, and recommendations."
      />
    );
  }

  const confidence = confidenceValue(selectedRun);
  const attentionUrl = selectedRun.attention_map_url ? resolveAssetUrl(selectedRun.attention_map_url) : null;
  const confidenceUrl = selectedRun.confidence_map_url ? resolveAssetUrl(selectedRun.confidence_map_url) : null;
  const recommendations = selectedRun.recommendations ?? [];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="Confidence score"
          value={confidence === null ? "n/a" : confidence.toFixed(1)}
          description="Reconstruction reliability proxy"
          icon={ShieldCheck}
        />
        <MetricCard
          title="Recommendations"
          value={`${recommendations.length}`}
          description="AI-suggested next actions"
          icon={Lightbulb}
        />
        <MetricCard
          title="Fallback"
          value={selectedRun.fallback_used ? "Used" : "No"}
          description={selectedRun.used_model}
          icon={BrainCircuit}
        />
      </div>

      {confidence !== null ? (
        <Card>
          <CardHeader>
            <CardTitle>Reconstruction confidence</CardTitle>
            <CardDescription>Lower values should be reviewed with fusion or temporal context.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Confidence</span>
              <span className="font-medium">{confidence.toFixed(1)}%</span>
            </div>
            <Progress value={confidence} />
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {[
          {
            title: "Attention map",
            description: "Proxy focus overlay from masks, edges, and reconstruction delta.",
            url: attentionUrl,
            filename: "attention-map.png"
          },
          {
            title: "Confidence map",
            description: "Pixel-level confidence proxy for reconstructed and stable areas.",
            url: confidenceUrl,
            filename: "confidence-map.png"
          }
        ].map((item) => (
          <Card key={item.title}>
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-base">{item.title}</CardTitle>
                  <CardDescription>{item.description}</CardDescription>
                </div>
                {item.url ? (
                  <Button asChild size="icon" variant="outline" aria-label={`Download ${item.title}`}>
                    <a href={item.url} download={item.filename}>
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                ) : null}
              </div>
            </CardHeader>
            <CardContent>
              {item.url ? (
                <div className="aspect-[4/3] overflow-hidden rounded-md border bg-muted/30">
                  <img
                    alt={`${item.title} for ${selectedRun.file_name}`}
                    className="h-full w-full object-contain"
                    src={item.url}
                  />
                </div>
              ) : (
                <div className="flex aspect-[4/3] items-center justify-center rounded-md border bg-muted/30 text-sm text-muted-foreground">
                  Not available for this run
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>AI recommendation engine</CardTitle>
          <CardDescription>Operational suggestions based on cloud/shadow coverage, metadata, and confidence.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {recommendations.length ? (
            recommendations.map((item) => (
              <div className="rounded-md border p-4" key={`${item.title}-${item.message}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-medium">{item.title}</h3>
                  <Badge variant={severityVariant(item.severity)}>{item.severity}</Badge>
                </div>
                <p className="mt-2 text-sm">{item.message}</p>
                <p className="mt-2 text-xs text-muted-foreground">{item.rationale}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.recommended_inputs.map((input) => (
                    <Badge key={input} variant="outline">
                      {input}
                    </Badge>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No recommendations recorded for this run.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
