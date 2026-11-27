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
