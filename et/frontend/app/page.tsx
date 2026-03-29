import { ChatPanel } from "@/components/ChatPanel";
import { PortfolioPanel } from "@/components/PortfolioPanel";
import { VideoPanel } from "@/components/VideoPanel";

export default function HomePage() {
  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">MarketMind AI</p>
          <h1>Portfolio-aware Market GPT for Indian investors, plus an AI video engine.</h1>
          <p className="muted">Built for recruiter demos, hackathons, and real-world wealth workflows with multi-agent reasoning, portfolio diagnostics, and automated market storytelling.</p>
        </div>
        <div className="hero-card">
          <span>What&apos;s included</span>
          <ul>
            <li>Fundamental, technical, news, and FII/DII agents</li>
            <li>Portfolio concentration and sector exposure analysis</li>
            <li>Daily market video generation with charts and subtitles</li>
          </ul>
        </div>
      </section>
      <section className="dashboard">
        <ChatPanel />
        <div className="sidebar">
          <PortfolioPanel />
          <VideoPanel />
        </div>
      </section>
    </main>
  );
}
