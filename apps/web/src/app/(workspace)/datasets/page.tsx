import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { SceneTable } from "@/components/datasets/scene-table";
import { InferenceHistoryTable } from "@/components/inference/history-table";
import { GeospatialMetadataCard } from "@/components/inference/geospatial-metadata-card";
import { ResultImageGrid } from "@/components/inference/result-image-grid";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DatasetExplorerPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Data management"
        title="Dataset Explorer"
        description="Inspect uploaded scenes, benchmark samples, auxiliary availability, and processing status."
      />

      <Tabs defaultValue="scenes">
        <TabsList>
          <TabsTrigger value="scenes">Scenes</TabsTrigger>
          <TabsTrigger value="auxiliary">Auxiliary</TabsTrigger>
          <TabsTrigger value="exports">Exports</TabsTrigger>
        </TabsList>
        <TabsContent value="scenes">
          <Card>
            <CardHeader>
              <CardTitle>Scene registry</CardTitle>
              <CardDescription>Click a scene row to select it for downstream pages.</CardDescription>
            </CardHeader>
            <CardContent>
              <SceneTable />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="auxiliary">
          <EmptyState
            title="No auxiliary catalog connected"
            description="Sentinel-1, Sentinel-2, DEM, and temporal inputs are supported in training-ready manifests; automated catalog discovery remains future work."
            action="Review methodology"
          />
        </TabsContent>
        <TabsContent value="exports">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Inference history</CardTitle>
                <CardDescription>Completed runs and downloadable reconstruction outputs.</CardDescription>
              </CardHeader>
              <CardContent>
                <InferenceHistoryTable />
              </CardContent>
            </Card>
            <GeospatialMetadataCard />
            <ResultImageGrid />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
