'use client';

import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useChunkDispatcher } from '../hooks/useChunkDispatcher';

type MicControlProps = {
  sessionId: string;
};

export function MicControl({ sessionId }: MicControlProps) {
  const dispatcher = useChunkDispatcher({ sessionId });

  const speech = useSpeechRecognition({
    sessionId,
    lang: 'en-GB',
    continuous: true,
    interimResults: true,
    onTranscript: (text, isFinal) => {
      if (isFinal) void dispatcher.append(text, true);
    },
    onEnd: dispatcher.dispatchNow,
  });

  if (!speech.isSupported) {
    return (
      <div style={{ padding: '12px', background: '#FEE2E2', borderRadius: '8px', color: '#991B1B' }}>
        Speech recognition not supported in this browser. Use Chrome.
      </div>
    );
  }

  const label = {
    idle: sessionId ? '🎤 Start Listening' : 'Select a session to record',
    stopping: 'Finishing speech…',
    listening: '🛑 Stop Listening',
  }[speech.state];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <button
        disabled={!sessionId || speech.state === 'stopping'}
        onClick={speech.isListening ? speech.stop : speech.start}
        style={{
          padding: '16px 24px',
          fontSize: '18px',
          fontWeight: 600,
          border: 'none',
          borderRadius: '12px',
          cursor: 'pointer',
          background: speech.isListening ? '#EF4444' : '#22C55E',
          color: '#fff',
        }}
      >
        {label}
      </button>

      {speech.isListening && (
        <div style={{ padding: '12px', background: '#DCFCE7', borderRadius: '8px' }}>
          <strong>Listening...</strong>
          {speech.interimTranscript && (
            <p style={{ margin: '8px 0 0', fontStyle: 'italic', color: '#166534' }}>
              {speech.interimTranscript}
            </p>
          )}
        </div>
      )}

      {dispatcher.pendingSentences > 0 && (
        <div style={{ fontSize: '14px', color: '#6B7280' }}>
          Buffer: {dispatcher.pendingSentences} sentences pending
        </div>
      )}

      {speech.error && (
        <div style={{ padding: '8px', background: '#FEE2E2', borderRadius: '6px', color: '#991B1B' }}>
          Error: {speech.error}
        </div>
      )}

      {dispatcher.failures.map((failure) => (
        <div key={failure.sessionId} role="alert" style={{ padding: '8px', background: '#FEF3C7', borderRadius: '6px', color: '#92400E' }}>
          <p>Speech for session {failure.sessionId} is waiting to send. {failure.error}</p>
          <button type="button" onClick={() => void dispatcher.retry(failure.sessionId)}>Retry sending speech</button>
        </div>
      ))}
    </div>
  );
}

