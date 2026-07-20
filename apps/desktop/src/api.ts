import type { ResponseMetrics } from "./types";

const API_URL = "http://127.0.0.1:8000";

type ChatApiResponse = {
  response: string;
  metrics?: ResponseMetrics;
};

export async function sendMessage(
  message: string
): Promise<{ reply: string; metrics?: ResponseMetrics }> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to contact backend.");
  }

  const data: ChatApiResponse = await response.json();

  return { reply: data.response, metrics: data.metrics };
}