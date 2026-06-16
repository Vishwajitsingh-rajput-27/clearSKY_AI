"use client";

import { Download, Map } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { resolveAssetUrl } from "@/lib/api";
import type { InferenceHistoryItem } from "@/store/inference-store";
import { useInferenceStore } from "@/store/inference-store";

type GeospatialMetadataCardProps = {
  run?: InferenceHistoryItem | null;
};

export function GeospatialMetadataCard({ run }: GeospatialMetadataCardProps) {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = run ?? (hasMounted ? currentRun : null);
  const metadata = selectedRun?.metadata;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Geospatial metadata</CardTitle>
            <CardDescription>Raster identity, CRS, size, and export status.</CardDescription>
          </div>
          <Map className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!metadata ? (
          <div className="rounded-md border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
            Metadata will appear after an inference run completes.
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <MetadataItem label="File type" value={metadata.file_type ?? "unknown"} />
              <MetadataItem label="Driver" value={metadata.driver ?? metadata.reader ?? "unknown"} />
              <MetadataItem label="Size" value={formatSize(metadata.width, metadata.height)} />
              <MetadataItem label="Bands" value={String(metadata.band_count ?? "-")} />
              <MetadataItem label="CRS" value={metadata.crs ?? "not available"} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant={metadata.is_geospatial ? "secondary" : "outline"}>
                {metadata.is_geospatial ? "geospatial" : "visual image"}
              </Badge>
              {metadata.dtype ? <Badge variant="outline">{metadata.dtype}</Badge> : null}
              {selectedRun.metrics.tile_count ? (
                <Badge variant="outline">{selectedRun.metrics.tile_count} tile windows</Badge>
              ) : null}
            </div>
            <Separator />
            <div className="flex flex-wrap gap-2">
              {selectedRun.analysis_geotiff_url ? (
                <Button asChild variant="outline">
                  <a href={resolveAssetUrl(selectedRun.analysis_geotiff_url)} download>
                    <Download className="mr-2 h-4 w-4" />
                    GeoTIFF
                  </a>
                </Button>
              ) : null}
              {selectedRun.qgis_manifest_url ? (
                <Button asChild variant="outline">
                  <a href={resolveAssetUrl(selectedRun.qgis_manifest_url)} download>
                    <Download className="mr-2 h-4 w-4" />
                    QGIS manifest
                  </a>
                </Button>
              ) : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function MetadataItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-sm font-medium" title={value}>
        {value}
      </div>
    </div>
  );
}

function formatSize(width?: number | null, height?: number | null): string {
  if (!width || !height) {
    return "-";
  }

  return `${width} x ${height}`;
}
