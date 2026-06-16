"use client";

import { Download, History } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { resolveAssetUrl } from "@/lib/api";
import { useInferenceStore } from "@/store/inference-store";

function formatBytes(bytes: number): string {
  if (!bytes) {
    return "-";
  }

  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

export function InferenceHistoryTable() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const history = useInferenceStore((state) => state.history);
  const selectRun = useInferenceStore((state) => state.selectRun);
  const selectedRun = hasMounted ? currentRun : null;
  const selectedHistory = hasMounted ? history : [];

  if (selectedHistory.length === 0) {
    return (
      <div className="flex min-h-40 flex-col items-center justify-center rounded-md border border-dashed bg-muted/20 p-6 text-center">
        <History className="mb-3 h-6 w-6 text-muted-foreground" aria-hidden="true" />
        <h3 className="text-sm font-medium">No project history</h3>
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">
          Completed inference runs will appear here with metrics and output links.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Run</TableHead>
          <TableHead>Model</TableHead>
          <TableHead>Cloud</TableHead>
          <TableHead>Shadow</TableHead>
          <TableHead>Quality</TableHead>
          <TableHead>Runtime</TableHead>
          <TableHead>Size</TableHead>
          <TableHead className="text-right">Output</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {selectedHistory.map((run) => {
          const active = selectedRun?.id === run.id;

          return (
            <TableRow
              className="cursor-pointer data-[state=selected]:bg-muted"
              key={run.id}
              onClick={() => selectRun(run.id)}
              data-state={active ? "selected" : undefined}
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="font-medium">{run.file_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(run.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  <Badge variant="outline">{run.requested_model}</Badge>
                  {run.fallback_used ? <Badge variant="secondary">fallback</Badge> : null}
                </div>
              </TableCell>
              <TableCell>{run.cloud_coverage_percent.toFixed(2)}%</TableCell>
              <TableCell>{run.shadow_coverage_percent.toFixed(2)}%</TableCell>
              <TableCell>{run.quality_score.toFixed(1)}</TableCell>
              <TableCell>{run.processing_time_seconds.toFixed(2)}s</TableCell>
              <TableCell className="text-muted-foreground">{formatBytes(run.file_size_bytes)}</TableCell>
              <TableCell className="text-right">
                <Button
                  asChild
                  size="icon"
                  variant="outline"
                  aria-label={`Download reconstruction for ${run.file_name}`}
                  onClick={(event) => event.stopPropagation()}
                >
                  <a href={resolveAssetUrl(run.reconstructed_image_url)} download="reconstructed.png">
                    <Download className="h-4 w-4" />
                  </a>
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
