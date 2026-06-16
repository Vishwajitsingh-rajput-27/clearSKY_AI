"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Cpu, FileUp, Info, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useHasMounted } from "@/hooks/use-has-mounted";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { useInferenceStore } from "@/store/inference-store";

const uploadSchema = z.object({
  acquisitionType: z.enum(["single", "temporal", "benchmark"]),
  processingMode: z.enum(["scientific", "visual"]),
  requestedModel: z.enum([
    "opencv-baseline",
    "swin-unet",
    "attention-unet",
    "multi-sensor-fusion"
  ]),
  projectId: z.string().optional(),
  file: z
    .any()
    .refine((files) => files?.length === 1, "Select one PNG, JPG, TIFF, GeoTIFF, or JP2 image."),
  targetFile: z.any().optional()
});

type UploadFormValues = z.infer<typeof uploadSchema>;

type RunInferenceVariables = {
  file: File;
  targetFile?: File | null;
  requestedModel: UploadFormValues["requestedModel"];
  projectId?: string | null;
};

export function UploadForm() {
  const hasMounted = useHasMounted();
  const status = useInferenceStore((state) => state.status);
  const progress = useInferenceStore((state) => state.progress);
  const errorMessage = useInferenceStore((state) => state.errorMessage);
  const currentRun = useInferenceStore((state) => state.currentRun);
  const startRun = useInferenceStore((state) => state.startRun);
  const setUploadProgress = useInferenceStore((state) => state.setUploadProgress);
  const setProcessing = useInferenceStore((state) => state.setProcessing);
  const completeRun = useInferenceStore((state) => state.completeRun);
  const failRun = useInferenceStore((state) => state.failRun);
  const token = useAuthStore((state) => state.token);
  const selectedRun = hasMounted ? currentRun : null;
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: apiClient.projects,
    enabled: Boolean(token)
  });

  const form = useForm<UploadFormValues>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      acquisitionType: "single",
      processingMode: "scientific",
      requestedModel: "opencv-baseline"
    }
  });

  const inference = useMutation({
    mutationFn: ({ file, targetFile, requestedModel, projectId }: RunInferenceVariables) =>
      apiClient.runInference({
        file,
        targetFile,
        requestedModel,
        projectId,
        onUploadProgress: (uploadProgress) => {
          setUploadProgress(uploadProgress);

          if (uploadProgress >= 100) {
            setProcessing();
          }
        }
      }),
    onMutate: ({ file, requestedModel }) => startRun(file, requestedModel),
    onSuccess: (result, { file }) => completeRun(result, file),
    onError: (error) => {
      failRun(error instanceof Error ? error.message : "Inference request failed.");
    }
  });

  const onSubmit = form.handleSubmit((values) => {
    const file = values.file?.[0] as File | undefined;
    const targetFile = values.targetFile?.[0] as File | undefined;
    if (file) {
      inference.mutate({
        file,
        targetFile,
        requestedModel: values.requestedModel,
        projectId: values.projectId
      });
    }
  });

  const busy = inference.isPending || status === "uploading" || status === "processing";
  const stageRows = [
    ["Upload", status === "idle" ? 0 : Math.min(progress, 70)],
    ["Cloud mask", selectedRun ? 100 : status === "processing" ? 70 : 0],
    ["Shadow mask", selectedRun ? 100 : status === "processing" ? 65 : 0],
    ["Reconstruction", selectedRun ? 100 : status === "processing" ? 55 : 0],
    ["Outputs", selectedRun ? 100 : 0]
  ];

  return (
    <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Run baseline inference</CardTitle>
            <CardDescription>Upload an image and execute the CPU-safe reconstruction pipeline.</CardDescription>
          </div>
          <Dialog>
            <DialogTrigger asChild>
              <Button size="icon" variant="ghost" aria-label="Upload rules">
                <Info className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Inference rules</DialogTitle>
                <DialogDescription>
                  The backend validates the file, generates masks, reconstructs cloudy regions, and
                  stores output images with public URLs.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>Accepted extensions: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.jp2`, `.j2k`.</p>
                <p>Requests for trained models fall back to OpenCV Telea inpainting until weights are connected.</p>
                <p>Large images are bounded by backend upload and pixel safety limits.</p>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={onSubmit}>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="acquisitionType">
                  Acquisition type
                </label>
                <Select
                  defaultValue="single"
                  onValueChange={(value) =>
                    form.setValue("acquisitionType", value as UploadFormValues["acquisitionType"])
                  }
                >
                  <SelectTrigger id="acquisitionType">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single">Single scene</SelectItem>
                    <SelectItem value="temporal">Temporal stack</SelectItem>
                    <SelectItem value="benchmark">Benchmark sample</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="processingMode">
                  Processing mode
                </label>
                <Select
                  defaultValue="scientific"
                  onValueChange={(value) =>
                    form.setValue("processingMode", value as UploadFormValues["processingMode"])
                  }
                >
                  <SelectTrigger id="processingMode">
                    <SelectValue placeholder="Select mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="scientific">Scientific</SelectItem>
                    <SelectItem value="visual">Visual</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="requestedModel">
                Requested model
              </label>
              <Select
                defaultValue="opencv-baseline"
                onValueChange={(value) =>
                  form.setValue("requestedModel", value as UploadFormValues["requestedModel"])
                }
              >
                <SelectTrigger id="requestedModel">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="opencv-baseline">OpenCV baseline</SelectItem>
                  <SelectItem value="swin-unet">Swin-UNet</SelectItem>
                  <SelectItem value="attention-unet">Attention U-Net</SelectItem>
                  <SelectItem value="multi-sensor-fusion">Multi-sensor fusion</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {token && projectsQuery.data?.length ? (
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="projectId">
                  Project
                </label>
                <Select
                  onValueChange={(value) => form.setValue("projectId", value)}
                >
                  <SelectTrigger id="projectId">
                    <SelectValue placeholder="Select project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projectsQuery.data.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="file">
                Satellite image
              </label>
              <Input
                id="file"
                type="file"
                accept=".png,.jpg,.jpeg,.tif,.tiff,.jp2,.j2k,image/png,image/jpeg,image/tiff"
                {...form.register("file")}
              />
              {form.formState.errors.file ? (
                <p className="text-sm text-destructive">{String(form.formState.errors.file.message)}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="targetFile">
                Ground truth image
              </label>
              <Input
                id="targetFile"
                type="file"
                accept=".png,.jpg,.jpeg,.tif,.tiff,.jp2,.j2k,image/png,image/jpeg,image/tiff"
                {...form.register("targetFile")}
              />
              <p className="text-xs text-muted-foreground">
                Optional cloud-free reference for PSNR, RMSE, MAE, and SAM.
              </p>
            </div>

            {errorMessage ? (
              <Alert variant="destructive">
                <AlertTitle>Inference failed</AlertTitle>
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            ) : null}

            {selectedRun && status === "completed" ? (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertTitle>Inference completed</AlertTitle>
                <AlertDescription>
                  {selectedRun.file_name} processed with {selectedRun.used_model} in{" "}
                  {selectedRun.processing_time_seconds.toFixed(2)}s.
                </AlertDescription>
              </Alert>
            ) : null}

            <Button disabled={busy} type="submit">
              {busy ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <FileUp className="mr-2 h-4 w-4" aria-hidden="true" />
              )}
              {busy ? "Processing" : "Run inference"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Processing state</CardTitle>
          <CardDescription>Live status for upload, mask generation, reconstruction, and output storage.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium capitalize">{status}</p>
              <p className="text-xs text-muted-foreground">
                {selectedRun?.file_name ?? "No active image"}
              </p>
            </div>
            <Cpu className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </div>
          <Separator />
          {stageRows.map(([label, value]) => (
            <div className="space-y-2" key={label}>
              <div className="flex justify-between text-sm">
                <span>{label}</span>
                <span className="text-muted-foreground">{Math.round(Number(value))}%</span>
              </div>
              <Progress value={Number(value)} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
