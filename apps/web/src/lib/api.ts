import { getAuthToken } from "@/lib/auth-token";

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type ApiEnvelope<T> = {
  success: boolean;
  data: T | null;
  error: {
    code: string;
    message: string;
    details?: unknown;
  } | null;
  message: string | null;
  request_id: string | null;
};

export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
};

export type UserResponse = {
  id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  storage_quota_bytes: number;
  used_storage_bytes: number;
  created_at?: string | null;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: UserResponse;
};

export type AuthPayload = {
  email: string;
  password: string;
  full_name?: string | null;
};

export type StorageUsageResponse = {
  storage_quota_bytes: number;
  used_storage_bytes: number;
  remaining_storage_bytes: number;
  usage_percent: number;
};

export type ProjectResponse = {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  status: string;
  storage_used_bytes: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ProjectCreatePayload = {
  name: string;
  description?: string | null;
};

export type UserHistoryItem = {
  id: string;
  kind: string;
  title: string;
  status: string;
  project_id?: string | null;
  model?: string | null;
  quality_score?: number | null;
  storage_bytes: number;
  created_at?: string | null;
  metadata: Record<string, unknown>;
};

export type UserHistoryResponse = {
  items: UserHistoryItem[];
  storage: StorageUsageResponse;
};

export type SceneResponse = {
  id: string;
  user_id?: string | null;
  project_id?: string | null;
  filename: string;
  original_filename: string | null;
  safe_filename: string | null;
  sensor: string;
  status: string;
  content_type: string | null;
  file_size_bytes: number | null;
  checksum_sha256: string | null;
  storage_url: string | null;
  created_at: string | null;
};

export type JobResponse = {
  id: string;
  user_id?: string | null;
  project_id?: string | null;
  scene_id: string | null;
  status: string;
  selected_mode: string;
  selected_model: string;
  progress: number;
  error_message: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type InferenceMetrics = {
  cloud_coverage_percent: number;
  shadow_coverage_percent: number;
  quality_score: number;
  reconstruction_confidence_score?: number | null;
  mean_absolute_difference: number;
  mask_coverage_percent: number;
  input_width: number;
  input_height: number;
  processed_width: number;
  processed_height: number;
  tile_count?: number;
};

export type AIRecommendation = {
  title: string;
  message: string;
  severity: string;
  rationale: string;
  recommended_inputs: string[];
};

export type EvaluationMetrics = {
  psnr?: number | null;
  ssim?: number | null;
  rmse?: number | null;
  mae?: number | null;
  sam?: number | null;
  spectral_consistency_score?: number | null;
  cloud_reduction_score?: number | null;
  no_reference_quality_score?: number | null;
  processing_time_seconds?: number | null;
};

export type BenchmarkModelRow = {
  model_key: string;
  model_name: string;
  inputs: string;
  requested: boolean;
  used: boolean;
  fallback_used: boolean;
  simulated: boolean;
  quality_score: number;
  spectral_consistency_score: number;
  cloud_reduction_score: number;
  ssim: number;
  sam?: number | null;
  runtime_seconds: number;
};

export type BenchmarkResultResponse = {
  id: string;
  inference_run_id: string;
  metric_mode: string;
  requested_model: string;
  used_model: string;
  metrics: EvaluationMetrics;
  benchmark_rows: BenchmarkModelRow[];
  explanation: Record<string, string>;
  report_json_url?: string | null;
  report_markdown_url?: string | null;
  created_at?: string | null;
};

export type ModelRegistryResponse = {
  id: string;
  model_name: string;
  version: string;
  architecture: string;
  runtime_type: string;
  input_modalities?: Record<string, unknown> | null;
  dataset_version?: string | null;
  training_date?: string | null;
  metrics: Record<string, unknown>;
  checkpoint_path?: string | null;
  checkpoint_status: string;
  stage: string;
  is_active: boolean;
  is_best: boolean;
  created_at?: string | null;
};

export type ExperimentRunResponse = {
  id: string;
  model_id?: string | null;
  experiment_name: string;
  model_name: string;
  version: string;
  status: string;
  training_date?: string | null;
  dataset_version?: string | null;
  metrics: Record<string, unknown>;
  hyperparameters: Record<string, unknown>;
  checkpoint_path?: string | null;
  checkpoint_score?: number | null;
  is_best: boolean;
  notes?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
};

export type ModelCheckpointResponse = {
  id: string;
  model_id?: string | null;
  experiment_id?: string | null;
  model_name: string;
  version: string;
  checkpoint_path: string;
  storage_uri?: string | null;
  status: string;
  epoch?: number | null;
  metric_name?: string | null;
  metric_value?: number | null;
  metrics: Record<string, unknown>;
  file_size_bytes?: number | null;
  is_best: boolean;
  created_at?: string | null;
};

export type ExperimentMetricResponse = {
  id: string;
  experiment_id?: string | null;
  model_name: string;
  version: string;
  split: string;
  epoch?: number | null;
  step?: number | null;
  loss?: number | null;
  metrics: Record<string, unknown>;
  recorded_at?: string | null;
  created_at?: string | null;
};

export type ModelRegistrySummaryResponse = {
  registered_models: number;
  active_models: number;
  experiment_count: number;
  checkpoint_count: number;
  best_model?: ModelRegistryResponse | null;
  latest_training_date?: string | null;
  best_quality_score?: number | null;
};

export type ResearchReportFormat = "json" | "markdown" | "csv" | "pdf";

export type ResearchReportType =
  | "experiment_report"
  | "benchmark_report"
  | "metrics_comparison"
  | "complete_research_report";

export type ResearchMetricComparisonRow = {
  source: string;
  model_name: string;
  version?: string | null;
  dataset_version?: string | null;
  status?: string | null;
  checkpoint_status?: string | null;
  quality_score?: number | null;
  spectral_consistency_score?: number | null;
  cloud_reduction_score?: number | null;
  ssim?: number | null;
  sam?: number | null;
  runtime_seconds?: number | null;
};

export type ResearchDashboardSummaryResponse = {
  generated_at: string;
  registered_models: number;
  active_models: number;
  experiment_count: number;
  benchmark_count: number;
  checkpoint_count: number;
  best_model_name?: string | null;
  best_model_version?: string | null;
  best_quality_score?: number | null;
  latest_training_date?: string | null;
  model_comparison: ResearchMetricComparisonRow[];
  chart_series: Array<{
    model: string;
    quality: number;
    spectral: number;
    cloud_reduction: number;
    ssim: number;
  }>;
};

export type ResearchExportRequest = {
  report_type: ResearchReportType;
  formats: ResearchReportFormat[];
};

export type ResearchExportFileResponse = {
  filename: string;
  format: ResearchReportFormat;
  mime_type: string;
  asset_type: string;
  storage_url: string;
  file_size_bytes: number;
};

export type ResearchExportResponse = {
  export_id: string;
  report_type: ResearchReportType;
  generated_at: string;
  files: ResearchExportFileResponse[];
};

export type RasterMetadata = {
  file_type?: string | null;
  driver?: string | null;
  width?: number | null;
  height?: number | null;
  band_count?: number | null;
  dtype?: string | null;
  crs?: string | null;
  transform?: number[] | null;
  bounds?: number[] | null;
  nodata?: number | null;
  is_geospatial?: boolean;
  reader?: string | null;
};

export type InferenceRunResponse = {
  original_image_url: string;
  cloud_mask_url: string;
  shadow_mask_url: string;
  reconstructed_image_url: string;
  difference_map_url: string;
  attention_map_url?: string | null;
  confidence_map_url?: string | null;
  analysis_geotiff_url?: string | null;
  qgis_manifest_url?: string | null;
  cloud_coverage_percent: number;
  shadow_coverage_percent: number;
  quality_score: number;
  reconstruction_confidence_score?: number | null;
  processing_time_seconds: number;
  requested_model: string;
  used_model: string;
  fallback_used: boolean;
  metrics: InferenceMetrics;
  metadata?: RasterMetadata | null;
  evaluation_mode?: string | null;
  evaluation?: EvaluationMetrics | null;
  evaluation_explanation?: Record<string, string>;
  benchmark_rows?: BenchmarkModelRow[];
  recommendations?: AIRecommendation[];
  evaluation_report_url?: string | null;
  evaluation_report_markdown_url?: string | null;
};

export type DemoSampleResponse = {
  sample_id: string;
  title: string;
  description: string;
  is_synthetic: boolean;
  cached: boolean;
  sample_filename: string;
  sample_image_url: string;
  reference_image_url?: string | null;
  result: InferenceRunResponse;
  explanation: string[];
  limitations: string[];
};

type RunInferenceOptions = {
  file: File;
  targetFile?: File | null;
  requestedModel: string;
  projectId?: string | null;
  onUploadProgress?: (progress: number) => void;
};

class ApiClientError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function resolveAssetUrl(url: string): string {
  if (!url) {
    return "";
  }

  if (/^(https?:|blob:|data:)/.test(url)) {
    return url;
  }

  if (url.startsWith("/")) {
    return `${apiBaseUrl}${url}`;
  }

  return `${apiBaseUrl}/${url}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers
  });

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;

  if (!response.ok || !payload?.success) {
    throw new ApiClientError(
      payload?.error?.message ?? `API request failed with status ${response.status}`,
      response.status,
      payload?.error?.code ?? "api_error",
      payload?.error?.details
    );
  }

  return payload.data as T;
}

function parseEnvelope<T>(responseText: string, status: number): T {
  let payload: ApiEnvelope<T>;

  try {
    payload = JSON.parse(responseText) as ApiEnvelope<T>;
  } catch (error) {
    throw new ApiClientError(
      "API response could not be parsed.",
      status,
      "parse_error",
      error instanceof Error ? error.message : undefined
    );
  }

  if (!payload.success || !payload.data) {
    throw new ApiClientError(
      payload.error?.message ?? `API request failed with status ${status}`,
      status,
      payload.error?.code ?? "api_error",
      payload.error?.details
    );
  }

  return payload.data;
}

function runInference({
  file,
  targetFile,
  requestedModel,
  projectId,
  onUploadProgress
}: RunInferenceOptions): Promise<InferenceRunResponse> {
  const formData = new FormData();
  formData.append("requested_model", requestedModel);
  if (projectId) {
    formData.append("project_id", projectId);
  }
  formData.append("file", file);
  if (targetFile) {
    formData.append("target", targetFile);
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${apiBaseUrl}/api/inference/run`);
    xhr.setRequestHeader("Accept", "application/json");
    const token = getAuthToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onUploadProgress) {
        return;
      }

      onUploadProgress(Math.round((event.loaded / event.total) * 100));
    };

    xhr.onerror = () => {
      reject(new ApiClientError("Could not reach the inference API.", 0, "network_error"));
    };

    xhr.onload = () => {
      try {
        const data = parseEnvelope<InferenceRunResponse>(xhr.responseText, xhr.status);

        if (xhr.status < 200 || xhr.status >= 300) {
          reject(
            new ApiClientError(
              `API request failed with status ${xhr.status}`,
              xhr.status,
              "api_error"
            )
          );
          return;
        }

        resolve(data);
      } catch (error) {
        reject(
          error instanceof Error
            ? error
            : new ApiClientError("Inference response could not be parsed.", xhr.status, "parse_error")
        );
      }
    };

    xhr.send(formData);
  });
}

export const apiClient = {
  health: () => request<HealthResponse>("/api/health"),
  signup: (payload: AuthPayload) =>
    request<TokenResponse>("/api/auth/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  login: (payload: Pick<AuthPayload, "email" | "password">) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  me: () => request<UserResponse>("/api/auth/me"),
  projects: () => request<ProjectResponse[]>("/api/projects"),
  createProject: (payload: ProjectCreatePayload) =>
    request<ProjectResponse>("/api/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  userHistory: () => request<UserHistoryResponse>("/api/users/me/history"),
  storageUsage: () => request<StorageUsageResponse>("/api/users/me/storage"),
  scenes: () => request<SceneResponse[]>("/api/scenes"),
  jobs: () => request<JobResponse[]>("/api/jobs"),
  benchmarks: () => request<BenchmarkResultResponse[]>("/api/benchmarks"),
  latestBenchmark: () => request<BenchmarkResultResponse | null>("/api/benchmarks/latest"),
  modelRegistrySummary: () => request<ModelRegistrySummaryResponse>("/api/model-registry/summary"),
  modelRegistryModels: () => request<ModelRegistryResponse[]>("/api/model-registry/models"),
  bestModel: () => request<ModelRegistryResponse | null>("/api/model-registry/models/best"),
  experiments: () => request<ExperimentRunResponse[]>("/api/model-registry/experiments"),
  trainingHistory: () => request<ExperimentRunResponse[]>("/api/model-registry/training-history"),
  metricsHistory: () => request<ExperimentMetricResponse[]>("/api/model-registry/metrics-history"),
  checkpoints: () => request<ModelCheckpointResponse[]>("/api/model-registry/checkpoints"),
  researchSummary: () => request<ResearchDashboardSummaryResponse>("/api/research/summary"),
  exportResearchReport: (payload: ResearchExportRequest) =>
    request<ResearchExportResponse>("/api/research/export", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }),
  demoSample: () => request<DemoSampleResponse>("/api/demo/sample"),
  runDemo: () => request<DemoSampleResponse>("/api/demo/run", { method: "POST" }),
  uploadScene: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return request<SceneResponse>("/api/scenes/upload", {
      method: "POST",
      body: formData
    });
  },
  runInference
};

export { ApiClientError };
