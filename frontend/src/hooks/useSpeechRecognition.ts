import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type SpeechRecognitionConstructor =
  | typeof window.SpeechRecognition
  | typeof window.webkitSpeechRecognition;

export type UseSpeechRecognitionOptions = {
  lang?: string;
  interimResults?: boolean;
  continuous?: boolean;
  /**
   * Invoked whenever the recognition API yields a transcript.
   */
  onTranscript?: (text: string, isFinal: boolean) => void;
  /**
   * Invoked when recognition ends (expected or unexpected), after any
   * remaining transcript has been flushed via `onTranscript`. Callers can use
   * this to flush buffered text to the API (see MicControl).
   */
  onEnd?: () => void;
};

export type SpeechState = "idle" | "listening" | "stopping";

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}) {
  const { lang = "en-GB", interimResults = true, continuous = true, onTranscript, onEnd } = options;
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  const onEndRef = useRef(onEnd);
  const [supported, setSupported] = useState(false);
  const [state, setState] = useState<SpeechState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [interimTranscript, setInterimTranscript] = useState("");
  
  // Continuous chunking tracking
  const interimStartTimeRef = useRef<number | null>(null);
  const forceFinalizationTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isListeningRef = useRef(false);
  
  // New refs for continuous cursor tracking
  const sentCursorRef = useRef(0);
  const fullTranscriptRef = useRef("");

  // Keep callback refs updated without recreating recognition
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
    onEndRef.current = onEnd;
  }, [onTranscript, onEnd]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const SpeechRecognitionCtor: SpeechRecognitionConstructor | undefined =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setSupported(false);
      return;
    }
    setSupported(true);
    
    // Only create once
    if (recognitionRef.current) return;
    
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = lang;
    recognition.interimResults = interimResults;
    recognition.continuous = continuous;

    // Helper: Extract pending text and send it as a chunk
    const extractAndSendChunk = () => {
      const fullText = fullTranscriptRef.current;
      
      // Safety check: ensure we have new content to send
      if (fullText.length <= sentCursorRef.current) return;

      const chunk = fullText.substring(sentCursorRef.current).trim();
      
      if (chunk && onTranscriptRef.current) {
        console.log('[SPEECH] Sending background chunk:', chunk.substring(0, 20) + '...');
        onTranscriptRef.current(chunk, true); // Send as final
      }
      
      // Update cursor to current position
      sentCursorRef.current = fullText.length;
      
      // Update UI to clear the "interim" view (since we just committed it)
      setInterimTranscript("");

      // Reset timer for next chunk
      if (forceFinalizationTimerRef.current) {
        clearTimeout(forceFinalizationTimerRef.current);
      }
      interimStartTimeRef.current = Date.now();
      forceFinalizationTimerRef.current = setTimeout(() => {
        extractAndSendChunk();
      }, 8000);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      // Reconstruct the full transcript from all results (final + interim)
      // This accounts for the API auto-correcting previous words
      let currentFullText = "";
      for (let i = 0; i < event.results.length; i += 1) {
        currentFullText += event.results[i][0].transcript;
      }
      // Add a trailing space if it's not the very end, to prevent word merging?
      // Actually, standard transcript usually has spacing. We'll trim later.
      
      fullTranscriptRef.current = currentFullText;

      // Calculate what is pending (visual interim)
      const pendingText = currentFullText.substring(sentCursorRef.current);
      setInterimTranscript(pendingText.trim());

      // Start tracking time if this is the first new input
      if (!interimStartTimeRef.current && pendingText.trim().length > 0) {
        interimStartTimeRef.current = Date.now();
        forceFinalizationTimerRef.current = setTimeout(() => {
          extractAndSendChunk();
        }, 8000);
      }

      // Check word count threshold (75 words)
      const wordCount = pendingText.trim().split(/\s+/).length;
      if (wordCount >= 75) {
        extractAndSendChunk();
      }
    };

    recognition.onerror = (event) => {
      if (event.error === 'aborted') return;
      console.error('[SPEECH] Error:', event.error);
      setError(event.error);
      setState("idle");
      isListeningRef.current = false;
    };

    recognition.onend = () => {
      // Flush any remaining text when stopping (expected or unexpected)
      if (fullTranscriptRef.current.length > sentCursorRef.current) {
         // We manually call the logic here one last time
         const chunk = fullTranscriptRef.current.substring(sentCursorRef.current).trim();
         if (chunk && onTranscriptRef.current) {
           console.log('[SPEECH] Flushing final chunk:', chunk);
           onTranscriptRef.current(chunk, true);
         }
      }

      setState("idle");
      isListeningRef.current = false;
      
      // Reset all cursors
      sentCursorRef.current = 0;
      fullTranscriptRef.current = "";
      setInterimTranscript("");
      
      interimStartTimeRef.current = null;
      if (forceFinalizationTimerRef.current) {
        clearTimeout(forceFinalizationTimerRef.current);
        forceFinalizationTimerRef.current = null;
      }

      // Signal speech end AFTER the final transcript flush above so consumers
      // can flush their chunk buffers to the API.
      onEndRef.current?.();
    };

    recognitionRef.current = recognition as SpeechRecognition;
    return () => {
      if (forceFinalizationTimerRef.current) {
        clearTimeout(forceFinalizationTimerRef.current);
        forceFinalizationTimerRef.current = null;
      }
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [lang, interimResults, continuous]);

  const start = useCallback(() => {
    if (!recognitionRef.current || !supported) return;
    setError(null);
    setState("listening");
    isListeningRef.current = true;
    
    // Reset cursors on start
    sentCursorRef.current = 0;
    fullTranscriptRef.current = "";
    setInterimTranscript("");
    
    try {
      recognitionRef.current.start();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setState("idle");
      isListeningRef.current = false;
    }
  }, [supported]);

  const stop = useCallback(() => {
    if (!recognitionRef.current) return;
    setState("stopping");
    // isListeningRef will be set to false in onend
    recognitionRef.current.stop();
  }, []);

  return useMemo(
    () => ({
      isSupported: supported,
      state,
      isListening: state === "listening",
      interimTranscript,
      error,
      start,
      stop,
    }),
    [supported, state, interimTranscript, error, start, stop],
  );
}

export type UseSpeechRecognitionReturn = ReturnType<typeof useSpeechRecognition>;