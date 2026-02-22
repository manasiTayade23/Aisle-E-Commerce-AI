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

function authHeaders(accessToken: string | null | undefined): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (accessToken) h["Authorization"] = `Bearer ${accessToken}`;
  return h;
}

export async function fetchCart(
  sessionId: string | null,
  accessToken?: string | null
): Promise<CartResponse> {
  if (!sessionId && !accessToken) return { items: [], total: 0 };
  const url = `${API_URL}/api/cart?session_id=${encodeURIComponent(sessionId || "")}`;
  const resp = await fetch(url, { headers: authHeaders(accessToken) });
  if (!resp.ok) return { items: [], total: 0 };
  const data = await resp.json();
  return { items: data.items ?? [], total: Number(data.total) ?? 0 };
}

/** Add item to cart directly (no LLM). Returns updated cart. Uses sessionId or auth token. */
export async function addToCartDirect(
  sessionId: string,
  productId: number,
  quantity: number = 1,
  accessToken?: string | null
): Promise<CartResponse> {
  const resp = await fetch(`${API_URL}/api/cart/add`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ session_id: sessionId, product_id: productId, quantity }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || "Failed to add to cart");
  }
  const data = await resp.json();
  return { items: data.items ?? [], total: Number(data.total) ?? 0 };
}

/** Update cart item quantity directly (no LLM). */
export async function updateCartQuantityDirect(
  sessionId: string,
  productId: number,
  quantity: number,
  accessToken?: string | null
): Promise<CartResponse> {
  const resp = await fetch(`${API_URL}/api/cart/update`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ session_id: sessionId, product_id: productId, quantity }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || "Failed to update cart");
  }
  const data = await resp.json();
  return { items: data.items ?? [], total: Number(data.total) ?? 0 };
}

/** Remove item from cart directly (no LLM). */
export async function removeFromCartDirect(
  sessionId: string,
  productId: number,
  accessToken?: string | null
): Promise<CartResponse> {
  const resp = await fetch(`${API_URL}/api/cart/remove`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: JSON.stringify({ session_id: sessionId, product_id: productId }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error((err as { error?: string }).error || "Failed to remove from cart");
  }
  const data = await resp.json();
  return { items: data.items ?? [], total: Number(data.total) ?? 0 };
}

export async function sendMessage(
  message: string,
  sessionId: string | null,
  onChunk: (data: Record<string, unknown>) => void,
  accessToken?: string | null
): Promise<string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
  const resp = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers,
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
