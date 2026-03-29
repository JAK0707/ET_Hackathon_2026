"use client";

import { useEffect, useState } from "react";
import { postJson, type Holding } from "@/lib/api";

type PortfolioResponse = {
  diversification_score: number;
  sector_exposure: Record<string, number>;
  risk_alerts: string[];
  summary: string;
  explain_like_im_5?: string | null;
};

const holdings: Holding[] = [
  { symbol: "TCS.NS", quantity: 12, average_price: 3680, sector: "Information Technology" },
  { symbol: "HDFCBANK.NS", quantity: 20, average_price: 1560, sector: "Financial Services" },
  { symbol: "RELIANCE.NS", quantity: 8, average_price: 2840, sector: "Energy" }
];

export function PortfolioPanel() {
  const [data, setData] = useState<PortfolioResponse | null>(null);
  useEffect(() => { postJson<PortfolioResponse>("/portfolio/analyze", { holdings, explain_like_im_5: true }).then(setData).catch(() => setData(null)); }, []);
  return (
    <section className="panel">
      <div className="section-header"><p className="eyebrow">Portfolio Lens</p><h2>Risk and diversification</h2></div>
      {data ? <>
        <div className="metric-row">
          <div className="metric"><span>Diversification</span><strong>{data.diversification_score}/100</strong></div>
          <div className="metric"><span>Top sector</span><strong>{Object.entries(data.sector_exposure)[0]?.[0] ?? "N/A"}</strong></div>
        </div>
        <p className="muted">{data.summary}</p>
        <div className="chips">{Object.entries(data.sector_exposure).map(([sector, weight]) => <span key={sector} className="chip">{sector}: {weight}%</span>)}</div>
        <div className="alert-box"><strong>Risk alerts</strong><p>{data.risk_alerts.join(" | ") || "No major alerts detected."}</p></div>
        {data.explain_like_im_5 ? <p className="muted">{data.explain_like_im_5}</p> : null}
      </> : <p className="muted">Connect the backend to load live portfolio analysis.</p>}
    </section>
  );
}
