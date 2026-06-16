export type SceneRecord = {
  id: string;
  name: string;
  region: string;
  sensor: string;
  cloud: number;
  shadow: number;
  status: "Ready" | "Processing" | "Queued" | "Archived";
  date: string;
};

export const scenes: SceneRecord[] = [
  {
    id: "L4-IN-KA-001",
    name: "Mandya agriculture block",
    region: "Karnataka",
    sensor: "LISS-IV",
    cloud: 31,
    shadow: 9,
    status: "Ready",
    date: "2026-06-02"
  },
  {
    id: "L4-IN-GJ-014",
    name: "Kachchh coastal transect",
    region: "Gujarat",
    sensor: "LISS-IV",
    cloud: 18,
    shadow: 4,
    status: "Processing",
    date: "2026-05-27"
  },
  {
    id: "L4-IN-AS-032",
    name: "Brahmaputra floodplain",
    region: "Assam",
    sensor: "LISS-IV",
    cloud: 46,
    shadow: 14,
    status: "Queued",
    date: "2026-05-19"
  },
  {
    id: "L4-IN-UK-008",
    name: "Garhwal terrain stack",
    region: "Uttarakhand",
    sensor: "LISS-IV",
    cloud: 23,
    shadow: 12,
    status: "Ready",
    date: "2026-05-11"
  }
];

export const detectionClasses = [
  { name: "Clear surface", value: 59 },
  { name: "Thick cloud", value: 24 },
  { name: "Thin cloud", value: 7 },
  { name: "Cloud shadow", value: 10 }
];

export const reconstructionSeries = [
  { stage: "Input", sam: 8.4, ssim: 0.61, ndvi: 0.18 },
  { stage: "Temporal", sam: 6.1, ssim: 0.72, ndvi: 0.11 },
  { stage: "S1/S2 Fusion", sam: 4.3, ssim: 0.81, ndvi: 0.07 },
  { stage: "Spectral QA", sam: 3.7, ssim: 0.86, ndvi: 0.04 }
];

export const benchmarkRows = [
  { model: "OpenCV fallback", inputs: "LISS-IV", sam: 7.9, ssim: 0.68, runtime: "18s" },
  { model: "Attention U-Net", inputs: "LISS-IV + masks", sam: 5.1, ssim: 0.79, runtime: "43s" },
  { model: "LISS-FuseSwin", inputs: "LISS-IV + S1 + S2 + DEM", sam: 3.7, ssim: 0.86, runtime: "71s" }
];

export const methodologySteps = [
  "LISS-IV raster validation and metadata extraction",
  "Cloud, haze, edge, and shadow segmentation",
  "Temporal, Sentinel-1, Sentinel-2, and DEM auxiliary alignment",
  "Scientific reconstruction with spectral preservation guardrails",
  "Evaluation, uncertainty scoring, and COG export"
];

