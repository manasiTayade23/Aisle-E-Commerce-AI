const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CartResponse {
  items: Array<{
    product_id: number;
    title: string;
    price: number;
    quantity: number;
    item_total: number;
    image: string;
  }>;
  total: number;
}

export async function fetchCart(sessionId: string | null): Promise<CartResponse> {
  if (!sessionId) return { items: [], total: 0 };
  const url = `${API_URL}/api/cart?session_id=${encodeURIComponent(sessionId)}`;
  const resp = await fetch(url);
  if (!resp.ok) return { items: [], total: 0 };
  const data = await resp.json();
  return { items: data.items ?? [], total: Number(data.total) ?? 0 };
}

export async function sendMessage(
  message: string,
  sessionId: string | null,
  onChunk: (data: Record<string, unknown>) => void
): Promise<string> {
  const resp = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!resp.ok) {
    let errorMsg = `Server error (${resp.status})`;
    try {
      const body = await resp.json();
      if (body.error) errorMsg = body.error;
    } catch {
      // use default
    }
    throw new Error(errorMsg);
  }

  const reader = resp.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let returnedSessionId = sessionId || "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const data = JSON.parse(line);
        if (data.type === "session") {
          returnedSessionId = data.session_id;
        } else if (data.type === "error") {
          throw new Error(data.content || "An error occurred");
        }
        onChunk(data);
      } catch (e) {
        if (e instanceof Error && e.message !== line) throw e;
      }
    }
  }

  if (buffer.trim()) {
    try {
      const data = JSON.parse(buffer);
      if (data.type === "session") {
        returnedSessionId = data.session_id;
      } else if (data.type === "error") {
        throw new Error(data.content || "An error occurred");
      }
      onChunk(data);
    } catch (e) {
      if (e instanceof Error && e.message !== buffer.trim()) throw e;
    }
  }

  return returnedSessionId;
}
