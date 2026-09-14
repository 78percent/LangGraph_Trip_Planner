import axios from "axios";
import type {
  ApiResponse,
  TripFormData,
  TripPlan,
  PlanSummary,
  PlanEvent,
  Session,
  ChatMessage,
  ChatReply,
  Location,
  RouteInfo,
} from "@/types";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";
const api = axios.create({ baseURL, timeout: 250000 });

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail.map((item: { msg: string }) => item.msg).join("；");
    if (!error.response || error.response.status >= 500)
      return "无法连接后端服务。请先运行项目根目录的 start_backend.cmd，再重试。";
    return error.message;
  }
  return error instanceof Error ? error.message : "请求失败，请稍后重试";
}

export async function checkBackend(): Promise<void> {
  const response = await api.get("/health", { timeout: 5000 });
  if (response.data?.status !== "ready")
    throw new Error("后端尚未就绪，请检查后端启动终端。");
}

async function get<T>(path: string): Promise<T> {
  return (await api.get<ApiResponse<T>>(path)).data.data;
}

export const listPlans = () => get<PlanSummary[]>("/api/trip/plans");
export const getPlan = (id: string) => get<TripPlan>(`/api/trip/plans/${id}`);
export const listSessions = () => get<Session[]>("/api/chat/sessions");
export const getHistory = (id: string) =>
  get<{ messages: ChatMessage[]; pending: boolean }>(
    `/api/chat/sessions/${id}`,
  );
export async function sendMessage(
  message: string,
  session_id: string | null,
): Promise<ChatReply> {
  return (
    await api.post<ApiResponse<ChatReply>>("/api/chat/send", {
      message,
      session_id,
    })
  ).data.data;
}
export async function resumeSession(id: string): Promise<ChatReply> {
  return (
    await api.post<ApiResponse<ChatReply>>(`/api/chat/sessions/${id}/resume`)
  ).data.data;
}
export async function revisePlan(
  id: string,
  instruction: string,
): Promise<TripPlan> {
  return (
    await api.post<ApiResponse<TripPlan>>(`/api/trip/plans/${id}/revise`, {
      instruction,
    })
  ).data.data;
}
export async function queryRoute(
  origin: Location,
  destination: Location,
  city: string,
  route_type: string,
): Promise<RouteInfo> {
  return (
    await api.post<ApiResponse<RouteInfo>>("/api/map/route", {
      origin,
      destination,
      city,
      route_type,
    })
  ).data.data;
}

export async function generateTripPlan(
  form: TripFormData,
  onProgress: (message: string) => void,
): Promise<TripPlan> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 250000);
  try {
    const response = await fetch(`${baseURL}/api/trip/plan/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
      signal: controller.signal,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new Error(
        typeof body?.detail === "string"
          ? body.detail
          : response.status >= 500
            ? "无法连接后端服务。请先运行项目根目录的 start_backend.cmd，再重试。"
            : "请求字段不正确，请检查日期和天数",
      );
    }
    if (!response.body) throw new Error("浏览器没有收到规划数据流");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let plan: TripPlan | null = null;
    const consume = (line: string) => {
      if (!line.trim()) return;
      const event = JSON.parse(line) as PlanEvent;
      if (event.type === "error") throw new Error(event.message);
      if (event.type === "progress") onProgress(event.message);
      if (event.type === "result") plan = event.data;
    };
    try {
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        lines.forEach(consume);
        if (done) break;
      }
      consume(buffer);
    } finally {
      await reader.cancel();
      reader.releaseLock();
    }
    if (!plan) throw new Error("连接已结束，但没有收到完整行程");
    return plan;
  } finally {
    window.clearTimeout(timeout);
  }
}
