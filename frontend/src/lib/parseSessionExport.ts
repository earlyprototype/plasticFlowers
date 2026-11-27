import { z } from 'zod';
import type { SessionExportBundle } from './types';

const id = z.string().min(1);
const date = z.string()
  .datetime({ local: true, offset: true, message: 'Expected a valid ISO timestamp' })
  // Python datetimes start at year 1. Date.parse also checks the offset range.
  .refine((value) => !value.startsWith('0000-') && Number.isFinite(Date.parse(value)), 'Invalid timestamp');
const confidence = z.number().min(0).max(1);

function graphText(maxLength: number) {
  return z.string().refine((value) => {
    // The exporter's length limits count Unicode code points.
    const length = Array.from(value).length;
    return length >= 2 && length <= maxLength;
  }, `Expected 2 to ${maxLength} characters`);
}

const node = z.object({
  id,
  label: z.string(),
  confidence,
  mentions: z.number().int().nonnegative(),
  timestamps: z.array(z.number()),
  inferred_type: z.string(),
  flower_id: id.nullable(),
  embedding: z.array(z.number()).nullable().optional(),
  created_at: date,
  last_active: date.nullable().optional(),
  status: z.enum(['ghost', 'solid', 'legacy']),
});

const relationship = z.object({
  id,
  source_id: id,
  target_id: id,
  category: z.enum(['CAUSAL', 'STRUCTURAL', 'COMPARATIVE', 'TEMPORAL', 'ASSOCIATIVE']),
  description: graphText(80),
  confidence,
  evidence: z.string(),
  source: z.enum(['builder', 'gardener']),
  created_at: date,
});
const relationshipFields = relationship.keyof().options;

const bundle = z.object({
  session: z.object({
    id, name: z.string(), created_at: date, ended_at: date.nullable(), transcript: z.string(),
    language_variant: z.string().default('en-GB'),
  }),
  graph: z.object({
    nodes: z.array(node),
    relationships: z.array(relationship),
    flowers: z.array(z.object({
      id, label: graphText(64), stem_node_id: z.string(), member_ids: z.array(id),
      edge_count: z.number().int().nonnegative(), created_at: date,
    })),
    bridges: z.array(z.object({
      source_flower_id: id, target_flower_id: id, connecting_relationships: z.array(relationship),
    })).default([]),
  }),
  metadata: z.record(z.unknown()).default({}),
});

export function parseSessionExport(text: string): SessionExportBundle {
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error('This file does not contain valid JSON.');
  }
  const result = bundle.safeParse(data);
  if (!result.success) {
    const issue = result.error.issues[0];
    throw new Error(`${issue.path.join('.') || 'Session export'}: ${issue.message}.`);
  }

  // Cytoscape shares one ID namespace across compound nodes, concepts and edges.
  const { nodes, flowers, relationships, bridges } = result.data.graph;
  const ids = new Set<string>();
  for (const element of [...flowers, ...nodes, ...relationships]) {
    if (ids.has(element.id)) throw new Error(`Duplicate graph ID "${element.id}".`);
    ids.add(element.id);
  }
  const flowerIds = new Set(flowers.map((flower) => flower.id));
  for (const node of nodes) {
    if (node.flower_id !== null && !flowerIds.has(node.flower_id)) {
      throw new Error(`Node "${node.id}" refers to missing flower "${node.flower_id}".`);
    }
  }
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const listedMembers = new Set<string>();
  for (const flower of flowers) {
    for (const memberId of flower.member_ids) {
      const member = nodesById.get(memberId);
      if (!member) throw new Error(`Flower "${flower.id}" lists missing member "${memberId}".`);
      if (member.flower_id !== flower.id) {
        throw new Error(`Flower "${flower.id}" lists member "${memberId}", which does not belong to it.`);
      }
      if (listedMembers.has(memberId)) {
        throw new Error(`Flower "${flower.id}" lists duplicate member "${memberId}".`);
      }
      listedMembers.add(memberId);
    }
    if (flower.stem_node_id && !flower.member_ids.includes(flower.stem_node_id)) {
      throw new Error(`Flower "${flower.id}" names stem "${flower.stem_node_id}" outside its member list.`);
    }
  }
  for (const node of nodes) {
    if (node.flower_id !== null && !listedMembers.has(node.id)) {
      throw new Error(`Flower "${node.flower_id}" is missing assigned node "${node.id}" from its member list.`);
    }
  }
  for (const edge of relationships) {
    for (const endpoint of [edge.source_id, edge.target_id]) {
      if (!nodesById.has(endpoint)) {
        throw new Error(`Relationship "${edge.id}" refers to missing node "${endpoint}".`);
      }
    }
  }
  const edgesById = new Map(relationships.map((edge) => [edge.id, edge]));
  for (const bridge of bridges) {
    const { source_flower_id: source, target_flower_id: target } = bridge;
    for (const flowerId of [source, target]) {
      if (!flowerIds.has(flowerId)) throw new Error(`Bridge refers to missing flower "${flowerId}".`);
    }
    if (source === target) throw new Error(`Bridge names flower "${source}" at both ends.`);
    if (!bridge.connecting_relationships.length) {
      throw new Error(`Bridge from "${source}" to "${target}" has no connecting relationships.`);
    }
    for (const connection of bridge.connecting_relationships) {
      const edge = edgesById.get(connection.id);
      if (!edge) throw new Error(`Bridge refers to missing relationship "${connection.id}".`);
      const conflict = relationshipFields.find((field) => connection[field] !== edge[field]);
      if (conflict) {
        throw new Error(`Bridge relationship "${edge.id}" differs from the graph in field "${conflict}".`);
      }
      const sourceNode = nodesById.get(edge.source_id);
      const targetNode = nodesById.get(edge.target_id);
      if (sourceNode?.flower_id !== source || targetNode?.flower_id !== target) {
        throw new Error(`Bridge relationship "${edge.id}" does not connect flower "${source}" to "${target}".`);
      }
    }
  }
  return result.data;
}
