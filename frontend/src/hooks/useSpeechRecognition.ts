import { useEffect, useState } from "react";

import { debugLog } from "../lib/debug";

export type UseSpeechRecognitionOptions = {
  sessionId?: string;
  lang?: string;
  interimResults?: boolean;
  continuous?: boolean;
  onTranscript?: (text: string, isFinal: boolean) => void;
  /** Called after the last transcript from this run. */
  onEnd?: () => void;
};

export type SpeechState = "idle" | "listening" | "stopping";

type RecorderOptions = {
  createRecognition: () => SpeechRecognition;
  onState: (state: SpeechState) => void;
  onInterim: (text: string) => void;
  onError: (message: string | null) => void;
};

export function createSpeechRecorder({ createRecognition, onState, onInterim, onError }: RecorderOptions) {
  let target: UseSpeechRecognitionOptions = {};
  let active: SpeechRecognition | null = null;
  let stopping = false;
  let resumeAfterEnd = false;

  function stopActive() {
    if (!active || stopping) return;
    stopping = true;
    onState("stopping");
    active.stop();
  }

  function start() {
    if (active || target.sessionId === "") return;
    const owner = target;
    let fullText = "";
    let sentCursor = 0;
    let timer: ReturnType<typeof setTimeout> | null = null;
    onError(null);

    function flush(reason: "deadline" | "word limit" | "end") {
      if (timer !== null) clearTimeout(timer);
      timer = null;
      const text = fullText.slice(sentCursor).trim();
      sentCursor = Math.max(sentCursor, fullText.length);
      if (text) {
        debugLog("[SPEECH] Transcript chunk", { reason, characters: text.length });
        owner.onTranscript?.(text, true);
      }
      onInterim("");
    }

    try {
      const recognition = createRecognition();
      recognition.lang = owner.lang ?? "en-GB";
      recognition.interimResults = owner.interimResults ?? true;
      recognition.continuous = owner.continuous ?? true;
      recognition.onresult = (event) => {
        if (active !== recognition) return;
        fullText = Array.from(event.results, (result) => result[0].transcript).join("");
        const pending = fullText.slice(sentCursor).trim();
        onInterim(pending);
        if (stopping) return;
        if (pending.split(/\s+/).length >= 75) {
          flush("word limit");
        } else if (pending && timer === null) {
          timer = setTimeout(() => { if (!stopping) flush("deadline"); }, 8000);
        }
      };
      recognition.onerror = (event) => {
        if (active === recognition && event.error !== "aborted") {
          console.error("[SPEECH] Recognition error", event.error);
          onError(event.error);
          resumeAfterEnd = false;
        }
      };
      recognition.onend = () => {
        if (active !== recognition) return;
        flush("end");
        owner.onEnd?.();
        active = null;
        stopping = false;
        const resume = resumeAfterEnd;
        resumeAfterEnd = false;
        onState("idle");
        if (resume) start();
      };
      active = recognition;
      onState("listening");
      recognition.start();
    } catch (err) {
      active = null;
      onError(err instanceof Error ? err.message : String(err));
      onState("idle");
    }
  }

  return {
    setTarget(next: UseSpeechRecognitionOptions) {
      if (target.sessionId === next.sessionId) {
        // Keep callback changes for this session visible to its active run.
        Object.assign(target, next);
        return;
      }
      target = { ...next };
      if (active && !stopping) {
        // The previous recognizer can still emit final results after stop().
        // Its handlers keep their original owner until onend opens the next run.
        resumeAfterEnd = true;
        stopActive();
      }
    },
    start,
    stop() {
      resumeAfterEnd = false;
      stopActive();
    },
  };
}

export function useSpeechRecognition({
  sessionId, lang, interimResults, continuous, onTranscript, onEnd,
}: UseSpeechRecognitionOptions = {}) {
  const [supported, setSupported] = useState(false);
  const [state, setState] = useState<SpeechState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [recorder] = useState(() => createSpeechRecorder({
    createRecognition() {
      const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
      return new Ctor();
    },
    onState: setState,
    onInterim: setInterimTranscript,
    onError: setError,
  }));

  useEffect(() => {
    setSupported(Boolean(window.SpeechRecognition || window.webkitSpeechRecognition));
    return recorder.stop;
  }, [recorder]);
  useEffect(() => {
    recorder.setTarget({ sessionId, lang, interimResults, continuous, onTranscript, onEnd });
  }, [recorder, sessionId, lang, interimResults, continuous, onTranscript, onEnd]);

  return {
    isSupported: supported,
    state,
    isListening: state === "listening",
    interimTranscript,
    error,
    start: recorder.start,
    stop: recorder.stop,
  };
}

export type UseSpeechRecognitionReturn = ReturnType<typeof useSpeechRecognition>;
