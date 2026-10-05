"use client";

import { useState } from "react";

const API_BASE = "http://127.0.0.1:8001";

type Source = { ref: number; file: string; lines: string; symbol: string };

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repo, setRepo] = useState("");
  const [knownRepos, setKnownRepos] = useState<string[]>([]);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState("");
  const [ingestError, setIngestError] = useState(false);

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [askError, setAskError] = useState(false);

  async function handleIngest() {
    setIngesting(true);
    setIngestError(false);
    setIngestStatus("Cloning and indexing the repository. This can take a few minutes for a large repo...");
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ingest failed");
      setRepo(data.repo);
      setKnownRepos((prev) => (prev.includes(data.repo) ? prev : [...prev, data.repo]));
      setIngestStatus(
        `Done. ${data.files_parsed} files parsed, ${data.chunks_stored} chunks stored in ${data.seconds}s.`
      );
    } catch (err: any) {
      setIngestError(true);
      setIngestStatus(
        err.message === "Failed to fetch"
          ? "Couldn't reach the backend. Is it running on port 8001?"
          : `Error: ${err.message}`
      );
    } finally {
      setIngesting(false);
    }
  }

  async function handleAsk() {
    if (!repo) return;
    setAsking(true);
    setAskError(false);
    setAnswer("");
    setSources([]);
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, repo, limit: 5 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Ask failed");
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (err: any) {
      setAskError(true);
      setAnswer(
        err.message === "Failed to fetch"
          ? "The backend didn't respond in time. This can happen on a free-tier model under load — try again."
          : `Error: ${err.message}`
      );
    } finally {
      setAsking(false);
    }
  }

  return (
    <main style={{ maxWidth: 800, margin: "40px auto", padding: "0 16px", fontFamily: "sans-serif" }}>
      <h1>Codebase Intelligence</h1>

      <section style={{ marginBottom: 32 }}>
        <h2>1. Ingest a repository</h2>
        <input
          style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
          placeholder="https://github.com/pallets/flask"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          disabled={ingesting}
        />
        <button onClick={handleIngest} disabled={ingesting || !repoUrl}>
          {ingesting && <Spinner />} {ingesting ? "Ingesting..." : "Ingest"}
        </button>
        {ingestStatus && (
          <p style={{ color: ingestError ? "#b00020" : "#333" }}>{ingestStatus}</p>
        )}

        {knownRepos.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <label>Active repo: </label>
            <select value={repo} onChange={(e) => setRepo(e.target.value)} disabled={ingesting}>
              {knownRepos.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        )}
      </section>

      <section>
        <h2>2. Ask a question</h2>
        {!repo && <p style={{ color: "#888" }}>Ingest a repository first.</p>}
        <input
          style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
          placeholder="How does this project handle authentication?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={!repo || asking}
        />
        <button onClick={handleAsk} disabled={asking || !repo || !question}>
          {asking && <Spinner />} {asking ? "Thinking..." : "Ask"}
        </button>

        {answer && (
          <div
            style={{
              marginTop: 16,
              whiteSpace: "pre-wrap",
              lineHeight: 1.5,
              color: askError ? "#b00020" : "#000",
            }}
          >
            {answer}
          </div>
        )}

        {sources.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h3>Sources</h3>
            <ul>
              {sources.map((s) => (
                <li key={s.ref}>
                  [{s.ref}] {s.symbol} — {s.file} (lines {s.lines})
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </main>
  );
}

function Spinner() {
  return (
    <span
      style={{
        display: "inline-block",
        width: 10,
        height: 10,
        border: "2px solid #999",
        borderTopColor: "transparent",
        borderRadius: "50%",
        animation: "spin 0.6s linear infinite",
        marginRight: 6,
      }}
    />
  );
}