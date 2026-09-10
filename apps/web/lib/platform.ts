import { apiFetch, ApiError } from "./api";
import type {
  Agent,
  Connection,
  Credential,
  Message,
  Module,
  Overview,
  Run,
  RunDetail,
  Workflow,
} from "../types/platform";

export const api = {
  get: <T>(path: string) => apiFetch<T>(`/api/v1${path}`),
  post: <T>(path: string, body: unknown = {}, key?: string) =>
    apiFetch<T>(`/api/v1${path}`, {
      method: "POST",
      body: JSON.stringify(body),
      headers: key ? { "Idempotency-Key": key } : undefined,
    }),
  patch: <T>(path: string, body: unknown) =>
    apiFetch<T>(`/api/v1${path}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  workflows: () => apiFetch<Workflow[]>("/api/v1/workflows"),
  modules: () => apiFetch<Module[]>("/api/v1/modules"),
  connections: () => apiFetch<Connection[]>("/api/v1/connections"),
  agents: () => apiFetch<Agent[]>("/api/v1/agents"),
  credentials: () => apiFetch<Credential[]>("/api/v1/credentials"),
  overview: () => apiFetch<Overview>("/api/v1/overview"),
  runs: () => apiFetch<Run[]>("/api/v1/runs"),
  run: (id: string) => apiFetch<RunDetail>(`/api/v1/runs/${id}`),
  inbox: () => apiFetch<Message[]>("/api/v1/inbox"),
};
export function errorMessage(e: unknown) {
  return e instanceof Error
    ? e.message
    : "Không thể kết nối. Vui lòng thử lại.";
}
export { ApiError };
