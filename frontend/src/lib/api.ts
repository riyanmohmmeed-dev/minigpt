const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const DEFAULT_MODEL = process.env.NEXT_PUBLIC_MODEL || "default";

export type Message = { role: "user" | "assistant"; content: string };

export async function createSession(): Promise<{ session_id: string }> {
  try {
    const res = await fetch(`${API_BASE}/v1/sessions`, { method: "POST" });
    if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
    return res.json();
  } catch (e) {
    if (e instanceof TypeError && (e.message === "Failed to fetch" || e.message === "network error")) {
      throw new Error("Cannot reach backend. Is it running on " + API_BASE + "?");
    }
    throw e;
  }
}

export async function streamChat(
  messages: Message[],
  sessionId: string | null,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: Error) => void
): Promise<void> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (sessionId) headers["X-Session-Id"] = sessionId;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/v1/chat/completions`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: DEFAULT_MODEL,
        messages,
        stream: true,
      }),
    });
  } catch (e) {
    const msg = e instanceof TypeError && (e.message === "Failed to fetch" || e.message === "network error")
      ? "Cannot reach backend. Is it running on " + API_BASE + "?"
      : e instanceof Error ? e.message : "Network error";
    onError(new Error(msg));
    return;
  }

  if (!res.ok) {
    let msg = `API ${res.status}`;
    try {
      const err = await res.json();
      msg = err?.error?.message || msg;
    } catch {
      msg = await res.text() || msg;
    }
    onError(new Error(msg));
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    onError(new Error("No response body"));
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (data === "[DONE]") continue;
          try {
            const json = JSON.parse(data);
            const content = json?.choices?.[0]?.delta?.content;
            if (typeof content === "string") onChunk(content);
          } catch {
            // skip invalid JSON
          }
        }
      }
    }
  } finally {
    onDone();
  }
}
