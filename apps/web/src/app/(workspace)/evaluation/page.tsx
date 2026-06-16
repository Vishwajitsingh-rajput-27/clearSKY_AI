import { LiveEvaluationChart } from "@/components/inference/evaluation-chart";
import { EvaluationExplanationCards } from "@/components/inference/evaluation-explanation-cards";
import { EvaluationMetricCards } from "@/components/inference/evaluation-metric-cards";
import { InferenceMetricsPanel } from "@/components/inference/metrics-panel";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function EvaluationPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Quality control"
        title="Evaluation"
        description="Track baseline coverage, difference, runtime, and quality metrics for each inference run."
      />

      <InferenceMetricsPanel />
      <EvaluationMetricCards />

      <Card>
        <CardHeader>
          <CardTitle>Evaluation charts</CardTitle>
          <CardDescription>Coverage, difference, quality, and run-history trends.</CardDescription>
        </CardHeader>
        <CardContent>
          <LiveEvaluationChart />
        </CardContent>
      </Card>

      <EvaluationExplanationCards />
    </div>
  );
}
