import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiClient, type AuthPayload, type UserResponse } from "@/lib/api";
import { clearAuthToken, getAuthToken, setAuthToken } from "@/lib/auth-token";

type AuthStatus = "idle" | "loading" | "authenticated" | "anonymous" | "error";

type AuthState = {
  status: AuthStatus;
  token: string | null;
  user: UserResponse | null;
  errorMessage: string | null;
  signup: (payload: AuthPayload) => Promise<void>;
  login: (payload: Pick<AuthPayload, "email" | "password">) => Promise<void>;
  fetchMe: () => Promise<void>;
  logout: () => void;
  clearError: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      status: getAuthToken() ? "authenticated" : "anonymous",
      token: getAuthToken(),
      user: null,
      errorMessage: null,
      signup: async (payload) => {
        set({ status: "loading", errorMessage: null });
        try {
          const response = await apiClient.signup(payload);
          setAuthToken(response.access_token);
          set({
            status: "authenticated",
            token: response.access_token,
            user: response.user,
            errorMessage: null
          });
        } catch (error) {
          set({
            status: "error",
            errorMessage: error instanceof Error ? error.message : "Signup failed."
          });
          throw error;
        }
      },
      login: async (payload) => {
        set({ status: "loading", errorMessage: null });
        try {
          const response = await apiClient.login(payload);
          setAuthToken(response.access_token);
          set({
            status: "authenticated",
            token: response.access_token,
            user: response.user,
            errorMessage: null
          });
        } catch (error) {
          set({
            status: "error",
            errorMessage: error instanceof Error ? error.message : "Login failed."
          });
          throw error;
        }
      },
      fetchMe: async () => {
        if (!get().token && !getAuthToken()) {
          set({ status: "anonymous", user: null });
          return;
        }

        try {
          const user = await apiClient.me();
          set({ status: "authenticated", user, token: getAuthToken(), errorMessage: null });
        } catch {
          clearAuthToken();
          set({ status: "anonymous", token: null, user: null });
        }
      },
      logout: () => {
        clearAuthToken();
        set({ status: "anonymous", token: null, user: null, errorMessage: null });
      },
      clearError: () => set({ errorMessage: null, status: get().token ? "authenticated" : "anonymous" })
    }),
    {
      name: "clearsky-auth-store",
      partialize: (state) => ({
        token: state.token,
        user: state.user
      })
    }
  )
);
