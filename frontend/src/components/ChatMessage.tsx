"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message, Product } from "@/lib/types";
import { ProductCard } from "./ProductCard";
import { CartItemCard } from "./CartItemCard";
import { ProductComparison } from "./ProductComparison";
import { ToolIndicator } from "./ToolIndicator";
import { TypingIndicator } from "./TypingIndicator";
import { cn } from "@/lib/cn";
import { User, Sparkles } from "lucide-react";

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

  // Detect if we should show comparison view (2 products from search with comparison context)
  const searchResult = message.toolResults?.find((tr) => tr.name === "search_products");
  const hasExactlyTwoProducts = searchResult?.data.products?.length === 2;

  return (
    <div className={cn("flex gap-3 animate-slide-up", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-2xl shadow-sm",
          isUser
            ? "bg-gradient-to-br from-gray-700 to-gray-900 text-white shadow-gray-300/30"
            : "bg-gradient-to-br from-peach-400 via-rose-400 to-peach-500 text-white shadow-peach-300/30"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={cn("flex flex-col gap-2.5 max-w-[82%] min-w-0", isUser ? "items-end" : "items-start")}>
        {/* Role label + timestamp */}
        <div className={cn("flex items-center gap-2", isUser ? "flex-row-reverse" : "flex-row")}>
          <span className={cn(
            "text-[11px] font-semibold uppercase tracking-wider",
            isUser ? "text-gray-500" : "text-peach-600"
          )}>
            {isUser ? "You" : "ShopAI"}
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

        {/* Product results */}
        {message.toolResults?.map((tr, i) => {
          if (tr.name === "search_products" && tr.data.products && tr.data.products.length > 0) {
            // Show comparison if exactly 2 products
            if (hasExactlyTwoProducts && tr.data.products.length === 2) {
              return (
                <ProductComparison
                  key={`tr-${i}`}
                  products={tr.data.products}
                  onAddToCart={onAddToCart}
                />
              );
            }
            return (
              <div key={`tr-${i}`} className="grid grid-cols-1 gap-2.5 w-full">
                {tr.data.products.slice(0, 6).map((p) => (
                  <ProductCard
                    key={p.id}
                    product={p}
                    onAddToCart={onAddToCart}
                    onViewDetails={onViewProduct}
                  />
                ))}
                {tr.data.count && tr.data.count > 6 && (
                  <p className="text-[11px] text-peach-600 text-center py-1 font-semibold">
                    +{tr.data.count - 6} more results
                  </p>
                )}
              </div>
            );
          }

          if (tr.name === "get_product_details" && tr.data.title) {
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
              <div key={`tr-${i}`} className="w-full">
                <ProductCard
                  product={product}
                  onAddToCart={onAddToCart}
                  onViewDetails={onViewProduct}
                />
                {typeof tr.data.description === "string" && (
                  <p className="mt-2 text-[13px] text-gray-600 line-clamp-3 px-1 leading-relaxed">
                    {tr.data.description}
                  </p>
                )}
              </div>
            );
          }

          if (tr.name === "get_cart" && tr.data.items) {
            if (tr.data.items.length === 0) return null;
            return (
              <div key={`tr-${i}`} className="flex flex-col gap-2.5 w-full">
                {tr.data.items.map((item) => (
                  <CartItemCard key={item.product_id} item={item} />
                ))}
                <div className="flex justify-between items-center px-4 py-3 rounded-2xl bg-gradient-to-r from-peach-50/80 to-rose-50/80 border border-peach-100/40">
                  <span className="text-sm font-semibold text-peach-600">Total</span>
                  <span className="text-lg font-bold text-gradient">
                    ${tr.data.total?.toFixed(2)}
                  </span>
                </div>
              </div>
            );
          }

          return null;
        })}

        {/* Text content */}
        {message.content && (
          <div
            className={cn(
              "rounded-2xl px-4 py-3 leading-relaxed",
              isUser
                ? "bg-gradient-to-br from-gray-800 to-gray-900 text-white text-[15px] rounded-tr-md shadow-lg shadow-gray-300/20"
                : "bg-white/80 backdrop-blur-sm border border-peach-100/40 text-gray-800 rounded-tl-md shadow-sm shadow-peach-100/20"
            )}
          >
            {isUser ? (
              <p className="leading-relaxed">{message.content}</p>
            ) : (
              <div className="prose-chat markdown-response overflow-x-auto max-w-full">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            )}
          </div>
        )}

        {/* Streaming indicator */}
        {message.isStreaming && !message.content && !message.toolCalls?.length && (
          <div className="inline-flex items-center gap-2.5 rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-200/60 px-4 py-2.5 shadow-sm rounded-tl-md">
            <span className="text-base animate-bounce-gentle">🤔</span>
            <span className="text-[13px] font-medium text-gray-600">Thinking...</span>
            <TypingIndicator />
          </div>
        )}
      </div>
    </div>
  );
}
