import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { DemoSampleResponse, InferenceRunResponse } from "@/lib/api";

export type InferenceStatus = "idle" | "uploading" | "processing" | "completed" | "error";

export type InferenceHistoryItem = InferenceRunResponse & {
  id: string;
  file_name: string;
  file_size_bytes: number;
  created_at: string;
  is_demo?: boolean;
  demo_sample_id?: string;
  demo_description?: string;
};

type InferenceState = {
  status: InferenceStatus;
  progress: number;
  errorMessage: string | null;
  currentRun: InferenceHistoryItem | null;
  history: InferenceHistoryItem[];
  requestedModel: string;
  activeFileName: string | null;
  startRun: (file: File, requestedModel: string) => void;
  startDemoRun: () => void;
  setUploadProgress: (progress: number) => void;
  setProcessing: () => void;
  completeRun: (result: InferenceRunResponse, file: File) => void;
  completeDemoRun: (demo: DemoSampleResponse) => void;
  failRun: (message: string) => void;
  selectRun: (id: string) => void;
  clearError: () => void;
};

export const useInferenceStore = create<InferenceState>()(
  persist(
    (set, get) => ({
      status: "idle",
      progress: 0,
      errorMessage: null,
      currentRun: null,
      history: [],
      requestedModel: "opencv-baseline",
      activeFileName: null,
      startRun: (file, requestedModel) =>
        set({
          status: "uploading",
          progress: 2,
          errorMessage: null,
          requestedModel,
          activeFileName: file.name
        }),
      startDemoRun: () =>
        set({
          status: "processing",
          progress: 88,
          errorMessage: null,
          requestedModel: "opencv-baseline",
          activeFileName: "Synthetic LISS-IV demo sample"
        }),
      setUploadProgress: (progress) =>
        set({
          status: progress >= 100 ? "processing" : "uploading",
          progress: progress >= 100 ? 82 : Math.max(2, Math.min(70, progress * 0.7))
        }),
      setProcessing: () => set({ status: "processing", progress: 88 }),
      completeRun: (result, file) => {
        const item: InferenceHistoryItem = {
          ...result,
          id: `${Date.now()}-${file.name}`,
          file_name: file.name,
          file_size_bytes: file.size,
          created_at: new Date().toISOString(),
          is_demo: false
        };
        const nextHistory = [
          item,
          ...get().history.filter((run) => run.id !== item.id)
        ].slice(0, 12);

        set({
          status: "completed",
          progress: 100,
          errorMessage: null,
          currentRun: item,
          history: nextHistory,
          activeFileName: file.name
        });
      },
      completeDemoRun: (demo) => {
        const item: InferenceHistoryItem = {
          ...demo.result,
          id: `demo-${demo.sample_id}-${Date.now()}`,
          file_name: demo.sample_filename,
          file_size_bytes: 0,
          created_at: new Date().toISOString(),
          is_demo: true,
          demo_sample_id: demo.sample_id,
          demo_description: demo.description
        };
        const nextHistory = [
          item,
          ...get().history.filter((run) => run.demo_sample_id !== demo.sample_id)
        ].slice(0, 12);

        set({
          status: "completed",
          progress: 100,
          errorMessage: null,
          currentRun: item,
          history: nextHistory,
          activeFileName: demo.sample_filename
        });
      },
      failRun: (message) =>
        set({
          status: "error",
          progress: 0,
          errorMessage: message,
          activeFileName: null
        }),
      selectRun: (id) => {
        const selected = get().history.find((run) => run.id === id) ?? null;
        set({
          currentRun: selected,
          status: selected ? "completed" : get().status,
          progress: selected ? 100 : get().progress
        });
      },
      clearError: () => set({ errorMessage: null, status: "idle", progress: 0 })
    }),
    {
      name: "clearsky-inference-store",
      partialize: (state) => ({
        currentRun: state.currentRun,
        history: state.history
      })
    }
  )
);
