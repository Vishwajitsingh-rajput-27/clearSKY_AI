import { create } from "zustand";

type ProductMode = "scientific" | "visual";

type UIState = {
  sidebarOpen: boolean;
  productMode: ProductMode;
  selectedSceneId: string;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setProductMode: (mode: ProductMode) => void;
  setSelectedSceneId: (sceneId: string) => void;
};

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  productMode: "scientific",
  selectedSceneId: "L4-IN-KA-001",
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setProductMode: (mode) => set({ productMode: mode }),
  setSelectedSceneId: (sceneId) => set({ selectedSceneId: sceneId })
}));

