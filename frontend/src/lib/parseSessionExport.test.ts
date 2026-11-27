import { describe, expect, it } from 'vitest';
import garden from '../../fixtures/rooftop-garden.json';
import empty from '../../fixtures/empty.json';
import { parseSessionExport } from './parseSessionExport';

describe('parseSessionExport', () => {
  it('reads the exporter format with a cross-flower edge and no derived bridge records', () => {
    const { graph, session } = parseSessionExport(JSON.stringify(garden));
    expect(graph.relationships[2]).toMatchObject({ source_id: 'barrel', target_id: 'roots' });
    expect(graph.flowers.map((f) => f.label)).toEqual(['Rooftop garden', 'Rain collection']);
    expect(session.transcript).toBe(garden.session.transcript);
    expect(parseSessionExport(JSON.stringify(empty)).graph.nodes).toEqual([]);
  });

  it('accepts legacy nodes emitted by the backend', () => {
    const bundle = structuredClone(garden);
    bundle.graph.nodes[0].status = 'legacy';
    expect(parseSessionExport(JSON.stringify(bundle)).graph.nodes[0].status).toBe('legacy');
  });

  it.each([null, '2026-06-01T10:00:00.123456+01:00'])('preserves last_active %s', (last_active) => {
    const bundle = structuredClone(garden);
    Object.assign(bundle.graph.nodes[0], { last_active });
    expect(parseSessionExport(JSON.stringify(bundle)).graph.nodes[0].last_active).toBe(last_active);
  });

  it.each(['yesterday morning', '2026-02-30T10:00:00Z'])('rejects last_active %s', (last_active) => {
    const bundle = structuredClone(garden);
    Object.assign(bundle.graph.nodes[0], { last_active });
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(/graph\.nodes\.0\.last_active/);
  });

  it.each([
    [undefined, 'en-GB'],
    ['en-US', 'en-US'],
  ])('reads language_variant %s', (language_variant, expected) => {
    const bundle = { ...garden, session: { ...garden.session, language_variant } };
    expect(parseSessionExport(JSON.stringify(bundle)).session.language_variant).toBe(expected);
  });

  it.each([
    '2000-02-29T00:15:00.123456+05:30',
    '2024-02-29T23:59:59.1-04:00',
    '2026-06-01T10:00:00',
  ])('preserves the export timestamp %s', (created_at) => {
    const bundle = { ...garden, session: { ...garden.session, created_at } };
    expect(parseSessionExport(JSON.stringify(bundle)).session.created_at).toBe(created_at);
  });

  it.each([
    '2026-02-30T12:00:00Z',
    '1900-02-29T10:00:00.123456+01:00',
    '0000-01-01T00:00:00Z',
    '2026-06-01T10:00:00+24:00',
  ])('reports the field containing the invalid timestamp %s', (created_at) => {
    const bundle = { ...garden, session: { ...garden.session, created_at } };
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(/session\.created_at/i);
  });

  it.each([
    [['roof'], /garden.*missing.*roots/i],
    [['roots', 'roof', 'roots'], /garden.*duplicate.*roots/i],
  ] as const)('requires each assigned node exactly once in its flower (%j)', (members, error) => {
    const bundle = structuredClone(garden);
    bundle.graph.flowers[0].member_ids = [...members];
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(error);
  });

  const [grows, collects, irrigates] = garden.graph.relationships;
  const bridge = {
    source_flower_id: 'water', target_flower_id: 'garden', connecting_relationships: [irrigates],
  };
  function withBridge(overrides: Partial<typeof bridge> = {}) {
    const graph = { ...garden.graph, bridges: [{ ...bridge, ...overrides }] };
    return JSON.stringify({ ...garden, graph });
  }

  it('accepts a supplied bridge matching the graph', () => {
    expect(parseSessionExport(withBridge()).graph.bridges).toEqual([bridge]);
  });

  it.each<[string, Partial<typeof bridge>, RegExp]>([
    ['missing source flower', { source_flower_id: 'absent' }, /bridge.*missing flower.*absent/i],
    ['missing target flower', { target_flower_id: 'absent' }, /bridge.*missing flower.*absent/i],
    ['no connecting relationships', { connecting_relationships: [] }, /bridge.*connecting relationship/i],
    ['same flower', { target_flower_id: 'water', connecting_relationships: [collects] }, /bridge.*water/i],
    ['missing relationship', { connecting_relationships: [irrigates, { ...irrigates, id: 'absent' }] }, /bridge.*missing relationship.*absent/i],
    ['edge inside one flower', { connecting_relationships: [grows] }, /bridge.*grows/i],
    ['reversed direction', { source_flower_id: 'garden', target_flower_id: 'water' }, /bridge.*irrigates/i],
  ])('rejects a bridge with %s', (_name, overrides, error) => {
    expect(() => parseSessionExport(withBridge(overrides))).toThrow(error);
  });

  it.each([
    ['source_id', 'spout'],
    ['target_id', 'roof'],
    ['category', 'TEMPORAL'],
    ['description', 'drains roots'],
    ['confidence', 0.5],
    ['evidence', 'The barrel was empty.'],
    ['source', 'gardener'],
    ['created_at', '2026-06-01T10:01:00Z'],
  ] as const)('identifies the bridge relationship and conflicting %s', (field, value) => {
    const content = withBridge({ connecting_relationships: [{ ...irrigates, [field]: value }] });
    expect(() => parseSessionExport(content)).toThrow(new RegExp(`irrigates.*${field}`));
  });

  it.each<[string, string, RegExp]>([
    ['invalid JSON', '{', /valid JSON/i],
    ['missing session', '{}', /session/i],
    ['missing array', JSON.stringify({ ...empty, graph: { ...empty.graph, nodes: null } }), /graph.nodes/i],
    ['invalid transcript', JSON.stringify({ ...empty, session: { ...empty.session, transcript: [] } }), /session.transcript/i],
    ['invalid flower', JSON.stringify({ ...empty, graph: { ...empty.graph, flowers: [null] } }), /graph.flowers.0/i],
  ])('explains %s', (_name, content, error) => {
    expect(() => parseSessionExport(content)).toThrow(error);
  });

  it('rejects a missing edge endpoint before the canvas can receive it', () => {
    const bundle = structuredClone(garden);
    bundle.graph.relationships[0].target_id = 'absent';
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(/grows.*absent/);
  });

  it.each([
    ['🌱', 'waters roots', /graph\.flowers\.0\.label/],
    ['a'.repeat(65), 'waters roots', /graph\.flowers\.0\.label/],
    ['Rooftop garden', '🌱', /graph\.relationships\.2\.description/],
    ['Rooftop garden', 'a'.repeat(81), /graph\.relationships\.2\.description/],
  ] as const)('rejects out-of-range graph text (%s, %s)', (label, description, error) => {
    const bundle = structuredClone(garden);
    bundle.graph.flowers[0].label = label;
    bundle.graph.relationships[2].description = description;
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(error);
  });

  it.each([[2, 2], [64, 80]])('accepts %i label and %i description Unicode characters', (labelLength, descriptionLength) => {
    const bundle = structuredClone(garden);
    bundle.graph.flowers[0].label = '🌱'.repeat(labelLength);
    bundle.graph.relationships[2].description = '🌱'.repeat(descriptionLength);
    expect(parseSessionExport(JSON.stringify(bundle)).graph).toEqual(bundle.graph);
  });

  it('requires a declared stem to appear in the flower member list', () => {
    const bundle = structuredClone(garden);
    bundle.graph.flowers[0].member_ids = ['roots'];
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(/garden.*stem.*roof/i);
  });

  it('accepts a flower without a declared stem', () => {
    const bundle = structuredClone(garden);
    bundle.graph.flowers[0].stem_node_id = '';
    expect(parseSessionExport(JSON.stringify(bundle)).graph.flowers[0].stem_node_id).toBe('');
  });

  it('rejects missing parent flowers and collisions in the canvas element namespace', () => {
    const bundle = structuredClone(garden);
    bundle.graph.nodes[0].flower_id = 'missing';
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(/roof.*missing/);
    bundle.graph.nodes[0] = { ...garden.graph.nodes[0], id: 'garden' };
    expect(() => parseSessionExport(JSON.stringify(bundle))).toThrow(/duplicate.*garden/i);
  });
});
