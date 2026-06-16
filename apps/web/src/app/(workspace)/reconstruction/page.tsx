import { LiveEvaluationChart } from "@/components/inference/evaluation-chart";
import { InferenceMetricsPanel } from "@/components/inference/metrics-panel";
import { ResultImageGrid } from "@/components/inference/result-image-grid";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ReconstructionPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Cloud-free output"
        title="Reconstruction"
        description="Inspect reconstructed imagery, input comparison, and baseline quality diagnostics."
      />

      <InferenceMetricsPanel compact />

      <Tabs defaultValue="scientific">
        <TabsList>
          <TabsTrigger value="scientific">Scientific</TabsTrigger>
          <TabsTrigger value="visual">Visual</TabsTrigger>
          <TabsTrigger value="uncertainty">Uncertainty</TabsTrigger>
        </TabsList>
        <TabsContent className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]" value="scientific">
          <div className="lg:col-span-2">
            <ResultImageGrid mode="reconstruction" />
          </div>
        </TabsContent>
        <TabsContent className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]" value="visual">
          <div className="lg:col-span-2">
            <ResultImageGrid mode="all" />
          </div>
        </TabsContent>
        <TabsContent value="uncertainty">
          <Card>
            <CardHeader>
              <CardTitle>Fusion readiness</CardTitle>
              <CardDescription>Auxiliary inputs reserved for later fusion modules.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                ["Temporal stack", 80],
                ["Sentinel-1 SAR", 65],
                ["Sentinel-2 optical", 70],
                ["DEM terrain features", 90]
              ].map(([label, value]) => (
                <div className="space-y-2" key={label}>
                  <div className="flex justify-between text-sm">
                    <span>{label}</span>
                    <Badge variant="outline">{value}%</Badge>
                  </div>
                  <Progress value={Number(value)} />
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Quality trend</CardTitle>
              <CardDescription>Live coverage, difference, and quality metrics.</CardDescription>
            </CardHeader>
            <CardContent>
              <LiveEvaluationChart />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
