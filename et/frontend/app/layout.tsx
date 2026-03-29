import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MarketMind AI",
  description: "Portfolio-aware market copilot and AI video engine for Indian investors"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
