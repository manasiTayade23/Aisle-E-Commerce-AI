"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Message, ToolCallData, ToolResultData, Conversation, Product, CartItem } from "@/lib/types";
import { sendMessage, fetchCart, addToCartDirect, updateCartQuantityDirect, removeFromCartDirect } from "@/lib/api";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { Sidebar } from "@/components/Sidebar";
import { CartDrawer } from "@/components/CartDrawer";
import { ProductDetailDrawer } from "@/components/ProductDetailDrawer";
import Link from "next/link";
import { signOut } from "next-auth/react";
import {
  Store, Menu, ShoppingCart, RotateCcw,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { data: authSession, status } = useSession();
  const accessToken = (authSession as { accessToken?: string } | null)?.accessToken ?? null;

  // Redirect to login when user lands and is not authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/signin");
    }
  }, [status, router]);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [cartOpen, setCartOpen] = useState(false);
  const [productDetailOpen, setProductDetailOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);

  // Fetch cart from backend (session or authenticated user)
  const refetchCart = useCallback(async () => {
    const res = await fetchCart(sessionId || "", accessToken);
    setCartItems(res.items);
  }, [sessionId, accessToken]);

  useEffect(() => {
    if (sessionId || accessToken) refetchCart();
    else setCartItems([]);
  }, [sessionId, accessToken, refetchCart]);

  const cartItemCount = cartItems.reduce((s, i) => s + i.quantity, 0);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = useCallback(
    async (text: string) => {
      setError(null);
      const now = Date.now();
      const userMsg: Message = {
        id: now.toString(),
        role: "user",
        content: text,
        timestamp: now,
      };

      const assistantId = (now + 1).toString();
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        toolCalls: [],
        toolResults: [],
        isStreaming: true,
        timestamp: now + 1,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsLoading(true);

      // Update conversation history
      setConversations((prev) => {
        const existing = prev.find((c) => c.id === sessionId);
        if (existing) {
          return prev.map((c) =>
            c.id === sessionId
              ? { ...c, lastMessage: text, timestamp: now, messageCount: c.messageCount + 1 }
              : c
          );
        }
        return prev;
      });

      try {
        const newSessionId = await sendMessage(text, sessionId, (data) => {
          if (data.type === "text") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + (data.content as string) }
                  : m
              )
            );
          } else if (data.type === "tool_call") {
            const tc: ToolCallData = {
              name: data.name as string,
              input: data.input as Record<string, unknown>,
            };
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, toolCalls: [...(m.toolCalls || []), tc] }
                  : m
              )
            );
          } else if (data.type === "tool_result") {
            const tr: ToolResultData = {
              name: data.name as string,
              data: data.data as ToolResultData["data"],
            };
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      toolResults: [...(m.toolResults || []), tr],
                      toolCalls: (m.toolCalls || []).filter(
                        (tc) => tc.name !== (data.name as string)
                      ),
                    }
                  : m
              )
            );
          } else if (data.type === "done") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, isStreaming: false, toolCalls: [] } : m
              )
            );
          }
        }, accessToken);

        if (newSessionId && newSessionId !== sessionId) {
          setSessionId(newSessionId);
          setConversations((prev) => {
            if (prev.find((c) => c.id === newSessionId)) return prev;
            return [
              {
                id: newSessionId,
                title: text.slice(0, 40) + (text.length > 40 ? "..." : ""),
                lastMessage: text,
                timestamp: now,
                messageCount: 2,
              },
              ...prev,
            ];
          });
        }
        // Refresh cart so sidebar/drawer reflect any add/remove/update from this turn (same cart as UI)
        if (newSessionId) {
          const res = await fetchCart(newSessionId, accessToken);
          setCartItems(res.items);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, isStreaming: false, content: "" } : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, accessToken]
  );

  const handleClear = () => {
    setMessages([]);
    setSessionId(null);
    setError(null);
  };

  // Ensure we have a session id for cart (create one if user adds to cart before first message)
  const getOrCreateSessionId = useCallback((): string => {
    if (sessionId) return sessionId;
    const newId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `sess-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setSessionId(newId);
    return newId;
  }, [sessionId]);

  const handleAddToCart = useCallback(async (productId: number) => {
    setError(null);
    const sid = getOrCreateSessionId();
    try {
      const res = await addToCartDirect(sid, productId, 1, accessToken);
      setCartItems(res.items);
      setCartOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add to cart");
    }
  }, [getOrCreateSessionId, accessToken]);

  const handleViewProduct = (product: Product) => {
    setSelectedProduct(product);
    setProductDetailOpen(true);
  };

  const handleAddFromDrawer = useCallback(async (productId: number, quantity: number) => {
    setError(null);
    const sid = getOrCreateSessionId();
    try {
      const res = await addToCartDirect(sid, productId, quantity, accessToken);
      setCartItems(res.items);
      setProductDetailOpen(false);
      setCartOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add to cart");
    }
  }, [getOrCreateSessionId, accessToken]);

  const handleUpdateCartQuantity = useCallback(async (productId: number, quantity: number) => {
    const sid = sessionId || getOrCreateSessionId();
    setError(null);
    try {
      if (quantity === 0) {
        const res = await removeFromCartDirect(sid, productId, accessToken);
        setCartItems(res.items);
      } else {
        const res = await updateCartQuantityDirect(sid, productId, quantity, accessToken);
        setCartItems(res.items);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update cart");
    }
  }, [sessionId, getOrCreateSessionId, accessToken]);

  const handleRemoveFromCart = useCallback(async (productId: number) => {
    const sid = sessionId || getOrCreateSessionId();
    setError(null);
    try {
      const res = await removeFromCartDirect(sid, productId, accessToken);
      setCartItems(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove from cart");
    }
  }, [sessionId, getOrCreateSessionId, accessToken]);

  const isEmpty = messages.length === 0;

  // Show nothing (or loader) while checking auth / redirecting
  if (status === "loading" || status === "unauthenticated") {
    return (
      <div className="flex h-dvh items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-slate-800 flex items-center justify-center">
            <Store className="h-5 w-5 text-white" />
          </div>
          <p className="text-sm font-medium text-gray-500">
            {status === "loading" ? "Loading…" : "Redirecting to sign in…"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-dvh overflow-hidden">
      {/* Background blobs */}
      <div className="blob-bg animate-float w-96 h-96 bg-peach-200 -top-20 -left-20" />
      <div className="blob-bg animate-float-delayed w-80 h-80 bg-rose-200 top-1/2 -right-20" />
      <div className="blob-bg animate-float w-72 h-72 bg-amber-100 -bottom-10 left-1/3" />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        activeConversationId={sessionId}
        onNewChat={handleClear}
        onSelectConversation={() => {}}
        cartItemCount={cartItemCount}
        onOpenCart={() => {
          if (sessionId || accessToken) refetchCart();
          setCartOpen(true);
        }}
        userName={authSession?.user?.name ?? authSession?.user?.email ?? null}
      />

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0 relative z-10">
        {/* Header */}
        <header className="flex items-center justify-between glass-strong border-b border-peach-100/30 px-4 lg:px-6 py-3 sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex h-9 w-9 items-center justify-center rounded-xl hover:bg-peach-50/80 transition-colors"
            >
              <Menu className="h-5 w-5 text-gray-600" />
            </button>

            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-white shadow-md">
                <Store className="h-4 w-4" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-[15px] font-extrabold text-gray-900 tracking-tight">Aisle</h1>
                <p className="text-[10px] font-bold text-gray-500 -mt-0.5">Your shopping sidekick</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleClear}
                className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-bold text-gray-600 hover:bg-peach-50/80 hover:text-gray-800 transition-all active:scale-95"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Clear</span>
              </button>
            )}

            {/* Auth: sign in / user */}
            {authSession?.user ? (
              <button
                onClick={() => signOut()}
                className="hidden sm:flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold text-gray-700 hover:bg-peach-50/80"
              >
                {authSession.user.email}
              </button>
            ) : (
              <Link
                href="/signin"
                className="hidden sm:flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold text-peach-600 hover:bg-peach-50/80"
              >
                Sign in
              </Link>
            )}

            {/* Cart button */}
            <button
              onClick={() => {
                if (sessionId || accessToken) refetchCart();
                setCartOpen(true);
              }}
              className="relative flex h-9 w-9 items-center justify-center rounded-xl hover:bg-peach-50/80 transition-colors"
            >
              <ShoppingCart className="h-5 w-5 text-gray-600" />
              {cartItemCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-peach-500 to-rose-500 text-[9px] font-bold text-white shadow-sm animate-bounce-gentle">
                  {cartItemCount}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* Messages / Empty state */}
        <div className="flex-1 overflow-y-auto">
          {isEmpty ? (
            <div className="flex h-full flex-col items-center justify-center px-4">
              {/* Animated hero */}
              <div className="relative mb-6">
                <div className="absolute inset-0 rounded-3xl bg-slate-200/30 blur-2xl animate-glow" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800 text-white shadow-xl animate-float">
                  <Store className="h-8 w-8" />
                </div>
              </div>
              <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight mb-1">
                What are you looking for?
              </h2>
              <p className="text-sm font-medium text-gray-600 mb-6 text-center max-w-sm leading-relaxed">
                Search products, compare prices, or manage your cart.
              </p>

              {/* Suggested prompts / quick actions */}
              <div className="flex flex-wrap justify-center gap-2 mb-6">
                {[
                  "Show electronics",
                  "Show me TVs",
                  "Women's clothing under $50",
                  "View my cart",
                  "Compare the first two",
                ].map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => handleSend(prompt)}
                    disabled={isLoading}
                    className="rounded-xl px-4 py-2.5 text-[13px] font-semibold text-gray-700 bg-white/90 border-2 border-peach-200/50 hover:border-peach-300 hover:bg-peach-50/50 hover:text-gray-900 transition-all shadow-sm hover:shadow-md active:scale-[0.98]"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {/* Centered chat input */}
              <div className="w-full max-w-xl">
                <ChatInput onSend={handleSend} disabled={isLoading} />
              </div>
            </div>
          ) : (
            <div className="mx-auto w-full max-w-4xl xl:max-w-5xl space-y-6 px-4 sm:px-6 lg:px-8 py-6">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onAddToCart={handleAddToCart}
                  onViewProduct={handleViewProduct}
                />
              ))}
              {error && (
                <div className="flex items-start gap-3 rounded-2xl border border-red-200/40 bg-red-50/80 backdrop-blur-sm px-4 py-3.5 text-[13px] font-semibold text-red-700 animate-fade-in leading-relaxed">
                  <span className="flex-shrink-0 mt-0.5 font-bold text-red-400">!</span>
                  <span>{error}</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Bottom input - only when conversation is active */}
        {!isEmpty && (
          <div className="glass-strong border-t border-peach-100/30 px-4 sm:px-6 lg:px-8 py-3.5 sticky bottom-0">
            <div className="mx-auto w-full max-w-4xl xl:max-w-5xl space-y-3">
              {/* Quick action buttons when chat is active */}
              <div className="flex flex-wrap gap-2 justify-center">
                {["Show electronics", "Show me TVs", "View my cart"].map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => handleSend(prompt)}
                    disabled={isLoading}
                    className="rounded-lg px-3 py-1.5 text-[12px] font-semibold text-gray-600 bg-white/80 border border-peach-200/40 hover:bg-peach-50/80 hover:border-peach-300/60 transition-all"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
              <ChatInput onSend={handleSend} disabled={isLoading} />
            </div>
          </div>
        )}
      </div>

      {/* Drawers */}
      <CartDrawer
        isOpen={cartOpen}
        onClose={() => setCartOpen(false)}
        items={cartItems}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveFromCart}
      />

      <ProductDetailDrawer
        product={selectedProduct}
        isOpen={productDetailOpen}
        onClose={() => setProductDetailOpen(false)}
        onAddToCart={handleAddFromDrawer}
      />
    </div>
  );
}
