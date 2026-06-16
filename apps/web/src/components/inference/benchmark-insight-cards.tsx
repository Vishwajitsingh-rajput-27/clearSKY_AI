import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const modelInsights = [
  {
    title: "Traditional masking",
    badge: "baseline",
    detail: "Fast mask-only reference with no reconstruction fidelity claim."
  },
  {
    title: "OpenCV inpainting",
    badge: "cpu",
    detail: "Operational fallback used publicly when trained weights are unavailable."
  },
  {
    title: "Attention U-Net",
    badge: "research",
    detail: "Patch reconstruction architecture with explicit cloud-region attention."
  },
  {
    title: "Swin-UNet",
    badge: "research",
    detail: "Windowed transformer encoder for larger contextual reconstruction."
  },
  {
    title: "Multi-sensor fusion",
    badge: "fusion",
    detail: "LISS-IV reconstruction branch designed for S1, S2, DEM, and temporal inputs."
  }
];

export function BenchmarkInsightCards() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      {modelInsights.map((item) => (
        <Card key={item.title}>
          <CardHeader className="space-y-2">
            <div className="flex items-start justify-between gap-2">
              <CardTitle className="text-sm">{item.title}</CardTitle>
              <Badge variant="outline">{item.badge}</Badge>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">{item.detail}</CardContent>
        </Card>
      ))}
    </div>
  );
}
