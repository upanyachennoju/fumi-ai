const API_URL = "http://127.0.0.1:8000";

export async function sendMessage(message: string): Promise<string> {
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

  const data = await response.json();

  return data.response;
}