"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { Message, ToolCallData, ToolResultData, Conversation, Product, CartItem } from "@/lib/types";
import { sendMessage, fetchCart } from "@/lib/api";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { Sidebar } from "@/components/Sidebar";
import { CartDrawer } from "@/components/CartDrawer";
import { ProductDetailDrawer } from "@/components/ProductDetailDrawer";
import {
  ShoppingBag, Menu, ShoppingCart, RotateCcw,
} from "lucide-react";

const CATEGORIES = ["all", "electronics", "jewelery", "men's clothing", "women's clothing"];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);
  const [productDetailOpen, setProductDetailOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [cartItems, setCartItems] = useState<CartItem[]>([]);

  // Fetch cart from backend for current session (single source of truth)
  const refetchCart = useCallback(async () => {
    const res = await fetchCart(sessionId);
    setCartItems(res.items);
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) refetchCart();
    else setCartItems([]);
  }, [sessionId, refetchCart]);

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
        });

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
        // Refresh cart so sidebar/drawer reflect any add/remove/update from this turn
        if (newSessionId) {
          const res = await fetchCart(newSessionId);
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
    [sessionId]
  );

  const handleClear = () => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    setActiveCategory("all");
  };

  const handleCategoryFilter = (category: string) => {
    setActiveCategory(category);
    if (category === "all") return;
    handleSend(`Show me ${category}`);
  };

  const handleAddToCart = (productId: number) => {
    handleSend(`Add product ${productId} to my cart`);
  };

  const handleViewProduct = (product: Product) => {
    setSelectedProduct(product);
    setProductDetailOpen(true);
  };

  const handleAddFromDrawer = (productId: number, quantity: number) => {
    handleSend(`Add ${quantity} of product ${productId} to my cart`);
  };

  const handleUpdateCartQuantity = (productId: number, quantity: number) => {
    if (quantity === 0) {
      handleSend(`Remove product ${productId} from my cart`);
    } else {
      handleSend(`Update product ${productId} quantity to ${quantity} in my cart`);
    }
  };

  const handleRemoveFromCart = (productId: number) => {
    handleSend(`Remove product ${productId} from my cart`);
  };

  const isEmpty = messages.length === 0;

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
          if (sessionId) refetchCart();
          setCartOpen(true);
        }}
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
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-peach-400 via-rose-400 to-peach-500 shadow-md shadow-peach-300/25">
                <ShoppingBag className="h-4 w-4 text-white" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-[15px] font-bold text-gradient tracking-tight">ShopAI</h1>
                <p className="text-[10px] font-semibold text-gray-500 tracking-widest uppercase -mt-0.5">Assistant</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Category filters - desktop */}
            <div className="hidden md:flex items-center gap-1 bg-white/50 rounded-xl p-1 border border-peach-100/30">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => handleCategoryFilter(cat)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold capitalize transition-all duration-200 ${
                    activeCategory === cat
                      ? "bg-gradient-to-r from-peach-400 to-rose-400 text-white shadow-sm shadow-peach-200/40"
                      : "text-gray-500 hover:text-gray-700 hover:bg-peach-50/50"
                  }`}
                >
                  {cat === "all" ? "All" : cat}
                </button>
              ))}
            </div>

            {messages.length > 0 && (
              <button
                onClick={handleClear}
                className="flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold text-gray-500 hover:bg-peach-50/80 hover:text-gray-700 transition-all active:scale-95"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Clear</span>
              </button>
            )}

            {/* Cart button */}
            <button
              onClick={() => {
                if (sessionId) refetchCart();
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

        {/* Category filters - mobile */}
        <div className="md:hidden flex items-center gap-1.5 px-4 py-2 overflow-x-auto glass border-b border-peach-100/20">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => handleCategoryFilter(cat)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-full text-[11px] font-semibold capitalize transition-all duration-200 ${
                activeCategory === cat
                  ? "bg-gradient-to-r from-peach-400 to-rose-400 text-white shadow-sm"
                  : "bg-white/50 text-gray-500 border border-peach-100/30"
              }`}
            >
              {cat === "all" ? "All" : cat}
            </button>
          ))}
        </div>

        {/* Messages / Empty state */}
        <div className="flex-1 overflow-y-auto">
          {isEmpty ? (
            <div className="flex h-full flex-col items-center justify-center px-4">
              {/* Animated hero */}
              <div className="relative mb-6">
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-peach-400/20 to-rose-300/20 blur-2xl animate-glow" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-peach-400 via-rose-400 to-peach-500 shadow-xl shadow-peach-400/25 animate-float">
                  <ShoppingBag className="h-8 w-8 text-white" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 tracking-tight mb-1">
                What are you looking for?
              </h2>
              <p className="text-sm text-gray-500 mb-8 text-center max-w-sm leading-relaxed">
                Search products, compare prices, or manage your cart.
              </p>

              {/* Centered chat input */}
              <div className="w-full max-w-xl">
                <ChatInput onSend={handleSend} disabled={isLoading} />
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-2xl space-y-5 px-4 py-5">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onAddToCart={handleAddToCart}
                  onViewProduct={handleViewProduct}
                />
              ))}
              {error && (
                <div className="flex items-start gap-3 rounded-2xl border border-red-200/40 bg-red-50/80 backdrop-blur-sm px-4 py-3.5 text-[13px] text-red-700 animate-fade-in leading-relaxed">
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
          <div className="glass-strong border-t border-peach-100/30 px-4 py-3.5 sticky bottom-0">
            <div className="mx-auto max-w-2xl">
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
