"use client";

import { Search, ShoppingCart, Package, Trash2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/cn";

const TOOL_META: Record<string, { emoji: string; label: string; color: string }> = {
  search_products: { emoji: "🔍", label: "Browsing the catalog...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
  get_product_details: { emoji: "📦", label: "Fetching product info...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
  add_to_cart: { emoji: "🛒", label: "Adding to your cart...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
  get_cart: { emoji: "🧾", label: "Checking your cart...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
  remove_from_cart: { emoji: "🗑️", label: "Removing from cart...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
  update_cart_quantity: { emoji: "✏️", label: "Updating quantity...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
  clear_cart: { emoji: "🗑️", label: "Clearing cart...", color: "text-gray-700 bg-white/80 border-gray-200/60" },
};

export function ToolIndicator({ name }: { name: string }) {
  const meta = TOOL_META[name] || { emoji: "⚙️", label: "Working on it...", color: "text-gray-700 bg-white/80 border-gray-200/60" };

  return (
    <div className={cn(
      "inline-flex items-center gap-2.5 rounded-2xl px-4 py-2.5 text-[13px] font-medium border backdrop-blur-sm animate-fade-in shadow-sm",
      meta.color
    )}>
      <span className="text-base animate-bounce-gentle">{meta.emoji}</span>
      <span>{meta.label}</span>
      <span className="flex items-center gap-1 ml-1">
        <span className="h-1.5 w-1.5 rounded-full bg-peach-400 animate-pulse-dot" style={{ animationDelay: "0ms" }} />
        <span className="h-1.5 w-1.5 rounded-full bg-peach-300 animate-pulse-dot" style={{ animationDelay: "200ms" }} />
        <span className="h-1.5 w-1.5 rounded-full bg-peach-200 animate-pulse-dot" style={{ animationDelay: "400ms" }} />
      </span>
    </div>
  );
}
