"use client";

import { Product } from "@/lib/types";
import { Star, ShoppingCart, Eye } from "lucide-react";

interface ProductRowProps {
  product: Product;
  onAddToCart?: (productId: number) => void;
  onViewDetails?: (product: Product) => void;
}

export function ProductRow({ product, onAddToCart, onViewDetails }: ProductRowProps) {
  return (
    <div className="group flex rounded-2xl bg-white border border-peach-100/50 overflow-hidden transition-all duration-200 hover:shadow-lg hover:shadow-peach-200/20 hover:border-peach-200/60 animate-fade-in">
      <div
        className="relative flex-shrink-0 w-28 h-28 sm:w-36 sm:h-36 bg-white border-r border-peach-100/50 flex items-center justify-center cursor-pointer"
        onClick={() => onViewDetails?.(product)}
      >
        <img
          src={product.image}
          alt={product.title}
          className="w-full h-full object-contain p-3 transition-transform duration-200 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 flex items-center justify-center transition-colors">
          <Eye className="h-5 w-5 text-peach-500 opacity-0 group-hover:opacity-80 transition-opacity" />
        </div>
      </div>
      <div className="flex flex-1 flex-col min-w-0 p-4">
        <h4
          className="text-[14px] font-semibold text-gray-900 leading-snug tracking-tight cursor-pointer hover:text-peach-600 transition-colors line-clamp-2"
          onClick={() => onViewDetails?.(product)}
        >
          {product.title}
        </h4>
        <p className="mt-1 text-[10px] font-bold text-peach-600/80 capitalize tracking-widest uppercase">
          {product.category}
        </p>
        <div className="mt-auto pt-3 flex items-center justify-between gap-3 flex-wrap">
          <span className="text-[16px] font-bold text-gradient tracking-tight">
            ${product.price.toFixed(2)}
          </span>
          <div className="flex items-center gap-3">
            {product.rating && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails?.(product);
                }}
                title={`${product.rating.rate} out of 5 (${product.rating.count} reviews)`}
                className="flex items-center gap-1 rounded-lg px-1.5 py-0.5 hover:bg-amber-50 transition-colors cursor-pointer"
              >
                <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                <span className="text-[12px] font-semibold text-gray-600">
                  {product.rating.rate}
                </span>
                <span className="text-[11px] text-gray-400">({product.rating.count})</span>
              </button>
            )}
            {onAddToCart && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToCart(product.id);
                }}
                className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-peach-400 to-rose-400 px-3 py-2 text-white text-[12px] font-semibold shadow-sm shadow-peach-200/50 hover:shadow-md transition-all active:scale-[0.98]"
              >
                <ShoppingCart className="h-3.5 w-3.5" />
                Add to cart
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
