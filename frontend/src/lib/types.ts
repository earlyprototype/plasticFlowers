// plasticFlower Gate 2 contract types
// Spec sources: `_docs/_dev/_MVP/_api/01_contracts.md`, `_docs/_dev/_MVP/_schema/01_data_model.md`,
// `_docs/_dev/_MVP/_ALIGNMENT.md`, `_dev/_plan/02_gate_contracts/contract_snapshot.md`

export type NodeStatus = "ghost" | "solid";
export type RelationshipCategory =
  | "CAUSAL"
  | "STRUCTURAL"
  | "COMPARATIVE"
  | "TEMPORAL"
  | "ASSOCIATIVE";
export type RelationshipSource = "builder" | "gardener";
export type ChunkStatus = "queued";

export interface Node {
  id: string;
  label: string;
  confidence: number; // 0.0-1.0
  mentions: number;
  timestamps: number[]; // seconds from session start
  inferred_type: string; // emergent, no enums
  flower_id: string | null;
  embedding?: number[] | null; // stored for similarity search (not sent yet)
  created_at: string; // ISO datetime
  status: NodeStatus;
}

export interface Relationship {
  id: string;
  source_id: string;
  target_id: string;
  category: RelationshipCategory;
  description: string; // 2-4 words
  confidence: number;
  evidence: string;
  source: RelationshipSource;
  created_at: string;
}

export interface Flower {
  id: string;
  label: string;
  stem_node_id: string;
  edge_count: number;
  member_ids: string[]; // Node ids belonging to this flower (may be empty on a fresh flower)
  created_at: string;
}

export interface FlowerBridge {
  source_flower_id: string;
  target_flower_id: string;
  connecting_relationships: Relationship[];
}

export interface GraphState {
  nodes: Node[];
  relationships: Relationship[];
  flowers: Flower[];
}

export interface GraphStateResponse extends GraphState {
  bridges: FlowerBridge[];
}

export interface NodesResponse {
  nodes: Node[];
}

export interface RelationshipsResponse {
  relationships: Relationship[];
}

export interface FlowersResponse {
  flowers: Flower[];
  bridges: FlowerBridge[];
}

export interface ReferencesResponse {
  references: ReferenceNode[];
}

export interface SessionSummary {
  id: string;
  name: string;
  created_at: string;
  ended_at: string | null;
}

export interface SessionDetail extends SessionSummary {
  transcript: string;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
}

export interface SessionCreateRequest {
  name?: string;
}

export interface SessionCreateResponse {
  id: string;
  name: string;
  created_at: string;
}

export interface SessionRenameRequest {
  name: string;
}

export interface SessionNameResponse {
  id: string;
  name: string;
}

export interface SessionEndResponse {
  id: string;
  ended_at: string;
}

export interface ChunkSubmissionRequest {
  text: string;
  start_time: number;
  end_time: number;
}

export interface ChunkSubmissionResponse {
  chunk_id: string;
  status: ChunkStatus;
}

export interface ChunkProcessedPayload {
  chunk_id: string;
  error?: string;
}

export interface SessionExportBundle {
  session: SessionDetail;
  graph: GraphStateResponse;
  metadata: Record<string, unknown>;
}

export interface NodeRemovedPayload {
  id: string;
}

export interface NodeMergedPayload {
  from_id: string;
  into_id: string;
}

// Mirrors backend/app/models/events.py NodeCorrectedPayload (STT label corrections)
export interface NodeCorrectedPayload {
  node_id: string;
  old_label: string;
  new_label: string;
  confidence: number; // 0.0-1.0
}

export interface RelationshipRemovedPayload {
  id: string;
}

export interface FlowerDissolvedPayload {
  id: string;
}

export interface GardenerCyclePayload {
  timestamp: string;
}

// Emitted when the server's bounded per-client event queue overflowed and
// dropped events — the client's graph state is incomplete and must refetch.
export interface ResyncRequiredPayload {
  reason: string; // e.g. "event_overflow"
}

export type NodeAddedEvent = {
  type: "node_added";
  payload: Node;
};

export type NodeUpdatedEvent = {
  type: "node_updated";
  payload: Node;
};

export type NodeRemovedEvent = {
  type: "node_removed";
  payload: NodeRemovedPayload;
};

export type NodeMergedEvent = {
  type: "node_merged";
  payload: NodeMergedPayload;
};

export type NodeCorrectedEvent = {
  type: "node_corrected";
  payload: NodeCorrectedPayload;
};

export type RelationshipAddedEvent = {
  type: "relationship_added";
  payload: Relationship;
};

export type RelationshipRemovedEvent = {
  type: "relationship_removed";
  payload: RelationshipRemovedPayload;
};

export type FlowerCreatedEvent = {
  type: "flower_created";
  payload: Flower;
};

export type FlowerUpdatedEvent = {
  type: "flower_updated";
  payload: Flower;
};

export type FlowerDissolvedEvent = {
  type: "flower_dissolved";
  payload: FlowerDissolvedPayload;
};

export type ChunkProcessedEvent = {
  type: "chunk_processed";
  payload: ChunkProcessedPayload;
};

export type GardenerCycleEvent = {
  type: "gardener_cycle";
  payload: GardenerCyclePayload;
};

export type HeartbeatEvent = {
  type: "heartbeat";
  payload: string;
};

export type ResyncRequiredEvent = {
  type: "resync_required";
  payload: ResyncRequiredPayload;
};

export type SSEvent =
  | NodeAddedEvent
  | NodeUpdatedEvent
  | NodeRemovedEvent
  | NodeMergedEvent
  | NodeCorrectedEvent
  | RelationshipAddedEvent
  | RelationshipRemovedEvent
  | FlowerCreatedEvent
  | FlowerUpdatedEvent
  | FlowerDissolvedEvent
  | ChunkProcessedEvent
  | GardenerCycleEvent
  | HeartbeatEvent
  | ReferenceAddedEvent
  | ResyncRequiredEvent;

export interface ReferenceSource {
  title: string;
  url: string;
  snippet: string;
  source_type: string;
}

export interface ReferenceNode {
  id: string;
  node_id: string;
  session_id: string;
  entity_type: string;
  canonical_summary: string;
  sources: ReferenceSource[];
  confidence: number;
  search_provider: string;
  fetched_at: string;
}

export type ReferenceAddedEvent = {
  type: "reference_added";
  payload: ReferenceNode;
};

export interface ErrorResponseBody {
  error: string;
  detail?: string;
  fields?: Record<string, unknown>;
}
