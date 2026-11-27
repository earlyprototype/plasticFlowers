import { z } from 'zod';
import type { SessionExportBundle } from './types';

const id = z.string().min(1);
const date = z.string().refine((value) => Number.isFinite(Date.parse(value)), 'Expected a date');
const confidence = z.number().min(0).max(1);

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
  status: z.enum(['ghost', 'solid', 'legacy']),
});

const relationship = z.object({
  id,
  source_id: id,
  target_id: id,
  category: z.enum(['CAUSAL', 'STRUCTURAL', 'COMPARATIVE', 'TEMPORAL', 'ASSOCIATIVE']),
  description: z.string(),
  confidence,
  evidence: z.string(),
  source: z.enum(['builder', 'gardener']),
  created_at: date,
});

const bundle = z.object({
  session: z.object({
    id, name: z.string(), created_at: date, ended_at: date.nullable(), transcript: z.string(),
  }),
  graph: z.object({
    nodes: z.array(node),
    relationships: z.array(relationship),
    flowers: z.array(z.object({
      id, label: z.string(), stem_node_id: z.string(), member_ids: z.array(id),
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
  const { nodes, flowers, relationships } = result.data.graph;
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
  const nodeIds = new Set(nodes.map((node) => node.id));
  for (const edge of relationships) {
    for (const endpoint of [edge.source_id, edge.target_id]) {
      if (!nodeIds.has(endpoint)) {
        throw new Error(`Relationship "${edge.id}" refers to missing node "${endpoint}".`);
      }
    }
  }
  return result.data;
}
