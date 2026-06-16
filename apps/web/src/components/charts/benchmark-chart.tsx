"use client";

import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { ChartFrame } from "@/components/charts/chart-frame";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { benchmarkRows } from "@/lib/mock-data";
import { useInferenceStore } from "@/store/inference-store";

export function BenchmarkChart() {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const rows = hasMounted ? currentRun?.benchmark_rows ?? [] : [];
  const data = rows.length
    ? rows.map((row) => ({
        model: row.model_name,
        ssim: Number(row.ssim.toFixed(3)),
        spectral: Number((row.spectral_consistency_score / 100).toFixed(3)),
        cloud: Number((row.cloud_reduction_score / 100).toFixed(3))
      }))
    : benchmarkRows.map((row) => ({
        model: row.model,
        ssim: row.ssim,
        spectral: 0,
        cloud: 0
      }));

  if (!hasMounted) {
    return <div className="h-72 w-full rounded-md bg-muted/20" />;
  }

  return (
    <ChartFrame>
      {({ width, height }) => (
        <BarChart
          data={data}
          height={height}
          margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
          width={width}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="model" tickLine={false} />
          <YAxis tickLine={false} />
          <Tooltip />
          <Bar dataKey="ssim" name="SSIM" fill="#475569" radius={[4, 4, 0, 0]} />
          {rows.length ? (
            <>
              <Bar dataKey="spectral" name="Spectral score" fill="#0f766e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="cloud" name="Cloud reduction" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </>
          ) : null}
        </BarChart>
      )}
    </ChartFrame>
  );
}
