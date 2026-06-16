"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { benchmarkRows } from "@/lib/mock-data";
import { useInferenceStore } from "@/store/inference-store";

export function LiveBenchmarkTable() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const rows = hasMounted ? currentRun?.benchmark_rows ?? [] : [];

  if (rows.length === 0) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model</TableHead>
            <TableHead>Inputs</TableHead>
            <TableHead>SAM</TableHead>
            <TableHead>SSIM</TableHead>
            <TableHead>Runtime</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {benchmarkRows.map((row) => (
            <TableRow key={row.model}>
              <TableCell className="font-medium">{row.model}</TableCell>
              <TableCell>
                <Badge variant="outline">{row.inputs}</Badge>
              </TableCell>
              <TableCell>{row.sam}</TableCell>
              <TableCell>{row.ssim}</TableCell>
              <TableCell>{row.runtime}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Model</TableHead>
          <TableHead>Inputs</TableHead>
          <TableHead>Quality</TableHead>
          <TableHead>Spectral</TableHead>
          <TableHead>Cloud reduction</TableHead>
          <TableHead>SSIM</TableHead>
          <TableHead>Runtime</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.model_key}>
            <TableCell className="font-medium">
              <div className="flex flex-wrap items-center gap-2">
                {row.model_name}
                {row.requested ? <Badge variant="outline">requested</Badge> : null}
                {row.used ? <Badge variant="secondary">used</Badge> : null}
              </div>
            </TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                <Badge variant="outline">{row.inputs}</Badge>
                {row.fallback_used ? <Badge variant="secondary">fallback</Badge> : null}
                {row.simulated ? <Badge>research estimate</Badge> : null}
              </div>
            </TableCell>
            <TableCell>{row.quality_score.toFixed(1)}</TableCell>
            <TableCell>{row.spectral_consistency_score.toFixed(1)}</TableCell>
            <TableCell>{row.cloud_reduction_score.toFixed(1)}</TableCell>
            <TableCell>{row.ssim.toFixed(4)}</TableCell>
            <TableCell>{row.runtime_seconds.toFixed(2)}s</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
