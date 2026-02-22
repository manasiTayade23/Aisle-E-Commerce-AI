"use client";

import { Product } from "@/lib/types";
import { Star, ShoppingCart, Eye } from "lucide-react";

interface ProductCardProps {
  product: Product;
  onAddToCart?: (productId: number) => void;
  onViewDetails?: (product: Product) => void;
}

export function ProductCard({ product, onAddToCart, onViewDetails }: ProductCardProps) {
  return (
    <div className="group relative flex gap-4 rounded-2xl bg-white/70 border border-peach-100/40 p-3.5 transition-all duration-300 hover:shadow-xl hover:shadow-peach-200/20 hover:border-peach-200/60 hover:-translate-y-0.5 animate-fade-in backdrop-blur-sm">
      {/* Image */}
      <div
        className="relative h-[76px] w-[76px] flex-shrink-0 overflow-hidden rounded-xl bg-white p-2 cursor-pointer"
        onClick={() => onViewDetails?.(product)}
      >
        <img
          src={product.image}
          alt={product.title}
          className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-110"
        />
        {/* View overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 rounded-xl transition-all duration-300 flex items-center justify-center">
          <Eye className="h-4 w-4 text-white opacity-0 group-hover:opacity-60 transition-opacity duration-300" />
        </div>
      </div>

      {/* Details */}
      <div className="flex flex-1 flex-col justify-between min-w-0 py-0.5">
        <div>
          <h4
            className="text-[13px] font-semibold text-gray-900 line-clamp-2 leading-snug tracking-tight cursor-pointer hover:text-peach-600 transition-colors"
            onClick={() => onViewDetails?.(product)}
          >
            {product.title}
          </h4>
          <p className="mt-1 text-[10px] font-bold text-peach-600/70 capitalize tracking-widest uppercase">
            {product.category}
          </p>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-[15px] font-bold text-gradient tracking-tight">
            ${product.price.toFixed(2)}
          </span>
          <div className="flex items-center gap-2">
            {product.rating && (
              <div className="flex items-center gap-1">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                <span className="text-[11px] font-semibold text-gray-600">
                  {product.rating.rate}
                </span>
              </div>
            )}
            {onAddToCart && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToCart(product.id);
                }}
                className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-peach-400 to-rose-400 text-white shadow-sm shadow-peach-200/50 hover:shadow-md hover:shadow-peach-300/40 transition-all active:scale-90"
              >
                <ShoppingCart className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
