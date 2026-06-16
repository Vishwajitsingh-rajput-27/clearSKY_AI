"use client";

import { useQuery } from "@tanstack/react-query";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { apiClient, resolveAssetUrl } from "@/lib/api";

export function StoredBenchmarkResults() {
  const query = useQuery({
    queryKey: ["benchmarks"],
    queryFn: apiClient.benchmarks
  });

  if (query.isLoading) {
    return <Skeleton className="h-44 w-full" />;
  }

  if (query.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Benchmark history unavailable</AlertTitle>
        <AlertDescription>
          {query.error instanceof Error ? query.error.message : "Could not load benchmarks."}
        </AlertDescription>
      </Alert>
    );
  }

  const rows = query.data ?? [];

  if (rows.length === 0) {
    return (
      <Alert>
        <AlertTitle>No stored benchmarks</AlertTitle>
        <AlertDescription>Run inference once to persist benchmark metrics.</AlertDescription>
      </Alert>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Run</TableHead>
          <TableHead>Mode</TableHead>
          <TableHead>Used model</TableHead>
          <TableHead>SSIM</TableHead>
          <TableHead>Spectral</TableHead>
          <TableHead>Quality</TableHead>
          <TableHead>Report</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.id}>
            <TableCell className="font-medium">{row.inference_run_id.slice(0, 8)}</TableCell>
            <TableCell>
              <Badge variant="outline">{row.metric_mode}</Badge>
            </TableCell>
            <TableCell>{row.used_model}</TableCell>
            <TableCell>{row.metrics.ssim?.toFixed(4) ?? "n/a"}</TableCell>
            <TableCell>{row.metrics.spectral_consistency_score?.toFixed(1) ?? "n/a"}</TableCell>
            <TableCell>{row.metrics.no_reference_quality_score?.toFixed(1) ?? "n/a"}</TableCell>
            <TableCell>
              {row.report_json_url ? (
                <Button variant="ghost" size="sm" asChild>
                  <a href={resolveAssetUrl(row.report_json_url)} target="_blank" rel="noreferrer">
                    JSON
                  </a>
                </Button>
              ) : (
                "n/a"
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
