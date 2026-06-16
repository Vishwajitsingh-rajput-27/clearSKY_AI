import { ApiHealthCard } from "@/components/dashboard/api-health-card";
import { DemoRunButton } from "@/components/demo/demo-run-button";
import { DashboardDemoState } from "@/components/demo/demo-mode-card";
import { SceneTable } from "@/components/datasets/scene-table";
import { InferenceHistoryTable } from "@/components/inference/history-table";
import { InferenceMetricsPanel } from "@/components/inference/metrics-panel";
import { PageHeader } from "@/components/shared/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operational overview"
        title="Dashboard"
        description="Monitor API health, inference outputs, project history, and dataset readiness from one research console."
      />

      <div className="flex justify-end">
        <DemoRunButton variant="outline" size="sm" />
      </div>

      <DashboardDemoState />

      <InferenceMetricsPanel compact />

      <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <ApiHealthCard />
        <Card>
          <CardHeader>
            <CardTitle>Module readiness</CardTitle>
            <CardDescription>Frontend wiring against backend core and future AI modules.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              ["Backend core", 100],
              ["Frontend core", 100],
              ["Baseline inference", 100],
              ["Geospatial metadata extraction", 20]
            ].map(([label, value]) => (
              <div className="space-y-2" key={label}>
                <div className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="text-muted-foreground">{value}%</span>
                </div>
                <Progress value={Number(value)} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project history</CardTitle>
          <CardDescription>Completed inference runs in the current browser workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <InferenceHistoryTable />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent scenes</CardTitle>
          <CardDescription>Live backend records appear here when available, otherwise demo data is shown.</CardDescription>
        </CardHeader>
        <CardContent>
          <SceneTable />
        </CardContent>
      </Card>
    </div>
  );
}
