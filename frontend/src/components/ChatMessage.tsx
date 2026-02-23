"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message, Product } from "@/lib/types";
import { ProductRow } from "./ProductRow";
import { CartItemCard } from "./CartItemCard";
import { ProductComparison } from "./ProductComparison";
import { ToolIndicator } from "./ToolIndicator";
import { ThinkingStatus } from "./ThinkingStatus";
import { cn } from "@/lib/cn";
import { User, Store } from "lucide-react";

interface ChatMessageProps {
  message: Message;
  onAddToCart?: (productId: number) => void;
  onViewProduct?: (product: Product) => void;
}

function formatTime(ts?: number) {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ChatMessage({ message, onAddToCart, onViewProduct }: ChatMessageProps) {
  const isUser = message.role === "user";

  const searchResult = message.toolResults?.find((tr) => tr.name === "search_products");
  const detailResults = message.toolResults?.filter((tr) => tr.name === "get_product_details" && tr.data?.title) ?? [];
  // Only show comparison when user asked (comparison agent ran: 2 or 3 get_product_details, no search_products)
  const showComparison =
    !searchResult &&
    (detailResults.length === 2 || detailResults.length === 3);

  return (
    <div className={cn("flex gap-3 sm:gap-4 animate-slide-up", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-9 w-9 sm:h-10 sm:w-10 flex-shrink-0 items-center justify-center rounded-2xl shadow-sm",
          isUser
            ? "bg-gradient-to-br from-slate-600 to-slate-800 text-white shadow-slate-400/25"
            : "bg-slate-800 text-white shadow-slate-400/25"
        )}
      >
        {isUser ? <User className="h-4 w-4 sm:h-5 sm:w-5" /> : <Store className="h-4 w-4 sm:h-5 sm:w-5" />}
      </div>

      {/* Content - full width on desktop, clear user vs assistant styling */}
      <div className={cn("flex flex-col gap-2.5 min-w-0 flex-1", isUser ? "items-end max-w-[85%] sm:max-w-[75%]" : "items-start w-full max-w-full")}>
        {/* Role label + timestamp */}
        <div className={cn("flex items-center gap-2", isUser ? "flex-row-reverse" : "flex-row")}>
          <span className={cn(
            "text-[11px] font-semibold uppercase tracking-wider",
            isUser ? "text-slate-500" : "text-peach-600"
          )}>
            {isUser ? "You" : "Aisle"}
          </span>
          {message.timestamp && (
            <span className="text-[10px] text-gray-400 font-medium">
              {formatTime(message.timestamp)}
            </span>
          )}
        </div>

        {/* Tool calls */}
        {message.toolCalls?.map((tc, i) => (
          <ToolIndicator key={`tc-${i}`} name={tc.name} />
        ))}

        {/* User: bubble. Assistant: streamed title (properly rendered), then product list only — no description */}
        {message.content && (
          <>
            {isUser ? (
              <div className="rounded-2xl px-4 py-3.5 leading-relaxed bg-slate-700 text-white text-[15px] rounded-tr-sm rounded-bl-2xl rounded-tl-2xl shadow-md shadow-slate-400/20 max-w-full">
                <p className="leading-relaxed">{message.content}</p>
              </div>
            ) : (
              <div className={cn(
                "prose-chat markdown-response text-[15px] text-gray-800 leading-relaxed max-w-full",
                message.isStreaming && "streaming-text"
              )}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                {message.isStreaming && (
                  <span className="streaming-cursor ml-0.5 inline-block" aria-hidden />
                )}
              </div>
            )}
          </>
        )}

        {/* Show product list / comparison only after streaming finishes — first streaming, then list */}
        {!message.isStreaming && message.toolResults?.map((tr, i) => {
          if (tr.name === "search_products" && tr.data.products && tr.data.products.length > 0) {
            const singleId = tr.data.products.length === 1 ? tr.data.products[0].id : null;
            const hasDetailForSingle = singleId != null && message.toolResults?.some(
              (r) => r.name === "get_product_details" && r.data?.id === singleId
            );
            if (hasDetailForSingle) return null;
            return (
              <div key={`tr-${i}`} className="flex flex-col gap-3 w-full animate-product-pop">
                {tr.data.products.slice(0, 6).map((p) => (
                  <ProductRow
                    key={p.id}
                    product={p}
                    onAddToCart={onAddToCart}
                    onViewDetails={onViewProduct}
                  />
                ))}
                {tr.data.count && tr.data.count > 6 && (
                  <p className="text-[12px] text-peach-600 text-center py-2 font-semibold">
                    +{tr.data.count - 6} more results
                  </p>
                )}
              </div>
            );
          }

          if (tr.name === "get_product_details" && tr.data.title) {
            if (showComparison) return null;
            const product: Product = {
              id: tr.data.id as number,
              title: tr.data.title as string,
              price: tr.data.price as number,
              category: tr.data.category as string,
              image: tr.data.image as string,
              description: tr.data.description as string,
              rating: tr.data.rating as { rate: number; count: number },
            };
            return (
              <div key={`tr-${i}`} className="w-full animate-product-pop">
                <ProductRow
                  product={product}
                  onAddToCart={onAddToCart}
                  onViewDetails={onViewProduct}
                />
              </div>
            );
          }

          // Cart display: get_cart returns { items, total }; add/remove/update/clear_cart return { success, cart: { items, total } }
          const cartPayload =
            tr.name === "get_cart"
              ? tr.data
              : (tr.name === "add_to_cart" || tr.name === "remove_from_cart" || tr.name === "update_cart_quantity" || tr.name === "clear_cart") && tr.data?.cart
              ? tr.data.cart
              : null;
          if (cartPayload?.items) {
            if (cartPayload.items.length === 0) return null;
            return (
              <div key={`tr-${i}`} className="flex flex-col gap-2.5 w-full">
                {cartPayload.items.map((item: { product_id: number; title: string; price: number; quantity: number; item_total: number; image?: string }) => (
                  <CartItemCard key={item.product_id} item={item} />
                ))}
                <div className="flex justify-between items-center px-4 py-3 rounded-2xl bg-gradient-to-r from-peach-50/80 to-rose-50/80 border border-peach-100/40">
                  <span className="text-sm font-semibold text-peach-600">Total</span>
                  <span className="text-lg font-bold text-gradient">
                    ${(cartPayload.total ?? 0).toFixed(2)}
                  </span>
                </div>
              </div>
            );
          }

          return null;
        })}

        {/* Comparison table only when user asked, and only after streaming finishes */}
        {!message.isStreaming && showComparison && detailResults.length >= 2 && (
          <div className="flex flex-col gap-3 w-full animate-product-pop">
            <ProductComparison
              products={detailResults.slice(0, 3).map((tr) => ({
                id: tr.data.id as number,
                title: tr.data.title as string,
                price: tr.data.price as number,
                category: tr.data.category as string,
                image: tr.data.image as string,
                description: tr.data.description as string,
                rating: tr.data.rating as { rate: number; count: number },
              }))}
              onAddToCart={onAddToCart}
              onViewDetails={onViewProduct}
            />
          </div>
        )}

        {/* Streaming / thinking indicator: rotating status when no content yet */}
        {message.isStreaming && !message.content && !message.toolCalls?.length && (
          <ThinkingStatus />
        )}
      </div>
    </div>
  );
}
