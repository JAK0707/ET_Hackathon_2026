"use client";

import { useState } from "react";
import { postJson } from "@/lib/api";

type VideoResponse = { script: string; video_path: string; chart_paths: string[] };

export function VideoPanel() {
  const [data, setData] = useState<VideoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  async function handleGenerate() {
    setLoading(true);
    try { setData(await postJson<VideoResponse>("/generate-video", { duration_seconds: 60, include_subtitles: true })); }
    catch { setData(null); }
    finally { setLoading(false); }
  }
  return (
    <section className="panel">
      <div className="section-header"><p className="eyebrow">Video Engine</p><h2>Auto-generated market reel</h2></div>
      <p className="muted">Generate a 30 to 90 second market update with charts, voiceover, and subtitles.</p>
      <button type="button" onClick={handleGenerate} className="primary-button" disabled={loading}>{loading ? "Generating..." : "Generate daily market video"}</button>
      {data ? <div className="video-result"><strong>Script preview</strong><p>{data.script}</p><p className="muted">Saved to: {data.video_path}</p></div> : null}
    </section>
  );
}
