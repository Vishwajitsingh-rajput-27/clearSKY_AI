"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, CalendarClock, CheckCircle2, FlaskConical } from "lucide-react";
import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";
import { ChartFrame } from "@/components/charts/chart-frame";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { MetricCard } from "@/components/shared/metric-card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { apiClient, type ExperimentMetricResponse, type ExperimentRunResponse } from "@/lib/api";

function formatDate(value?: string | null) {
  if (!value) {
    return "Pending";
  }

  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(value));
}

function asNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function statusBadge(status: string) {
  if (status === "completed") {
    return <Badge variant="secondary">{status}</Badge>;
  }

  if (status === "failed") {
    return <Badge variant="destructive">{status}</Badge>;
  }

  return <Badge variant="outline">{status}</Badge>;
}

function bestScore(runs: ExperimentRunResponse[]) {
  const scores = runs
    .map((run) => run.checkpoint_score)
    .filter((score): score is number => typeof score === "number");

  return scores.length ? Math.max(...scores) : null;
}

function latestTrainingDate(runs: ExperimentRunResponse[]) {
  const dates = runs
    .map((run) => run.training_date)
    .filter((value): value is string => Boolean(value))
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

  return dates[0] ?? null;
}

function buildMetricChartRows(metrics: ExperimentMetricResponse[]) {
  return metrics
    .slice()
    .reverse()
    .map((row, index) => ({
      label: `${row.model_name.split("-")[0]} ${row.step ?? index + 1}`,
      quality:
        asNumber(row.metrics.no_reference_quality_score) ??
        asNumber(row.metrics.spectral_consistency_score) ??
        0,
      cloud: asNumber(row.metrics.cloud_reduction_score) ?? 0,
      spectral: asNumber(row.metrics.spectral_consistency_score) ?? 0
    }));
}

function MetricHistoryChart({ metrics }: { metrics: ExperimentMetricResponse[] }) {
  const hasMounted = useHasMounted();
  const chartRows = buildMetricChartRows(metrics);

  if (!hasMounted) {
    return <div className="h-72 w-full rounded-md bg-muted/20" />;
  }

  if (chartRows.length === 0) {
    return (
      <Alert>
        <AlertTitle>No metric history</AlertTitle>
        <AlertDescription>Training and validation metric records will appear here.</AlertDescription>
      </Alert>
    );
  }

  return (
    <ChartFrame>
      {({ width, height }) => (
        <LineChart
          data={chartRows}
          height={height}
          margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
          width={width}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" tickLine={false} />
          <YAxis domain={[0, 100]} tickLine={false} />
          <Tooltip />
          <Line dataKey="quality" name="Quality" stroke="#2563eb" strokeWidth={2} />
          <Line dataKey="cloud" name="Cloud reduction" stroke="#16a34a" strokeWidth={2} />
          <Line dataKey="spectral" name="Spectral" stroke="#dc2626" strokeWidth={2} />
        </LineChart>
      )}
    </ChartFrame>
  );
}

export function TrainingHistoryContent() {
  const historyQuery = useQuery({
    queryKey: ["model-registry", "training-history"],
    queryFn: apiClient.trainingHistory
  });
  const metricsQuery = useQuery({
    queryKey: ["model-registry", "metrics-history"],
    queryFn: apiClient.metricsHistory
  });

  if (historyQuery.isLoading || metricsQuery.isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton className="h-32 w-full" key={index} />
          ))}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (historyQuery.isError || metricsQuery.isError) {
    const error = historyQuery.error ?? metricsQuery.error;
    return (
      <Alert variant="destructive">
        <AlertTitle>Training history unavailable</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : "Could not load training history."}
        </AlertDescription>
      </Alert>
    );
  }

  const runs = historyQuery.data ?? [];
  const metrics = metricsQuery.data ?? [];
  const completedRuns = runs.filter((run) => run.status === "completed").length;
  const plannedRuns = runs.filter((run) => run.status === "planned").length;
  const score = bestScore(runs);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Training runs"
          value={`${runs.length}`}
          description="Tracked experiments"
          icon={FlaskConical}
        />
        <MetricCard
          title="Completed"
          value={`${completedRuns}`}
          description={`${plannedRuns} planned`}
          icon={CheckCircle2}
        />
        <MetricCard
          title="Best score"
          value={score === null ? "n/a" : score.toFixed(1)}
          description="Checkpoint selection metric"
          icon={Activity}
        />
        <MetricCard
          title="Latest training"
          value={formatDate(latestTrainingDate(runs))}
          description="Most recent dated run"
          icon={CalendarClock}
        />
      </div>

      <Tabs defaultValue="runs">
        <TabsList>
          <TabsTrigger value="runs">Runs</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>
        <TabsContent value="runs">
          <Card>
            <CardHeader>
              <CardTitle>Training history</CardTitle>
              <CardDescription>Experiment status, dataset version, checkpoint score, and lineage notes.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Experiment</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Dataset</TableHead>
                    <TableHead>Training date</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Checkpoint</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell>
                        <div className="font-medium">{run.experiment_name}</div>
                        <div className="max-w-md text-xs text-muted-foreground">{run.notes ?? "n/a"}</div>
                      </TableCell>
                      <TableCell>
                        <div>{run.model_name}</div>
                        <div className="text-xs text-muted-foreground">{run.version}</div>
                      </TableCell>
                      <TableCell>{statusBadge(run.status)}</TableCell>
                      <TableCell>{run.dataset_version ?? "Pending"}</TableCell>
                      <TableCell>{formatDate(run.training_date)}</TableCell>
                      <TableCell>{run.checkpoint_score?.toFixed(1) ?? "n/a"}</TableCell>
                      <TableCell className="max-w-xs truncate">
                        {run.checkpoint_path ?? "n/a"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="metrics">
          <div className="grid gap-4 xl:grid-cols-[1fr_1.1fr]">
            <Card>
              <CardHeader>
                <CardTitle>Metric history</CardTitle>
                <CardDescription>Recorded validation and benchmark signals over tracked runs.</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricHistoryChart metrics={metrics} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Metric records</CardTitle>
                <CardDescription>Raw history entries used by registry selection and reporting.</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>Split</TableHead>
                      <TableHead>Step</TableHead>
                      <TableHead>Quality</TableHead>
                      <TableHead>Cloud</TableHead>
                      <TableHead>Spectral</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {metrics.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell>
                          <div className="font-medium">{row.model_name}</div>
                          <div className="text-xs text-muted-foreground">{row.version}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{row.split}</Badge>
                        </TableCell>
                        <TableCell>{row.step ?? "n/a"}</TableCell>
                        <TableCell>
                          {asNumber(row.metrics.no_reference_quality_score)?.toFixed(1) ?? "n/a"}
                        </TableCell>
                        <TableCell>
                          {asNumber(row.metrics.cloud_reduction_score)?.toFixed(1) ?? "n/a"}
                        </TableCell>
                        <TableCell>
                          {asNumber(row.metrics.spectral_consistency_score)?.toFixed(1) ?? "n/a"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
