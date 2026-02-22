"use client";

import { CartItem } from "@/lib/types";

export function CartItemCard({ item }: { item: CartItem }) {
  return (
    <div className="flex items-center gap-3.5 rounded-2xl bg-white/70 border border-peach-100/40 p-3.5 animate-fade-in backdrop-blur-sm shadow-sm">
      <div className="h-14 w-14 flex-shrink-0 overflow-hidden rounded-xl bg-white p-1.5">
        <img
          src={item.image}
          alt={item.title}
          className="h-full w-full object-contain"
        />
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="text-[13px] font-semibold text-gray-900 line-clamp-1 tracking-tight">
          {item.title}
        </h4>
        <div className="flex items-center gap-3 mt-1.5">
          <span className="text-[13px] font-bold text-gradient">
            ${item.price.toFixed(2)}
          </span>
          <span className="text-[11px] font-semibold text-peach-700 bg-peach-50 px-2 py-0.5 rounded-full">
            x{item.quantity}
          </span>
          <span className="text-[14px] font-bold text-gray-900 ml-auto tracking-tight">
            ${item.item_total.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}
