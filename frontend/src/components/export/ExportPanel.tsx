'use client';

import { useCallback, useState } from 'react';

import {
  endSession,
  exportMarkdownSummary,
  exportSessionJSON,
  exportTranscriptPlain,
  exportTranscriptVTT,
} from '../../lib/api';

export interface ExportPanelProps {
  sessionId: string;
  /** Called after the end-session API call succeeds, with the server's ended_at. */
  onSessionEnded?: (endedAt?: string) => void;
}

type ExportFormat = 'json' | 'transcript' | 'vtt' | 'markdown';

interface ExportState {
  loading: ExportFormat | 'end' | null;
  error: string | null;
}

export function ExportPanel({ sessionId, onSessionEnded }: ExportPanelProps) {
  const [state, setState] = useState<ExportState>({ loading: null, error: null });

  const triggerDownload = useCallback((content: string | object, filename: string, mimeType: string) => {
    const text = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);

  const handleExport = useCallback(async (format: ExportFormat) => {
    setState({ loading: format, error: null });
    try {
      switch (format) {
        case 'json': {
          const data = await exportSessionJSON(sessionId);
          triggerDownload(data, `${sessionId}_export.json`, 'application/json');
          break;
        }
        case 'transcript': {
          const text = await exportTranscriptPlain(sessionId);
          triggerDownload(text, `${sessionId}_transcript.txt`, 'text/plain');
          break;
        }
        case 'vtt': {
          const vtt = await exportTranscriptVTT(sessionId);
          triggerDownload(vtt, `${sessionId}_transcript.vtt`, 'text/vtt');
          break;
        }
        case 'markdown': {
          const md = await exportMarkdownSummary(sessionId);
          triggerDownload(md, `${sessionId}_summary.md`, 'text/markdown');
          break;
        }
      }
      setState({ loading: null, error: null });
    } catch (err) {
      setState({ loading: null, error: err instanceof Error ? err.message : 'Export failed' });
    }
  }, [sessionId, triggerDownload]);

  const handleEndSession = useCallback(async () => {
    setState({ loading: 'end', error: null });
    try {
      const result = await endSession(sessionId);
      setState({ loading: null, error: null });
      onSessionEnded?.(result.ended_at);
    } catch (err) {
      setState({ loading: null, error: err instanceof Error ? err.message : 'Failed to end session' });
    }
  }, [sessionId, onSessionEnded]);

  const isLoading = state.loading !== null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        padding: '16px',
        background: '#FFFFFF',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      }}
    >
      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#1F2937' }}>
        Export Session
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <button
          onClick={() => handleExport('json')}
          disabled={isLoading}
          style={{
            padding: '10px 12px',
            border: '1px solid #D1D5DB',
            borderRadius: '8px',
            background: state.loading === 'json' ? '#F3F4F6' : '#FFFFFF',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            color: '#374151',
            transition: 'background 0.15s',
          }}
        >
          {state.loading === 'json' ? 'Exporting...' : 'JSON'}
        </button>

        <button
          onClick={() => handleExport('transcript')}
          disabled={isLoading}
          style={{
            padding: '10px 12px',
            border: '1px solid #D1D5DB',
            borderRadius: '8px',
            background: state.loading === 'transcript' ? '#F3F4F6' : '#FFFFFF',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            color: '#374151',
            transition: 'background 0.15s',
          }}
        >
          {state.loading === 'transcript' ? 'Exporting...' : 'Transcript'}
        </button>

        <button
          onClick={() => handleExport('vtt')}
          disabled={isLoading}
          style={{
            padding: '10px 12px',
            border: '1px solid #D1D5DB',
            borderRadius: '8px',
            background: state.loading === 'vtt' ? '#F3F4F6' : '#FFFFFF',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            color: '#374151',
            transition: 'background 0.15s',
          }}
        >
          {state.loading === 'vtt' ? 'Exporting...' : 'VTT'}
        </button>

        <button
          onClick={() => handleExport('markdown')}
          disabled={isLoading}
          style={{
            padding: '10px 12px',
            border: '1px solid #D1D5DB',
            borderRadius: '8px',
            background: state.loading === 'markdown' ? '#F3F4F6' : '#FFFFFF',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            color: '#374151',
            transition: 'background 0.15s',
          }}
        >
          {state.loading === 'markdown' ? 'Exporting...' : 'Summary'}
        </button>
      </div>

      <hr style={{ margin: '4px 0', border: 'none', borderTop: '1px solid #E5E7EB' }} />

      <button
        onClick={handleEndSession}
        disabled={isLoading}
        style={{
          padding: '10px 14px',
          border: 'none',
          borderRadius: '8px',
          background: state.loading === 'end' ? '#FCA5A5' : '#EF4444',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          fontSize: '14px',
          fontWeight: 600,
          color: '#FFFFFF',
          transition: 'background 0.15s',
        }}
      >
        {state.loading === 'end' ? 'Ending...' : 'End Session'}
      </button>

      {state.error && (
        <p style={{ margin: 0, fontSize: '13px', color: '#DC2626' }}>
          {state.error}
        </p>
      )}
    </div>
  );
}





