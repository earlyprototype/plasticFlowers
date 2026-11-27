'use client';

import { type ChangeEvent, useRef, useState } from 'react';
import { GraphCanvas } from '../../components/graph';
import { parseSessionExport } from '../../lib/parseSessionExport';
import type { SessionExportBundle } from '../../lib/types';
import styles from './viewer.module.css';

export default function BundleViewer() {
  const [view, setView] = useState<{ bundle: SessionExportBundle; revision: number } | null>(null);
  const [error, setError] = useState('');
  const selection = useRef(0);

  async function openFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    if (!file) return;
    const revision = ++selection.current;
    setError('');
    try {
      const bundle = parseSessionExport(await file.text());
      if (revision === selection.current) setView({ bundle, revision });
    } catch (cause) {
      if (revision === selection.current) {
        const reason = cause instanceof Error ? cause.message : 'Could not read the file.';
        setError(`Could not open ${file.name}. ${reason}`);
      }
    }
  }

  const session = view?.bundle.session;
  const graph = view?.bundle.graph;

  return (
    <main className={styles.viewer}>
      <header>
        <h1>Open an exported conversation</h1>
        <p>Choose a session JSON file to read its graph and transcript on this device.</p>
        <label className={styles.file}>
          Open JSON export
          <input
            type="file"
            accept=".json,application/json"
            onClick={(event) => { event.currentTarget.value = ''; }}
            onChange={openFile}
          />
        </label>
        {error && <p role="alert" className={styles.error}>{error}</p>}
      </header>

      {view && session && graph && (
        <section aria-labelledby="session-name">
          <h2 id="session-name">{session.name || session.id}</h2>
          <div className={styles.columns}>
            <div className={styles.map}>
              <GraphCanvas
                key={view.revision}
                className={styles.canvas}
                readOnly
                nodes={graph.nodes}
                relationships={graph.relationships}
                flowers={graph.flowers}
                sessionId={session.id}
                sessionStartMs={Date.parse(session.created_at)}
              />
              {graph.nodes.length === 0 && graph.flowers.length === 0 && (
                <p className={styles.empty}>No graph elements in this export.</p>
              )}
            </div>
            <section className={styles.transcript} aria-labelledby="transcript-title">
              <h3 id="transcript-title">Transcript</h3>
              <p>{session.transcript || 'No transcript in this export.'}</p>
            </section>
          </div>
        </section>
      )}
    </main>
  );
}
