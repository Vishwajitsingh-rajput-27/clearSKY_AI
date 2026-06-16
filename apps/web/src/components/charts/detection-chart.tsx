"use client";

import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { ChartFrame } from "@/components/charts/chart-frame";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { detectionClasses } from "@/lib/mock-data";
import { useInferenceStore } from "@/store/inference-store";

export function DetectionChart() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = hasMounted ? currentRun : null;
  const liveClasses = selectedRun
    ? [
        {
          name: "Cloud",
          value: Number(selectedRun.cloud_coverage_percent.toFixed(2))
        },
        {
          name: "Shadow",
          value: Number(selectedRun.shadow_coverage_percent.toFixed(2))
        },
        {
          name: "Clear",
          value: Number(
            Math.max(0, 100 - selectedRun.metrics.mask_coverage_percent).toFixed(2)
          )
        }
      ]
    : detectionClasses;

  if (!hasMounted) {
    return <div className="h-72 w-full rounded-md bg-muted/20" />;
  }

  return (
    <ChartFrame>
      {({ width, height }) => (
        <BarChart
          data={liveClasses}
          height={height}
          margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
          width={width}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tickLine={false} />
          <YAxis tickLine={false} />
          <Tooltip />
          <Bar dataKey="value" name="Pixel share" fill="#334155" radius={[4, 4, 0, 0]} />
        </BarChart>
      )}
    </ChartFrame>
  );
}
