'use client';

import { useCallback, useMemo } from 'react';

import type { Flower, Node } from '../../lib/types';

export type FilterState = {
  status: 'all' | 'ghost' | 'solid';
  minConfidence: number;
  flowerId: 'all' | 'none' | string;
  inferredType: 'all' | string;
};

type FiltersPanelProps = {
  nodes: Node[];
  flowers: Flower[];
  value: FilterState;
  onChange: (next: FilterState) => void;
};

export function FiltersPanel({ nodes, flowers, value, onChange }: FiltersPanelProps) {
  const typeOptions = useMemo(() => {
    const types = Array.from(new Set(nodes.map((n) => n.inferred_type).filter(Boolean))).sort();
    return types;
  }, [nodes]);

  const handleStatus = useCallback(
    (status: FilterState['status']) => onChange({ ...value, status }),
    [onChange, value],
  );

  const handleConfidence = useCallback(
    (minConfidence: number) => onChange({ ...value, minConfidence }),
    [onChange, value],
  );

  const handleFlower = useCallback(
    (flowerId: FilterState['flowerId']) => onChange({ ...value, flowerId }),
    [onChange, value],
  );

  const handleType = useCallback(
    (inferredType: FilterState['inferredType']) => onChange({ ...value, inferredType }),
    [onChange, value],
  );

  const handleReset = useCallback(
    () =>
      onChange({
        status: 'all',
        minConfidence: 0,
        flowerId: 'all',
        inferredType: 'all',
      }),
    [onChange],
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        padding: '12px',
        background: '#FFFFFF',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#111827' }}>Z-filters</h3>
        <button
          onClick={handleReset}
          style={{
            border: 'none',
            background: 'transparent',
            color: '#2563EB',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Reset
        </button>
      </div>

      <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: '#374151' }}>
        Status
        <select
          value={value.status}
          onChange={(e) => handleStatus(e.target.value as FilterState['status'])}
          style={{ padding: '8px', borderRadius: '8px', border: '1px solid #D1D5DB' }}
        >
          <option value="all">All</option>
          <option value="solid">Solid</option>
          <option value="ghost">Ghost</option>
        </select>
      </label>

      <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: '#374151' }}>
        Min confidence ({value.minConfidence.toFixed(2)})
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={value.minConfidence}
          onChange={(e) => handleConfidence(Number(e.target.value))}
        />
      </label>

      <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: '#374151' }}>
        Flower
        <select
          value={value.flowerId}
          onChange={(e) => handleFlower(e.target.value as FilterState['flowerId'])}
          style={{ padding: '8px', borderRadius: '8px', border: '1px solid #D1D5DB' }}
        >
          <option value="all">All</option>
          <option value="none">No flower</option>
          {flowers.map((flower) => (
            <option key={flower.id} value={flower.id}>
              {flower.label}
            </option>
          ))}
        </select>
      </label>

      <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: '#374151' }}>
        Type
        <select
          value={value.inferredType}
          onChange={(e) => handleType(e.target.value as FilterState['inferredType'])}
          style={{ padding: '8px', borderRadius: '8px', border: '1px solid #D1D5DB' }}
        >
          <option value="all">All</option>
          {typeOptions.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}




