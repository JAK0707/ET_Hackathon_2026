"use client";
/**
 * ChatPanel.tsx — UPGRADED
 * Key additions vs original:
 *   - Inline citation chips [1][2] inside message text
 *   - Expandable "Sources" drawer per message
 *   - Agent step timeline (shows the 8-step agentic chain)
 *   - Verdict badge (BUY/HOLD/SELL) with confidence pill
 *   - user_id sent in every request for portfolio memory
 *
 * Drop this at: frontend/components/ChatPanel.tsx
 */

import { useState, useRef, useEffect } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────

interface Citation {
  id: number;
  label: string;
  source: string;
  agent: string;
}

interface AgentSignal {
  agent: string;
  summary: string;
  score: number;
  key_points: string[];
  sources: string[];
}

interface Decision {
  verdict: "BUY" | "HOLD" | "SELL";
  confidence: "High" | "Medium" | "Low";
  reasons: string[];
  risks: string[];
}

interface AnalysisResponse {
  intent: string;
  symbol: string;
  market_summary: string;
  decision: Decision;
  agent_signals: AgentSignal[];
  citations: Citation[];
  agent_steps: string[];
  explain_like_im_5?: string;
  rag_context: string[];
}

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  analysis?: AnalysisResponse;
  loading?: boolean;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const VERDICT_STYLES: Record<string, string> = {
  BUY: "verdict-buy",
  HOLD: "verdict-hold",
  SELL: "verdict-sell",
};

const AGENT_COLORS: Record<string, string> = {
  fundamental: "#0f766e",
  technical: "#7c3aed",
  news: "#b45309",
  flow: "#1d4ed8",
  decision: "#374151",
};

function getUserId(): string {
  if (typeof window === "undefined") return "default";
  let uid = localStorage.getItem("mm_user_id");
  if (!uid) {
    uid = `user_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem("mm_user_id", uid);
  }
  return uid;
}

// Inject citation chips [1][2] into plain text
function TextWithCitations({
  text,
  citations,
  onCiteClick,
}: {
  text: string;
  citations: Citation[];
  onCiteClick: (id: number) => void;
}) {
  if (!citations.length) return <span>{text}</span>;
  const parts = text.split(/(\[\d+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const id = parseInt(match[1]);
          const cite = citations.find((c) => c.id === id);
          return (
            <button
              key={i}
              className="cite-chip"
              title={cite?.source || ""}
              onClick={() => onCiteClick(id)}
              style={{ color: AGENT_COLORS[cite?.agent || "decision"] }}
            >
              {part}
            </button>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

// Score bar (-1 to +1)
function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(((score + 1) / 2) * 100);
  const color = score > 0.3 ? "#0f766e" : score < -0.3 ? "#dc2626" : "#b45309";
  return (
    <div className="score-bar-track">
      <div
        className="score-bar-fill"
        style={{ width: `${pct}%`, background: color }}
      />
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────

function AssistantMessage({ msg }: { msg: Message }) {
  const [showSources, setShowSources] = useState(false);
  const [showSteps, setShowSteps] = useState(false);
  const [highlightedCite, setHighlightedCite] = useState<number | null>(null);
  const a = msg.analysis;

  if (msg.loading) {
    return (
      <div className="msg assistant loading">
        <div className="loading-dots">
          <span /><span /><span />
        </div>
        <p className="loading-label">Running analysis agents…</p>
      </div>
    );
  }

  return (
    <div className="msg assistant">
      {/* Verdict badge */}
      {a?.decision && (
        <div className="verdict-row">
          <span className={`verdict-badge ${VERDICT_STYLES[a.decision.verdict]}`}>
            {a.decision.verdict}
          </span>
          <span className="confidence-pill">{a.decision.confidence} confidence</span>
          {a.symbol && a.symbol !== "^NSEI" && (
            <span className="symbol-tag">{a.symbol}</span>
          )}
        </div>
      )}

      {/* Main text */}
      <p className="msg-text">
        <TextWithCitations
          text={msg.text}
          citations={a?.citations || []}
          onCiteClick={(id) =>
            setHighlightedCite(highlightedCite === id ? null : id)
          }
        />
      </p>

      {/* Reasons & Risks */}
      {a?.decision?.reasons?.length ? (
        <div className="reasons-risks">
          <div className="reasons">
            <p className="rr-label">Why {a.decision.verdict}</p>
            <ul>
              {a.decision.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
          <div className="risks">
            <p className="rr-label risks-label">Risks</p>
            <ul>
              {a.decision.risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}

      {/* Agent signal bars */}
      {a?.agent_signals?.length ? (
        <div className="signal-bars">
          {a.agent_signals.map((sig) => (
            <div key={sig.agent} className="signal-row">
              <span
                className="agent-label"
                style={{ color: AGENT_COLORS[sig.agent] }}
              >
                {sig.agent}
              </span>
              <ScoreBar score={sig.score} />
              <span className="score-val">
                {sig.score > 0 ? "+" : ""}
                {sig.score.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {/* Footer actions */}
      <div className="msg-footer">
        {/* Citations toggle */}
        {a?.citations?.length ? (
          <button
            className="footer-btn"
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? "Hide sources" : `${a.citations.length} sources`}
          </button>
        ) : null}

        {/* Agent steps toggle */}
        {a?.agent_steps?.length ? (
          <button
            className="footer-btn"
            onClick={() => setShowSteps(!showSteps)}
          >
            {showSteps ? "Hide steps" : "Show agent steps"}
          </button>
        ) : null}
      </div>

      {/* Sources drawer */}
      {showSources && a?.citations?.length ? (
        <div className="sources-drawer">
          {a.citations.map((c) => (
            <div
              key={c.id}
              className={`citation-row ${highlightedCite === c.id ? "highlighted" : ""}`}
            >
              <span
                className="cite-chip-static"
                style={{ color: AGENT_COLORS[c.agent] }}
              >
                {c.label}
              </span>
              <span className="cite-source">{c.source}</span>
              <span
                className="cite-agent-tag"
                style={{
                  background: AGENT_COLORS[c.agent] + "22",
                  color: AGENT_COLORS[c.agent],
                }}
              >
                {c.agent}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {/* Agent steps timeline */}
      {showSteps && a?.agent_steps?.length ? (
        <ol className="steps-timeline">
          {a.agent_steps.map((step, i) => (
            <li key={i} className="step-item">
              <span className="step-dot" />
              <span className="step-text">{step}</span>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [holdings, setHoldings] = useState<{ symbol: string; quantity: number; avg_price: number }[]>([]);
  const [eli5, setEli5] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const userId = useRef(getUserId());

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text) return;
    setInput("");

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      text,
    };
    const loadingMsg: Message = {
      id: Date.now().toString() + "_l",
      role: "assistant",
      text: "",
      loading: true,
    };
    setMessages((prev) => [...prev, userMsg, loadingMsg]);

    try {
      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          holdings,
          explain_like_im_5: eli5,
          user_id: userId.current,
        }),
      });

      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data: AnalysisResponse = await res.json();

      const assistantMsg: Message = {
        id: Date.now().toString() + "_a",
        role: "assistant",
        text: data.market_summary || data.explain_like_im_5 || "Analysis complete.",
        analysis: data,
      };

      setMessages((prev) => {
        const without = prev.filter((m) => !m.loading);
        return [...without, assistantMsg];
      });
    } catch (err) {
      setMessages((prev) => {
        const without = prev.filter((m) => !m.loading);
        return [
          ...without,
          {
            id: Date.now().toString() + "_err",
            role: "assistant",
            text: "Something went wrong. Please check the backend is running.",
          },
        ];
      });
    }
  }

  return (
    <div className="chat-panel">

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h3>MarketMind AI — Indian Market GPT</h3>
            <p>Ask about any NSE/BSE stock, your portfolio, or today's market.</p>
            <div className="suggestions">
              {[
                "Analyse TCS",
                "Should I buy Reliance?",
                "Market summary today",
                "Is HDFC Bank a good buy?",
                "Analyse my portfolio",
              ].map((s) => (
                <button key={s} className="suggestion" onClick={() => setInput(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) =>
            msg.role === "user" ? (
              <div key={msg.id} className="msg user">
                {msg.text}
              </div>
            ) : (
              <AssistantMessage key={msg.id} msg={msg} />
            )
          )
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <label className="eli5-toggle">
          <input
            type="checkbox"
            checked={eli5}
            onChange={(e) => setEli5(e.target.checked)}
          />
          ELI5
        </label>
        <textarea
          className="chat-input"
          rows={1}
          placeholder="Ask about a stock, your portfolio, or today's market…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button className="send-btn" onClick={send} disabled={!input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}