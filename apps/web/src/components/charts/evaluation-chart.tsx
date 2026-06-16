"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { ChartFrame } from "@/components/charts/chart-frame";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { reconstructionSeries } from "@/lib/mock-data";

export function EvaluationChart() {
  const hasMounted = useHasMounted();

  if (!hasMounted) {
    return <div className="h-72 w-full rounded-md bg-muted/20" />;
  }

  return (
    <ChartFrame>
      {({ width, height }) => (
        <LineChart
          data={reconstructionSeries}
          height={height}
          margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
          width={width}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="stage" tickLine={false} />
          <YAxis tickLine={false} />
          <Tooltip />
          <Line dataKey="sam" name="SAM" stroke="#2563eb" strokeWidth={2} />
          <Line dataKey="ssim" name="SSIM" stroke="#16a34a" strokeWidth={2} />
          <Line dataKey="ndvi" name="NDVI delta" stroke="#dc2626" strokeWidth={2} />
        </LineChart>
      )}
    </ChartFrame>
  );
}
