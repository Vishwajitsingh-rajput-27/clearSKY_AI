"use client";

import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, CheckCircle2, Database, HardDrive, Trophy } from "lucide-react";
import { MetricCard } from "@/components/shared/metric-card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { apiClient, type ModelRegistryResponse } from "@/lib/api";

function formatDate(value?: string | null) {
  if (!value) {
    return "Not trained";
  }

  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(value));
}

function metricNumber(metrics: Record<string, unknown>, key: string) {
  const value = metrics[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function qualityScore(model?: ModelRegistryResponse | null) {
  if (!model) {
    return null;
  }

  return (
    metricNumber(model.metrics, "no_reference_quality_score") ??
    metricNumber(model.metrics, "quality_score") ??
    metricNumber(model.metrics, "spectral_consistency_score") ??
    null
  );
}

function modalities(model: ModelRegistryResponse) {
  const rawModalities = model.input_modalities?.modalities;
  return Array.isArray(rawModalities) ? rawModalities.join(", ") : "LISS-IV";
}

function checkpointBadge(status: string) {
  if (status === "available" || status === "not_required") {
    return <Badge variant="secondary">{status}</Badge>;
  }

  return <Badge variant="outline">{status}</Badge>;
}

export function ModelRegistryContent() {
  const summaryQuery = useQuery({
    queryKey: ["model-registry", "summary"],
    queryFn: apiClient.modelRegistrySummary
  });
  const modelsQuery = useQuery({
    queryKey: ["model-registry", "models"],
    queryFn: apiClient.modelRegistryModels
  });
  const checkpointsQuery = useQuery({
    queryKey: ["model-registry", "checkpoints"],
    queryFn: apiClient.checkpoints
  });

  if (summaryQuery.isLoading || modelsQuery.isLoading || checkpointsQuery.isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton className="h-32 w-full" key={index} />
        ))}
      </div>
    );
  }

  if (summaryQuery.isError || modelsQuery.isError || checkpointsQuery.isError) {
    const error = summaryQuery.error ?? modelsQuery.error ?? checkpointsQuery.error;
    return (
      <Alert variant="destructive">
        <AlertTitle>Model registry unavailable</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : "Could not load model registry data."}
        </AlertDescription>
      </Alert>
    );
  }

  const summary = summaryQuery.data;
  const models = modelsQuery.data ?? [];
  const checkpoints = checkpointsQuery.data ?? [];
  const bestModel = summary?.best_model ?? null;
  const bestScore = summary?.best_quality_score ?? qualityScore(bestModel);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Registered models"
          value={`${summary?.registered_models ?? models.length}`}
          description="Versioned model entries"
          icon={BrainCircuit}
        />
        <MetricCard
          title="Active models"
          value={`${summary?.active_models ?? models.filter((model) => model.is_active).length}`}
          description="Available in selection flow"
          icon={CheckCircle2}
        />
        <MetricCard
          title="Experiments"
          value={`${summary?.experiment_count ?? 0}`}
          description="Training and validation runs"
          icon={Database}
        />
        <MetricCard
          title="Checkpoints"
          value={`${summary?.checkpoint_count ?? checkpoints.length}`}
          description="Managed checkpoint records"
          icon={HardDrive}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            Best available model
          </CardTitle>
          <CardDescription>
            Selected from active models with available checkpoints or deterministic operational baselines.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {bestModel ? (
            <div className="grid gap-4 lg:grid-cols-[1fr_18rem]">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-semibold">{bestModel.model_name}</h2>
                  <Badge>{bestModel.version}</Badge>
                  <Badge variant="outline">{bestModel.stage}</Badge>
                  {checkpointBadge(bestModel.checkpoint_status)}
                </div>
                <p className="max-w-3xl text-sm text-muted-foreground">{bestModel.architecture}</p>
                <div className="grid gap-2 text-sm sm:grid-cols-2 xl:grid-cols-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Dataset</p>
                    <p className="font-medium">{bestModel.dataset_version ?? "Pending"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Training date</p>
                    <p className="font-medium">{formatDate(bestModel.training_date)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Runtime</p>
                    <p className="font-medium">{bestModel.runtime_type}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Modalities</p>
                    <p className="font-medium">{modalities(bestModel)}</p>
                  </div>
                </div>
              </div>
              <div className="space-y-2 rounded-md border p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-muted-foreground">Selection score</span>
                  <span className="text-2xl font-semibold">{bestScore?.toFixed(1) ?? "n/a"}</span>
                </div>
                <Progress value={bestScore ?? 0} />
                <p className="text-xs text-muted-foreground">
                  Scores are computed from recorded metrics; missing trained checkpoints remain visible but are not selected.
                </p>
              </div>
            </div>
          ) : (
            <Alert>
              <AlertTitle>No best model selected</AlertTitle>
              <AlertDescription>Register a model or complete a benchmarked training run.</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model versions</CardTitle>
          <CardDescription>Registered versions, datasets, checkpoint status, and tracked metrics.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Dataset</TableHead>
                <TableHead>Checkpoint</TableHead>
                <TableHead>Quality</TableHead>
                <TableHead>Best</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((model) => {
                const score = qualityScore(model);
                return (
                  <TableRow key={model.id}>
                    <TableCell>
                      <div className="font-medium">{model.model_name}</div>
                      <div className="text-xs text-muted-foreground">{model.architecture}</div>
                    </TableCell>
                    <TableCell>{model.version}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{model.stage}</Badge>
                    </TableCell>
                    <TableCell>{model.dataset_version ?? "Pending"}</TableCell>
                    <TableCell>{checkpointBadge(model.checkpoint_status)}</TableCell>
                    <TableCell>{score?.toFixed(1) ?? "n/a"}</TableCell>
                    <TableCell>{model.is_best ? <Badge>Selected</Badge> : <Badge variant="outline">No</Badge>}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Checkpoint management</CardTitle>
          <CardDescription>Checkpoint paths, availability, best flags, and metric anchors.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Checkpoint</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Metric</TableHead>
                <TableHead>Epoch</TableHead>
                <TableHead>Best</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {checkpoints.map((checkpoint) => (
                <TableRow key={checkpoint.id}>
                  <TableCell className="max-w-xs truncate font-medium">
                    {checkpoint.checkpoint_path}
                  </TableCell>
                  <TableCell>{checkpoint.model_name}</TableCell>
                  <TableCell>{checkpointBadge(checkpoint.status)}</TableCell>
                  <TableCell>
                    {checkpoint.metric_name && checkpoint.metric_value !== null
                      ? `${checkpoint.metric_name}: ${checkpoint.metric_value?.toFixed(1)}`
                      : "n/a"}
                  </TableCell>
                  <TableCell>{checkpoint.epoch ?? "n/a"}</TableCell>
                  <TableCell>{checkpoint.is_best ? <Badge>Yes</Badge> : <Badge variant="outline">No</Badge>}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
