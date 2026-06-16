"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { ChartFrame } from "@/components/charts/chart-frame";
import { EmptyState } from "@/components/shared/empty-state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useHasMounted } from "@/hooks/use-has-mounted";
import type { InferenceHistoryItem } from "@/store/inference-store";
import { useInferenceStore } from "@/store/inference-store";

function buildCoverageData(run: InferenceHistoryItem) {
  return [
    {
      name: "Cloud",
      value: Number(run.cloud_coverage_percent.toFixed(2))
    },
    {
      name: "Shadow",
      value: Number(run.shadow_coverage_percent.toFixed(2))
    },
    {
      name: "Mask",
      value: Number(run.metrics.mask_coverage_percent.toFixed(2))
    },
    {
      name: "Difference",
      value: Number(Math.min(100, run.metrics.mean_absolute_difference).toFixed(2))
    }
  ];
}

function buildScientificData(run: InferenceHistoryItem) {
  const evaluation = run.evaluation;

  return [
    {
      name: "SSIM",
      value: evaluation?.ssim ? Number((evaluation.ssim * 100).toFixed(2)) : 0
    },
    {
      name: "Spectral",
      value: Number((evaluation?.spectral_consistency_score ?? 0).toFixed(2))
    },
    {
      name: "Cloud reduction",
      value: Number((evaluation?.cloud_reduction_score ?? 0).toFixed(2))
    },
    {
      name: "No-ref quality",
      value: Number((evaluation?.no_reference_quality_score ?? 0).toFixed(2))
    }
  ];
}

function buildHistoryData(history: InferenceHistoryItem[]) {
  return history
    .slice()
    .reverse()
    .map((run, index) => ({
      name: `Run ${index + 1}`,
      quality: Number(run.quality_score.toFixed(2)),
      cloud: Number(run.cloud_coverage_percent.toFixed(2)),
      shadow: Number(run.shadow_coverage_percent.toFixed(2))
    }));
}

export function LiveEvaluationChart() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const history = useInferenceStore((state) => state.history);
  const selectedRun = hasMounted ? currentRun : null;
  const selectedHistory = hasMounted ? history : [];

  if (!selectedRun) {
    return (
      <EmptyState
        title="No evaluation metrics"
        description="Metrics are generated automatically after the baseline inference pipeline completes."
      />
    );
  }

  return (
    <Tabs defaultValue="current">
      <TabsList>
        <TabsTrigger value="current">Current run</TabsTrigger>
        <TabsTrigger value="scientific">Scientific</TabsTrigger>
        <TabsTrigger value="history">History</TabsTrigger>
      </TabsList>
      <TabsContent value="current">
        <ChartFrame>
          {({ width, height }) => (
            <BarChart
              data={buildCoverageData(selectedRun)}
              height={height}
              margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
              width={width}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tickLine={false} />
              <YAxis tickLine={false} domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="value" name="Percent / intensity" fill="#334155" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ChartFrame>
      </TabsContent>
      <TabsContent value="scientific">
        <ChartFrame>
          {({ width, height }) => (
            <BarChart
              data={buildScientificData(selectedRun)}
              height={height}
              margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
              width={width}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tickLine={false} />
              <YAxis tickLine={false} domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="value" name="Score" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ChartFrame>
      </TabsContent>
      <TabsContent value="history">
        <ChartFrame>
          {({ width, height }) => (
            <LineChart
              data={buildHistoryData(selectedHistory)}
              height={height}
              margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
              width={width}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tickLine={false} />
              <YAxis tickLine={false} domain={[0, 100]} />
              <Tooltip />
              <Line dataKey="quality" name="Quality" stroke="#2563eb" strokeWidth={2} />
              <Line dataKey="cloud" name="Cloud" stroke="#64748b" strokeWidth={2} />
              <Line dataKey="shadow" name="Shadow" stroke="#16a34a" strokeWidth={2} />
            </LineChart>
          )}
        </ChartFrame>
      </TabsContent>
    </Tabs>
  );
}
