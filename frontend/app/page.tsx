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
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <header className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Codebase Intelligence
          </h1>
          <p className="mt-2 text-slate-500">
            Ask natural-language questions about any public GitHub repository.
          </p>
        </header>

        <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-4">
            1. Ingest a repository
          </h2>
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-slate-100"
              placeholder="https://github.com/pallets/flask"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={ingesting}
            />
            <button
              onClick={handleIngest}
              disabled={ingesting || !repoUrl}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {ingesting && <Spinner />}
              {ingesting ? "Ingesting..." : "Ingest"}
            </button>
          </div>

          {ingestStatus && (
            <p className={`mt-3 text-sm ${ingestError ? "text-red-600" : "text-slate-600"}`}>
              {ingestStatus}
            </p>
          )}

          {knownRepos.length > 0 && (
            <div className="mt-4 flex items-center gap-2">
              <label className="text-sm text-slate-500">Active repo:</label>
              <select
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                disabled={ingesting}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {knownRepos.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}
        </section>

        <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-4">
            2. Ask a question
          </h2>

          {!repo && (
            <p className="text-sm text-slate-400 mb-3">Ingest a repository first.</p>
          )}

          <div className="flex gap-2">
            <input
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-slate-100"
              placeholder="How does this project handle authentication?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={!repo || asking}
            />
            <button
              onClick={handleAsk}
              disabled={asking || !repo || !question}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {asking && <Spinner />}
              {asking ? "Thinking..." : "Ask"}
            </button>
          </div>

          {answer && (
            <div
              className={`mt-5 whitespace-pre-wrap text-sm leading-relaxed rounded-lg p-4 ${
                askError ? "bg-red-50 text-red-700" : "bg-slate-50 text-slate-800"
              }`}
            >
              {answer}
            </div>
          )}

          {sources.length > 0 && (
            <div className="mt-5">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
                Sources
              </h3>
              <ul className="space-y-1.5">
                {sources.map((s) => (
                  <li
                    key={s.ref}
                    className="text-sm text-slate-600 bg-slate-50 rounded-md px-3 py-2 border border-slate-200"
                  >
                    <span className="font-mono text-indigo-600">[{s.ref}]</span>{" "}
                    <span className="font-medium">{s.symbol}</span>
                    <span className="text-slate-400"> — {s.file} (lines {s.lines})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function Spinner() {
  return (
    <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
  );
}