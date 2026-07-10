'use client';

import { FormEvent, useCallback, useMemo, useState } from "react";

import { ExportPanel } from "../components/export";
import { FiltersPanel, type FilterState } from "../components/filters";
import { GraphCanvas } from "../components/graph";
import {
  defaultPortraitTitle,
  isCartographyEnabled,
} from "../components/graph/config/cartography";
import { MicControl } from "../components/MicControl";
import { ResearchPanel } from "../components/research/ResearchPanel";
import { useGraphState } from "../hooks";
import { createSession, renameSession, listSessions } from "../lib/api";
import type { SessionSummary } from "../lib/types";

const DEFAULT_SESSION_ID = "";

// Portrait mode requires cartography — the toggle is hidden when the flag is
// off. NEXT_PUBLIC_* vars are inlined at build time (module constant).
const CARTOGRAPHY_ENABLED = isCartographyEnabled();

export default function HomePage() {
  const [sessionInput, setSessionInput] = useState(DEFAULT_SESSION_ID);
  const [sessionId, setSessionId] = useState<string>(DEFAULT_SESSION_ID);
  const [filters, setFilters] = useState<FilterState>({
    status: "all",
    minConfidence: 0,
    flowerId: "all",
    inferredType: "all",
  });

  const {
    nodes,
    relationships,
    flowers,
    references,
    connectionState,
    sseError,
    graphError,
    lastChunkError,
    refreshGraph,
    builderCount,
    gardenerCount,
    researcherCount,
  } = useGraphState(sessionId);

  const filteredNodes = useMemo(() => {
    return nodes.filter((node) => {
      if (filters.status !== "all" && node.status !== filters.status) return false;
      if (node.confidence < filters.minConfidence) return false;
      if (filters.flowerId === "none" && node.flower_id !== null) return false;
      if (filters.flowerId !== "all" && filters.flowerId !== "none" && node.flower_id !== filters.flowerId) {
        return false;
      }
      if (filters.inferredType !== "all" && node.inferred_type !== filters.inferredType) return false;
      return true;
    });
  }, [filters, nodes]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredRelationships = useMemo(
    () =>
      relationships.filter(
        (rel) => filteredNodeIds.has(rel.source_id) && filteredNodeIds.has(rel.target_id),
      ),
    [relationships, filteredNodeIds],
  );

  const filteredFlowerIds = useMemo(() => {
    if (filters.flowerId === "all") {
      return new Set(flowers.map((f) => f.id));
    }
    if (filters.flowerId === "none") {
      return new Set<string>();
    }
    return new Set([filters.flowerId]);
  }, [filters.flowerId, flowers]);

  const filteredFlowers = useMemo(() => {
    if (filters.flowerId === "all") {
      const idsWithMembers = new Set(filteredNodes.map((n) => n.flower_id).filter(Boolean) as string[]);
      return flowers.filter((flower) => idsWithMembers.size === 0 || idsWithMembers.has(flower.id));
    }
    if (filters.flowerId === "none") {
      return [];
    }
    return flowers.filter((flower) => flower.id === filters.flowerId);
  }, [filters.flowerId, filteredNodes, flowers]);

  const totalCounts = useMemo(
    () => ({
      nodes: nodes.length,
      relationships: relationships.length,
      flowers: flowers.length,
    }),
    [nodes.length, relationships.length, flowers.length],
  );

  const [sessionEnded, setSessionEnded] = useState(false);
  const [sessionEndedAt, setSessionEndedAt] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [sessionName, setSessionName] = useState<string>("");
  const [showSessionPicker, setShowSessionPicker] = useState(false);
  const [availableSessions, setAvailableSessions] = useState<SessionSummary[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Session portrait (Move 5): the presentation render of the finished map.
  // Auto-enters when the session ends; also toggleable from the header. The
  // title is local state only — persisting it to the backend is a follow-up.
  const [portrait, setPortrait] = useState(false);
  const [portraitTitle, setPortraitTitle] = useState("");

  const handleLoadClick = async () => {
    setIsLoadingSessions(true);
    try {
      const result = await listSessions();
      setAvailableSessions(result.sessions);
      setShowSessionPicker(true);
    } catch (err) {
      console.error("Failed to load sessions:", err);
      alert("Failed to load sessions list");
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const handleSelectSession = (session: SessionSummary) => {
    setSessionInput(session.id);
    setSessionId(session.id);
    setSessionName(session.name);
    setSessionEnded(session.ended_at !== null);
    setSessionEndedAt(session.ended_at);
    setPortrait(false);
    setShowSessionPicker(false);
  };

  const handleRename = async () => {
    if (!sessionId) return;
    const newName = prompt("Enter a memorable name for this session:", sessionName || "");
    if (newName && newName.trim()) {
      try {
        await renameSession(sessionId, { name: newName.trim() });
        setSessionName(newName.trim());
      } catch (err) {
        console.error("Failed to rename session:", err);
        alert("Failed to rename session");
      }
    }
  };

  const handleConnect = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = sessionInput.trim();
    if (value) {
      // useGraphState refreshes on the sessionId change; calling the current
      // refreshGraph here would hit the OLD session (stale closure).
      setSessionId(value);
      setSessionEnded(false);
      setSessionEndedAt(null);
      setPortrait(false);
    }
  };

  const handleNewSession = async () => {
    setIsCreating(true);
    try {
      const defaultName = `live-${Date.now()}`;
      const result = await createSession({ name: defaultName });
      setSessionInput(result.id);
      setSessionId(result.id);
      setSessionName(result.name);
      setSessionEnded(false);
      setSessionEndedAt(null);
      setPortrait(false);
    } catch (err) {
      console.error('Failed to create session:', err);
      alert("Failed to create session. Check console/backend.");
    } finally {
      setIsCreating(false);
    }
  };

  // Ending a session must produce a keepable artifact: once the end-session
  // API call succeeds, the UI flips into portrait mode automatically.
  const handleSessionEnded = useCallback((endedAt?: string) => {
    setSessionEnded(true);
    setSessionEndedAt(endedAt ?? new Date().toISOString());
    if (CARTOGRAPHY_ENABLED) {
      setPortrait(true);
    }
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#F5F5F4",
        padding: "32px",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
      }}
    >
      <header style={{ maxWidth: "820px" }}>
        <h1 style={{ margin: "0 0 8px", fontSize: "28px" }}>Live Graph + SSE Monitor</h1>
        <p style={{ margin: 0, color: "#444" }}>
          Use this harness to watch Server-Sent Events in real time. Connect to a session, start the replay
          script, then bounce the backend (Ctrl+C / restart). The status badge on the canvas should move
          through <strong>open → reconnecting → open</strong>, providing the artefact required for Gate&nbsp;4.
        </p>
        {CARTOGRAPHY_ENABLED ? (
          <div style={{ marginTop: "12px", display: "flex", gap: "8px", alignItems: "center" }}>
            <button
              type="button"
              id="portrait-toggle"
              onClick={() => setPortrait((value) => !value)}
              style={{
                border: "1px solid #A8B196",
                borderRadius: "6px",
                padding: "6px 14px",
                background: portrait ? "#42493E" : "#FBFAF2",
                color: portrait ? "#FBFAF2" : "#42493E",
                fontWeight: 600,
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              {portrait ? "Exit portrait" : "Portrait"}
            </button>
            {portrait ? (
              <input
                type="text"
                id="portrait-title"
                value={portraitTitle}
                onChange={(event) => setPortraitTitle(event.target.value)}
                placeholder={defaultPortraitTitle(sessionId)}
                aria-label="Portrait title"
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid #D4D4D4",
                  fontSize: "13px",
                  width: "260px",
                }}
              />
            ) : null}
          </div>
        ) : null}
      </header>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(280px, 320px) minmax(auto, 1fr)",
          gap: "24px",
          alignItems: "start",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <form
            onSubmit={handleConnect}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              padding: "20px",
              background: "#FFFFFF",
              borderRadius: "12px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.07)",
            }}
          >
            <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
              <label htmlFor="session-input" style={{ fontWeight: 600 }}>
                Session ID
              </label>
              <input
                id="session-input"
                type="text"
                value={sessionInput}
                onChange={(event) => setSessionInput(event.target.value)}
                placeholder="Paste session ID + Enter to load"
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border: "1px solid #D4D4D4",
                  marginTop: "6px",
                }}
              />
            </fieldset>

            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                onClick={handleNewSession}
                disabled={isCreating}
                style={{
                  flex: 1,
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  background: "#22C55E",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: isCreating ? "wait" : "pointer",
                }}
              >
                {isCreating ? "..." : "🆕 New"}
              </button>
              <button
                type="button"
                onClick={handleLoadClick}
                disabled={isLoadingSessions}
                style={{
                  flex: 1,
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  background: "#F97316",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: isLoadingSessions ? "wait" : "pointer",
                }}
              >
                {isLoadingSessions ? "..." : "📂 Load"}
              </button>
              <button
                type="button"
                onClick={handleRename}
                disabled={!sessionId}
                style={{
                  flex: 1,
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  background: sessionId ? "#3B82F6" : "#9CA3AF",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: sessionId ? "pointer" : "not-allowed",
                }}
              >
                💾 Save
              </button>
            </div>

            {showSessionPicker && (
              <div style={{
                marginTop: "12px",
                border: "1px solid #E5E7EB",
                borderRadius: "8px",
                maxHeight: "200px",
                overflowY: "auto",
                background: "#F9FAFB",
              }}>
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 12px",
                  borderBottom: "1px solid #E5E7EB",
                  background: "#fff",
                  position: "sticky",
                  top: 0,
                }}>
                  <strong style={{ fontSize: "14px" }}>📂 Select Session ({availableSessions.length})</strong>
                  <button
                    type="button"
                    onClick={() => setShowSessionPicker(false)}
                    style={{ background: "none", border: "none", cursor: "pointer", fontSize: "16px" }}
                  >
                    ✕
                  </button>
                </div>
                {availableSessions.length === 0 ? (
                  <div style={{ padding: "12px", color: "#6B7280", fontSize: "14px" }}>
                    No sessions found
                  </div>
                ) : (
                  availableSessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => handleSelectSession(session)}
                      style={{
                        padding: "10px 12px",
                        borderBottom: "1px solid #E5E7EB",
                        cursor: "pointer",
                        background: session.id === sessionId ? "#FFF7ED" : "transparent",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "#F3F4F6")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = session.id === sessionId ? "#FFF7ED" : "transparent")}
                    >
                      <div style={{ fontWeight: 600, fontSize: "14px" }}>{session.name}</div>
                      <div style={{ fontSize: "12px", color: "#6B7280" }}>
                        {new Date(session.created_at).toLocaleString()}
                        {session.ended_at && " (ended)"}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            <div style={{ fontSize: "14px", color: "#374151" }}>
              <p style={{ margin: "0 0 8px" }}>
                <strong>Flow:</strong>
              </p>
              <ol style={{ margin: 0, paddingLeft: "18px", lineHeight: 1.4 }}>
                <li>Start the backend (`python backend/scripts/dev_server.py`).</li>
                <li>Run the replay helper (<code>npm --prefix frontend run replay …</code>).</li>
                <li>Restart the backend to force an SSE reconnect and watch the badge.</li>
              </ol>
            </div>

            <dl style={{ margin: 0, fontSize: "14px" }}>
              {sessionName && (
                <>
                  <dt style={{ fontWeight: 600 }}>Session Name</dt>
                  <dd style={{ marginBottom: "8px", color: "#3B82F6" }}>{sessionName}</dd>
                </>
              )}
              <dt style={{ fontWeight: 600 }}>Connection</dt>
              <dd style={{ marginBottom: "8px" }}>{connectionState}</dd>
              <dt style={{ fontWeight: 600 }}>Counts</dt>
              <dd style={{ marginBottom: "8px" }}>
                {totalCounts.nodes} nodes · {totalCounts.relationships} relationships · {totalCounts.flowers} flowers
                <button
                  type="button"
                  onClick={() => refreshGraph()}
                  style={{
                    marginLeft: "8px",
                    padding: "2px 8px",
                    fontSize: "12px",
                    background: "#E5E7EB",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  🔄
                </button>
              </dd>
              {sessionEnded ? (
                <>
                  <dt style={{ fontWeight: 600, color: "#059669" }}>Session</dt>
                  <dd style={{ marginBottom: "8px" }}>Ended</dd>
                </>
              ) : null}
              {sseError ? (
                <>
                  <dt style={{ fontWeight: 600, color: "#B91C1C" }}>SSE error</dt>
                  <dd style={{ marginBottom: "8px" }}>{sseError}</dd>
                </>
              ) : null}
              {graphError ? (
                <>
                  <dt style={{ fontWeight: 600, color: "#B91C1C" }}>Graph sync error</dt>
                  <dd style={{ marginBottom: "8px" }}>{graphError}</dd>
                </>
              ) : null}
              {lastChunkError ? (
                <>
                  <dt style={{ fontWeight: 600, color: "#B45309" }}>Last chunk warning</dt>
                  <dd style={{ marginBottom: "8px" }}>{lastChunkError}</dd>
                </>
              ) : null}
            </dl>
          </form>

          <div style={{ padding: '20px', background: '#FFFFFF', borderRadius: '12px', boxShadow: '0 10px 30px rgba(0,0,0,0.07)' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>🎤 Live Speech Input</h3>
            <MicControl sessionId={sessionId} />
          </div>
          <div style={{ padding: '20px', background: '#FFFFFF', borderRadius: '12px', boxShadow: '0 10px 30px rgba(0,0,0,0.07)' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '16px' }}>Agent Activity</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "14px", color: "#374151" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <strong>Builder:</strong>
                <span>{builderCount} chunks processed</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <strong>Gardener:</strong>
                <span>{gardenerCount} cycles completed</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <strong>Researcher:</strong>
                <span>{researcherCount} references found</span>
              </div>
            </div>
          </div>
          <FiltersPanel nodes={nodes} flowers={flowers} value={filters} onChange={setFilters} />
          <ResearchPanel references={references} />
          <ExportPanel sessionId={sessionId} onSessionEnded={handleSessionEnded} />
        </div>

        <GraphCanvas
          className="sse-test__canvas"
          nodes={filteredNodes}
          relationships={filteredRelationships}
          flowers={filteredFlowers}
          connectionState={connectionState}
          lastChunkError={lastChunkError}
          portrait={portrait}
          portraitTitle={portraitTitle}
          sessionId={sessionId}
          sessionEndedAt={sessionEndedAt}
        />
      </section>
    </main>
  );
}

