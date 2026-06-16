"use client";

/* eslint-disable @next/next/no-img-element */

import { Download, ExternalLink } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { resolveAssetUrl } from "@/lib/api";
import type { InferenceHistoryItem } from "@/store/inference-store";
import { useInferenceStore } from "@/store/inference-store";

type Product = {
  key: keyof Pick<
    InferenceHistoryItem,
    | "original_image_url"
    | "cloud_mask_url"
    | "shadow_mask_url"
    | "reconstructed_image_url"
    | "difference_map_url"
    | "attention_map_url"
    | "confidence_map_url"
  >;
  title: string;
  description: string;
  filename: string;
};

const products: Product[] = [
  {
    key: "original_image_url",
    title: "Original",
    description: "Uploaded image preview normalized for browser display.",
    filename: "original.png"
  },
  {
    key: "cloud_mask_url",
    title: "Cloud mask",
    description: "Brightness and saturation threshold mask after morphology.",
    filename: "cloud-mask.png"
  },
  {
    key: "shadow_mask_url",
    title: "Shadow mask",
    description: "Dark-region shadow candidates excluding cloud pixels.",
    filename: "shadow-mask.png"
  },
  {
    key: "reconstructed_image_url",
    title: "Reconstructed",
    description: "OpenCV Telea inpainting with contrast and sharpening.",
    filename: "reconstructed.png"
  },
  {
    key: "difference_map_url",
    title: "Difference map",
    description: "Absolute-difference heatmap between input and output.",
    filename: "difference-map.png"
  },
  {
    key: "attention_map_url",
    title: "Attention map",
    description: "Explainability overlay showing where the reconstruction pipeline focused.",
    filename: "attention-map.png"
  },
  {
    key: "confidence_map_url",
    title: "Confidence map",
    description: "Spatial confidence proxy for reconstructed and unchanged pixels.",
    filename: "confidence-map.png"
  }
];

type ResultImageGridProps = {
  mode?: "all" | "masks" | "reconstruction";
  run?: InferenceHistoryItem | null;
};

export function ResultImageGrid({ mode = "all", run }: ResultImageGridProps) {
  const hasMounted = useHasMounted();
  const currentRun = useInferenceStore((state) => state.currentRun);
  const selectedRun = run ?? (hasMounted ? currentRun : null);

  if (!selectedRun) {
    return (
      <EmptyState
        title="No inference result"
        description="Run a baseline reconstruction from the upload workspace to populate this view."
      />
    );
  }

  const visibleProducts = products.filter((product) => {
    if (mode === "masks") {
      return product.key === "cloud_mask_url" || product.key === "shadow_mask_url";
    }

    if (mode === "reconstruction") {
      return (
        product.key === "original_image_url" ||
        product.key === "reconstructed_image_url" ||
        product.key === "difference_map_url" ||
        product.key === "confidence_map_url"
      );
    }

    return true;
  });

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {visibleProducts.map((product) => {
        const productUrl = selectedRun[product.key];
        if (!productUrl) {
          return null;
        }

        const url = resolveAssetUrl(String(productUrl));

        return (
          <Card key={product.key}>
            <CardHeader className="space-y-1">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-base">{product.title}</CardTitle>
                  <CardDescription>{product.description}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button asChild size="icon" variant="outline" aria-label={`Open ${product.title}`}>
                    <a href={url} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button
                    asChild
                    size="icon"
                    variant="outline"
                    aria-label={`Download ${product.title}`}
                  >
                    <a href={url} download={product.filename}>
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="aspect-[4/3] overflow-hidden rounded-md border bg-muted/30">
                <img
                  alt={`${product.title} for ${selectedRun.file_name}`}
                  className="h-full w-full object-contain"
                  src={url}
                />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
