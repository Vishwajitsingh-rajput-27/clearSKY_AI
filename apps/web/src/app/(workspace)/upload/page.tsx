import { InferenceHistoryTable } from "@/components/inference/history-table";
import { GeospatialMetadataCard } from "@/components/inference/geospatial-metadata-card";
import { InferenceMetricsPanel } from "@/components/inference/metrics-panel";
import { ResultImageGrid } from "@/components/inference/result-image-grid";
import { UploadForm } from "@/components/upload/upload-form";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Scene ingest"
        title="Upload"
        description="Upload a cloudy image, run the CPU-safe baseline pipeline, and inspect generated products."
      />
      <UploadForm />
      <InferenceMetricsPanel />
      <GeospatialMetadataCard />
      <ResultImageGrid />
      <Card>
        <CardHeader>
          <CardTitle>Project history</CardTitle>
          <CardDescription>Recent inference runs stored in the current browser workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <InferenceHistoryTable />
        </CardContent>
      </Card>
    </div>
  );
}
