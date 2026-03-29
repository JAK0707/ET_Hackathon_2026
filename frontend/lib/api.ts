const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Holding = {
  symbol: string;
  quantity: number;
  average_price: number;
  sector?: string;
};

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!response.ok) throw new Error(`Request failed with ${response.status}`);
  return response.json();
}
