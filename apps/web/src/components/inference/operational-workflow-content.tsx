"use client";

import { BrainCircuit, CheckCircle2, Database, Layers, Map, Satellite, ShieldCheck } from "lucide-react";
import { ExplainabilityPanel } from "@/components/inference/explainability-panel";
import { TimeSeriesViewer } from "@/components/inference/time-series-viewer";
import { MetricCard } from "@/components/shared/metric-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { useInferenceStore } from "@/store/inference-store";

const workflowSteps = [
  {
    title: "Scene intake",
    description: "Upload validation, safe filenames, metadata extraction, and storage accounting.",
    icon: Database
  },
  {
    title: "Mask generation",
    description: "Cloud and shadow masks are produced with morphology-cleaned CPU baselines.",
    icon: Satellite
  },
  {
    title: "Reconstruction",
    description: "OpenCV fallback or registered PyTorch weights reconstruct invalid pixels.",
    icon: BrainCircuit
  },
  {
    title: "Explainability",
    description: "Attention and confidence maps expose where the pipeline focused and where QA is needed.",
    icon: ShieldCheck
  },
  {
    title: "Fusion decision",
    description: "Recommendations identify Sentinel-1, Sentinel-2, temporal, or DEM improvements.",
    icon: Layers
  },
  {
    title: "Operational export",
    description: "GeoTIFF, QGIS manifests, reports, and research exports support downstream review.",
    icon: Map
  }
];

export function OperationalWorkflowContent() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const history = useInferenceStore((state) => state.history);
  const selectedRun = hasMounted ? currentRun : null;
  const confidence =
    selectedRun?.reconstruction_confidence_score ??
    selectedRun?.metrics.reconstruction_confidence_score ??
    null;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Workflow runs"
          value={`${hasMounted ? history.length : 0}`}
          description="Browser project history"
          icon={CheckCircle2}
        />
        <MetricCard
          title="Confidence"
          value={confidence === null ? "n/a" : confidence.toFixed(1)}
          description="Current reconstruction"
          icon={ShieldCheck}
        />
        <MetricCard
          title="Recommendations"
          value={`${selectedRun?.recommendations?.length ?? 0}`}
          description="AI next actions"
          icon={BrainCircuit}
        />
        <MetricCard
          title="Fusion readiness"
          value={selectedRun?.metadata?.is_geospatial ? "High" : "Basic"}
          description="Depends on input metadata"
          icon={Layers}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Operational workflow</CardTitle>
          <CardDescription>Production path from public upload to explainable reconstruction and export.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {workflowSteps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div className="rounded-md border p-4" key={step.title}>
                  <div className="flex items-center justify-between gap-3">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <Badge variant="outline">Step {index + 1}</Badge>
                  </div>
                  <h3 className="mt-3 text-sm font-medium">{step.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{step.description}</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="explainability">
        <TabsList>
          <TabsTrigger value="explainability">Explainability</TabsTrigger>
          <TabsTrigger value="time-series">Time series</TabsTrigger>
        </TabsList>
        <TabsContent value="explainability">
          <ExplainabilityPanel />
        </TabsContent>
        <TabsContent value="time-series">
          <TimeSeriesViewer />
        </TabsContent>
      </Tabs>
    </div>
  );
}
