import type {
  ChunkSubmissionRequest,
  ChunkSubmissionResponse,
  FlowersResponse,
  GraphStateResponse,
  NodeStatus,
  NodesResponse,
  RelationshipCategory,
  RelationshipsResponse,
  RelationshipSource,
  ReferencesResponse,
  SessionCreateRequest,
  SessionCreateResponse,
  SessionDetail,
  SessionEndResponse,
  SessionExportBundle,
  SessionListResponse,
  SessionNameResponse,
  SessionRenameRequest,
} from "./types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010").replace(/\/$/, "");
const API_ROOT = `${API_BASE_URL}/api`;
const JSON_HEADERS = { "Content-Type": "application/json" } as const;

type QueryValue = string | number | boolean | undefined | null;
type QueryParams = Record<string, QueryValue>;
type NodeStatusFilter = NodeStatus | "all";

type ErrorShape = { error?: string; detail?: string };

const buildUrl = (path: string, query?: QueryParams): string => {
  const searchParams = new URLSearchParams();
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      searchParams.append(key, String(value));
    }
  }
  const queryString = searchParams.toString();
  return `${API_ROOT}${path}${queryString ? `?${queryString}` : ""}`;
};

const buildError = async (response: Response): Promise<Error> => {
  let message = response.statusText;
  try {
    const body = (await response.json()) as ErrorShape;
    if (body?.error || body?.detail) {
      message = `${body.error ?? "error"}${body.detail ? `: ${body.detail}` : ""}`;
    }
  } catch {
    try {
      const text = await response.text();
      if (text) message = text;
    } catch {
      // ignore secondary failure
    }
  }
  return new Error(`API ${response.status}: ${message}`);
};

const requestJSON = async <T>(
  path: string,
  init?: RequestInit,
  query?: QueryParams,
): Promise<T> => {
  const response = await fetch(buildUrl(path, query), init);
  if (!response.ok) {
    throw await buildError(response);
  }
  return (await response.json()) as T;
};

const requestText = async (
  path: string,
  init?: RequestInit,
  query?: QueryParams,
): Promise<string> => {
  const response = await fetch(buildUrl(path, query), init);
  if (!response.ok) {
    throw await buildError(response);
  }
  return await response.text();
};

const jsonRequest = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: JSON_HEADERS,
  body: JSON.stringify(body ?? {}),
});

const encodeId = (value: string): string => encodeURIComponent(value);

// Session management -------------------------------------------------------

export async function createSession(
  payload: SessionCreateRequest,
): Promise<SessionCreateResponse> {
  return requestJSON<SessionCreateResponse>("/sessions", jsonRequest("POST", payload));
}

export async function listSessions(): Promise<SessionListResponse> {
  return requestJSON<SessionListResponse>("/sessions");
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  return requestJSON<SessionDetail>(`/sessions/${encodeId(sessionId)}`);
}

export async function renameSession(
  sessionId: string,
  payload: SessionRenameRequest,
): Promise<SessionNameResponse> {
  return requestJSON<SessionNameResponse>(
    `/sessions/${encodeId(sessionId)}`,
    jsonRequest("PATCH", payload),
  );
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(buildUrl(`/sessions/${encodeId(sessionId)}`), { method: "DELETE" });
  if (!response.ok) {
    throw await buildError(response);
  }
}

export async function endSession(sessionId: string): Promise<SessionEndResponse> {
  return requestJSON<SessionEndResponse>(
    `/sessions/${encodeId(sessionId)}/end`,
    { method: "POST" },
  );
}

// Chunks -------------------------------------------------------------------

export async function submitChunk(
  sessionId: string,
  payload: ChunkSubmissionRequest,
): Promise<ChunkSubmissionResponse> {
  return requestJSON<ChunkSubmissionResponse>(
    `/sessions/${encodeId(sessionId)}/chunks`,
    jsonRequest("POST", payload),
  );
}

// Graph data ---------------------------------------------------------------

export async function getGraphState(sessionId: string): Promise<GraphStateResponse> {
  return requestJSON<GraphStateResponse>(`/sessions/${encodeId(sessionId)}/graph`);
}

export async function getNodes(
  sessionId: string,
  filters?: { status?: NodeStatusFilter; flower_id?: string | null },
): Promise<NodesResponse> {
  return requestJSON<NodesResponse>(
    `/sessions/${encodeId(sessionId)}/nodes`,
    undefined,
    {
      status: filters?.status,
      flower_id: filters?.flower_id ?? undefined,
    },
  );
}

export async function getRelationships(
  sessionId: string,
  filters?: { category?: RelationshipCategory; source?: RelationshipSource },
): Promise<RelationshipsResponse> {
  return requestJSON<RelationshipsResponse>(
    `/sessions/${encodeId(sessionId)}/relationships`,
    undefined,
    {
      category: filters?.category,
      source: filters?.source,
    },
  );
}

export async function getFlowers(sessionId: string): Promise<FlowersResponse> {
  return requestJSON<FlowersResponse>(`/sessions/${encodeId(sessionId)}/flowers`);
}

export async function getReferences(sessionId: string): Promise<ReferencesResponse> {
  return requestJSON<ReferencesResponse>(`/sessions/${encodeId(sessionId)}/references`);
}

// Exports ------------------------------------------------------------------

export async function exportSessionJSON(sessionId: string): Promise<SessionExportBundle> {
  return requestJSON<SessionExportBundle>(`/sessions/${encodeId(sessionId)}/export/json`);
}

export async function exportTranscriptPlain(sessionId: string): Promise<string> {
  return requestText(`/sessions/${encodeId(sessionId)}/export/transcript`);
}

export async function exportTranscriptVTT(sessionId: string): Promise<string> {
  return requestText(`/sessions/${encodeId(sessionId)}/export/vtt`);
}

export async function exportMarkdownSummary(sessionId: string): Promise<string> {
  return requestText(`/sessions/${encodeId(sessionId)}/export/markdown`);
}

// SSE ----------------------------------------------------------------------

export const getStreamUrl = (sessionId: string): string =>
  `${API_ROOT}/sessions/${encodeId(sessionId)}/stream`;
