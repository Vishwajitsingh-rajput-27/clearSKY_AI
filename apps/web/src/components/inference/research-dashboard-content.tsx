"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts";
import { Download, FileArchive, FileText, FlaskConical, Layers, Trophy } from "lucide-react";
import { ChartFrame } from "@/components/charts/chart-frame";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { MetricCard } from "@/components/shared/metric-card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import {
  apiClient,
  resolveAssetUrl,
  type ResearchDashboardSummaryResponse,
  type ResearchExportResponse,
  type ResearchMetricComparisonRow,
  type ResearchReportType
} from "@/lib/api";

const reportTypes: Array<{ label: string; value: ResearchReportType }> = [
  { label: "Complete research report", value: "complete_research_report" },
  { label: "Experiment report", value: "experiment_report" },
  { label: "Benchmark report", value: "benchmark_report" },
  { label: "Metrics comparison", value: "metrics_comparison" }
];

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

function formatScore(value?: number | null) {
  return typeof value === "number" ? value.toFixed(1) : "n/a";
}

function sourceBadge(source: string) {
  if (source === "benchmark") {
    return <Badge variant="secondary">benchmark</Badge>;
  }

  return <Badge variant="outline">{source.replace("_", " ")}</Badge>;
}

function chartRows(summary: ResearchDashboardSummaryResponse) {
  return summary.chart_series.map((row) => ({
    ...row,
    label: row.model.length > 22 ? `${row.model.slice(0, 19)}...` : row.model,
    ssim_scaled: row.ssim <= 1 ? row.ssim * 100 : row.ssim
  }));
}

function QualityChart({ summary }: { summary: ResearchDashboardSummaryResponse }) {
  const hasMounted = useHasMounted();
  const rows = chartRows(summary);

  if (!hasMounted) {
    return <div className="h-72 w-full rounded-md bg-muted/20" />;
  }

  return (
    <ChartFrame>
      {({ width, height }) => (
        <BarChart
          data={rows}
          height={height}
          margin={{ left: 8, right: 12, top: 8, bottom: 24 }}
          width={width}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" interval={0} tickLine={false} />
          <YAxis domain={[0, 100]} tickLine={false} />
          <Tooltip />
          <Bar dataKey="quality" fill="#2563eb" name="Quality" radius={[4, 4, 0, 0]} />
        </BarChart>
      )}
    </ChartFrame>
  );
}

function MetricBalanceChart({ summary }: { summary: ResearchDashboardSummaryResponse }) {
  const hasMounted = useHasMounted();
  const rows = chartRows(summary).slice(0, 8);

  if (!hasMounted) {
    return <div className="h-72 w-full rounded-md bg-muted/20" />;
  }

  return (
    <ChartFrame>
      {({ width, height }) => (
        <BarChart
          data={rows}
          height={height}
          margin={{ left: 8, right: 12, top: 8, bottom: 24 }}
          width={width}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" interval={0} tickLine={false} />
          <YAxis domain={[0, 100]} tickLine={false} />
          <Tooltip />
          <Legend />
          <Bar dataKey="spectral" fill="#16a34a" name="Spectral" radius={[3, 3, 0, 0]} />
          <Bar dataKey="cloud_reduction" fill="#dc2626" name="Cloud reduction" radius={[3, 3, 0, 0]} />
          <Bar dataKey="ssim_scaled" fill="#7c3aed" name="SSIM x100" radius={[3, 3, 0, 0]} />
        </BarChart>
      )}
    </ChartFrame>
  );
}

function ExportPanel({
  lastExport,
  onExport
}: {
  lastExport: ResearchExportResponse | null;
  onExport: (fullPackage: boolean) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Research exports</CardTitle>
        <CardDescription>Generate experiment, benchmark, PDF, CSV, and metrics comparison artifacts.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <Button onClick={() => onExport(false)}>
            <FileText className="mr-2 h-4 w-4" />
            PDF + CSV
          </Button>
          <Button variant="outline" onClick={() => onExport(true)}>
            <FileArchive className="mr-2 h-4 w-4" />
            Full package
          </Button>
        </div>

        {lastExport ? (
          <div className="space-y-3 rounded-md border p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium">Latest export</p>
                <p className="text-xs text-muted-foreground">
                  {lastExport.report_type.replaceAll("_", " ")} | {formatDate(lastExport.generated_at)}
                </p>
              </div>
              <Badge variant="secondary">{lastExport.files.length} files</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {lastExport.files.map((file) => (
                <Button asChild key={file.storage_url} size="sm" variant="outline">
                  <a href={resolveAssetUrl(file.storage_url)} download>
                    <Download className="mr-2 h-4 w-4" />
                    {file.format.toUpperCase()}
                  </a>
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <Alert>
            <AlertTitle>No export generated in this session</AlertTitle>
            <AlertDescription>Export files are persisted as platform assets after generation.</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

function ComparisonTable({ rows }: { rows: ResearchMetricComparisonRow[] }) {
  const topRows = rows
    .slice()
    .sort((a, b) => (b.quality_score ?? 0) - (a.quality_score ?? 0))
    .slice(0, 12);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Source</TableHead>
          <TableHead>Model</TableHead>
          <TableHead>Dataset</TableHead>
          <TableHead>Quality</TableHead>
          <TableHead>Spectral</TableHead>
          <TableHead>Cloud</TableHead>
          <TableHead>SSIM</TableHead>
          <TableHead>Runtime</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {topRows.map((row, index) => (
          <TableRow key={`${row.source}-${row.model_name}-${index}`}>
            <TableCell>{sourceBadge(row.source)}</TableCell>
            <TableCell>
              <div className="font-medium">{row.model_name}</div>
              <div className="text-xs text-muted-foreground">{row.version ?? row.status ?? "n/a"}</div>
            </TableCell>
            <TableCell>{row.dataset_version ?? "n/a"}</TableCell>
            <TableCell>{formatScore(row.quality_score)}</TableCell>
            <TableCell>{formatScore(row.spectral_consistency_score)}</TableCell>
            <TableCell>{formatScore(row.cloud_reduction_score)}</TableCell>
            <TableCell>{row.ssim === null || row.ssim === undefined ? "n/a" : row.ssim.toFixed(3)}</TableCell>
            <TableCell>{row.runtime_seconds ? `${row.runtime_seconds.toFixed(2)}s` : "n/a"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function ResearchDashboardContent() {
  const [reportType, setReportType] = useState<ResearchReportType>("complete_research_report");
  const [lastExport, setLastExport] = useState<ResearchExportResponse | null>(null);
  const summaryQuery = useQuery({
    queryKey: ["research", "summary"],
    queryFn: apiClient.researchSummary
  });
  const exportMutation = useMutation({
    mutationFn: apiClient.exportResearchReport,
    onSuccess: (data) => {
      setLastExport(data);
    }
  });

  if (summaryQuery.isLoading) {
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

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Research dashboard unavailable</AlertTitle>
        <AlertDescription>
          {summaryQuery.error instanceof Error ? summaryQuery.error.message : "Could not load research data."}
        </AlertDescription>
      </Alert>
    );
  }

  const summary = summaryQuery.data;

  const runExport = (fullPackage: boolean) => {
    exportMutation.mutate({
      report_type: reportType,
      formats: fullPackage ? ["pdf", "csv", "json", "markdown"] : ["pdf", "csv"]
    });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Models"
          value={`${summary.registered_models}`}
          description={`${summary.active_models} active`}
          icon={Layers}
        />
        <MetricCard
          title="Experiments"
          value={`${summary.experiment_count}`}
          description="Tracked training runs"
          icon={FlaskConical}
        />
        <MetricCard
          title="Benchmarks"
          value={`${summary.benchmark_count}`}
          description="Stored benchmark records"
          icon={FileText}
        />
        <MetricCard
          title="Best score"
          value={formatScore(summary.best_quality_score)}
          description={summary.best_model_name ?? "No model selected"}
          icon={Trophy}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_22rem]">
        <Card>
          <CardHeader>
            <CardTitle>Publication chart: model quality</CardTitle>
            <CardDescription>Highest recorded quality signal per model across registry, experiments, and benchmarks.</CardDescription>
          </CardHeader>
          <CardContent>
            <QualityChart summary={summary} />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Report scope</CardTitle>
              <CardDescription>Select the report family before exporting artifacts.</CardDescription>
            </CardHeader>
            <CardContent>
              <Select value={reportType} onValueChange={(value) => setReportType(value as ResearchReportType)}>
                <SelectTrigger>
                  <SelectValue placeholder="Report type" />
                </SelectTrigger>
                <SelectContent>
                  {reportTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {exportMutation.isError ? (
                <Alert className="mt-4" variant="destructive">
                  <AlertTitle>Export failed</AlertTitle>
                  <AlertDescription>
                    {exportMutation.error instanceof Error
                      ? exportMutation.error.message
                      : "Could not generate research export."}
                  </AlertDescription>
                </Alert>
              ) : null}
              {exportMutation.isPending ? (
                <p className="mt-3 text-sm text-muted-foreground">Generating export files...</p>
              ) : null}
            </CardContent>
          </Card>

          <ExportPanel lastExport={lastExport} onExport={runExport} />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Publication chart: metric balance</CardTitle>
          <CardDescription>Spectral preservation, cloud reduction, and SSIM are shown on a shared 0-100 axis.</CardDescription>
        </CardHeader>
        <CardContent>
          <MetricBalanceChart summary={summary} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Metrics comparison report</CardTitle>
          <CardDescription>Top comparison rows used for CSV and PDF research exports.</CardDescription>
        </CardHeader>
        <CardContent>
          <ComparisonTable rows={summary.model_comparison} />
        </CardContent>
      </Card>
    </div>
  );
}
