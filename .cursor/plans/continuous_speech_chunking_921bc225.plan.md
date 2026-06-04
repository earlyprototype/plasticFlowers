---
name: Continuous Speech Chunking
overview: Refactor speech recognition to use a "sent cursor" approach, eliminating the stop/restart cycle. Recognition runs continuously while chunks are extracted in the background every 8 seconds, preventing audio dropouts and providing smoother UX.
todos:
  - id: add-cursor-refs
    content: Add `sentCursorRef` and `fullTranscriptRef` to track sent position and accumulated text
    status: done
  - id: create-extract-function
    content: Create `extractAndSendChunk()` function to replace `forceFinalization()` - extracts substring from cursor, sends chunk, updates cursor position
    status: done
  - id: modify-onresult
    content: Modify `onresult` handler to reconstruct full transcript from `event.results`, call `extractAndSendChunk()` instead of `forceFinalization()`, remove all stop/start calls
    status: done
  - id: handle-final-results
    content: Update final result handling to send remaining text after cursor, then reset cursor and fullTranscript
    status: done
  - id: handle-cleanup
    content: Update stop/cleanup handlers to send any remaining text after cursor before resetting state
    status: done
  - id: test-continuous-speech
    content: Test with 30+ seconds of continuous speech to verify no dropouts, smooth chunking, and proper counter increments
    status: done
---

# Continuous Speech Recognition with Background Chunking

## Problem

Current implementation stops and restarts Web Speech API every 8 seconds to chunk text, causing:

- Brief audio dropouts
- Interruption in listening
- Jarring user experience

## Solution

Keep recognition running continuously, using a "sent cursor" to track which text has been chunked and sent. Crucially, we must **reconstruct** the transcript from the API's `event.results` on every event to account for the API's internal auto-corrections of previous interim words before we commit them to a chunk.

### Current Flow (Stop/Restart)

```mermaid
sequenceDiagram
    participant User
    participant WebSpeech as Web Speech API
    participant Hook as useSpeechRecognition
    participant UI as Display
    
    User->>WebSpeech: Speak
    WebSpeech->>Hook: Interim: "Hello my name is..."
    Hook->>UI: Display text
    Note over Hook: 8s timer hits
    Hook->>WebSpeech: STOP recognition
    Hook->>Hook: Send chunk
    WebSpeech-->>Hook: Brief dropout
    Hook->>WebSpeech: START recognition
    User->>WebSpeech: Continue speaking
    Note over UI: User sees interruption
```



### Proposed Flow (Continuous)

```mermaid
sequenceDiagram
    participant User
    participant WebSpeech as Web Speech API
    participant Hook as useSpeechRecognition
    participant Cursor as Sent Cursor
    participant UI as Display
    
    User->>WebSpeech: Speak continuously
    WebSpeech->>Hook: Interim: "Hello my name is..."
    Hook->>UI: Display full text
    Note over Cursor: cursor = 0
    Note over Hook: 8s timer hits
    Hook->>Cursor: Extract text[0 to current]
    Hook->>Hook: Send chunk in background
    Hook->>Cursor: cursor = current position
    Note over WebSpeech: NEVER stops
    WebSpeech->>Hook: Interim: "Hello my name is John and..."
    Hook->>UI: Display full text (uninterrupted)
    Note over UI: User sees smooth streaming
```



## Implementation Details

### File: `frontend/src/hooks/useSpeechRecognition.ts`

#### New State/Refs Required

Add:

- `sentCursorRef = useRef(0)` - tracks character position of last sent text
- `fullTranscriptRef = useRef("")` - accumulates ALL text (final + interim) currently known by the API

#### Key Logic Changes

**Current approach (lines ~88-101):**

- When 8s/75 words hit: `forceFinalization()` stops recognition, sends chunk, restarts
- Problem: causes dropout

**New approach:**

- When 8s/75 words hit: `extractAndSendChunk()` 
- Extract: `chunk = fullTranscript.substring(sentCursor, current)`
- Send chunk via `onTranscriptRef.current(chunk, true)`
- Update: `sentCursor = fullTranscript.length`
- Recognition NEVER stops
- Reset 8s timer for next chunk

**Visual display:**

- `interimTranscript` state updates on every event to show the full reconstructed text.
- User sees continuous streaming.

#### Detailed Changes

1. **Add new refs** (after line 32):
```typescript
const sentCursorRef = useRef(0);
const fullTranscriptRef = useRef("");
```




2. **Replace `forceFinalization` function** with:
```typescript
const extractAndSendChunk = useCallback(() => {
  const fullText = fullTranscriptRef.current;
  // Safety: only send if we have new content
  if (fullText.length <= sentCursorRef.current) return;

  const chunk = fullText.substring(sentCursorRef.current).trim();
  
  if (chunk && onTranscriptRef.current) {
    onTranscriptRef.current(chunk, true); // Send as final
  }
  
  // Update cursor to current position
  sentCursorRef.current = fullText.length;
  
  // Reset timer for next chunk
  if (forceFinalizationTimerRef.current) {
    clearTimeout(forceFinalizationTimerRef.current);
  }
  interimStartTimeRef.current = Date.now();
  forceFinalizationTimerRef.current = setTimeout(() => {
    extractAndSendChunk();
  }, 8000);
}, []);
```




3. **Modify `onresult` handler** (around line 60-101):

Instead of appending or relying on `resultIndex` simply:

1. Iterate through *all* `event.results` to build the `currentFullText`.

- *Rationale:* The Web Speech API often revises "interim" parts of the string. Rebuilding ensures we have the latest corrected version.

2. Update `fullTranscriptRef.current = currentFullText`.
3. Update `setInterimTranscript(currentFullText)`.
4. Check 8s/75 words threshold → call `extractAndSendChunk()`.
5. Remove all `recognition.stop()` and `recognition.start()` calls inside this handler.
6. **Handle actual final results (API Driven)**:

- While we process continuously, the API might mark a segment as `isFinal` (e.g., after a long pause).
- We rely on our `extractAndSendChunk` timer primarily, but if `event.results` resets (browser dependent behavior), we must handle it. 
- *Chrome Behavior:* With `continuous=true`, `event.results` usually keeps growing. We will assume it grows. If `event.resultIndex` resets to 0 (indicating a new session context from the browser), we should treat that as a reset point.

5. **Handle stop/cleanup**:

- When user stops listening: send remaining text after cursor
- On errors: reset cursor and fullTranscript

## Benefits

- **Zero audio dropouts:** Recognition never interrupts.
- **Smoother UX:** Text streams continuously without hiccups.
- **Better chunking:** Natural speech flow preserved.
- **Stability:** Reconstructing transcript on every event captures API auto-corrections.

## Risks & Mitigations

- **Mid-word splitting:** A chunk might cut a word or sentence in half.
- *Mitigation:* The `Gardener` agent now has access to the full `recent_transcript` in Neo4j (Gate 7 feature), allowing it to resolve ambiguities or "Ghost Nodes" created by split context.
- **Browser Memory:** Very long sessions might make `event.results` large.
- *Mitigation:* Unlikely to be an issue for typical <1 hour sessions.

## Testing Checklist

After implementation:

1. Speak continuously for 30+ seconds - verify no audio interruptions
2. Check console - should see chunks sent every ~8 seconds
3. Visual display should show uninterrupted text streaming
4. Backend should receive chunks smoothly